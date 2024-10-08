from datasets import load_dataset, load_from_disk, Dataset
import datetime  # type: ignore
import jsonlines
from data_processing.pattern_filtering.pattern import (
    clean_text as clean_mc4_text,
)
from data_processing.pattern_filtering.pattern import (
    clean_text as clean_oscar_text,
)

from data_processing.perplexity_filtering.perplexity import (
    classify_spam,
    sample_text_back,
)
from data_processing.core.processing_config import load_config
from data_processing.core.metadata import (
    create_info_file,
    create_metadata_file,
)
import numpy as np
import scipy
import json
import os
import zstandard as zstd
import argparse  # type: ignore

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config_filename",
    help="Filename of yaml file to use in hydra (Default: 'config/internet_config.yaml')",  # noqa: E501
    default="config/internet_config.yaml",
)
args = parser.parse_args()
config_filename = str(args.config_filename)

config_dict = load_config(config_filename)

input_based_path = config_dict["input_based_path"]
num_proc = config_dict["processing_parameters"]["num_proc"]
do_perplexity = config_dict["processing_parameters"]["do_perplexity"]
batch_size = config_dict["processing_parameters"]["batch_size"]
sampled_back_ratio = config_dict["processing_parameters"]["sampled_back_ratio"]
output_dir = config_dict["output_dir"]
scratch_location = config_dict["scratch_location"]
version = config_dict["version"]
source = config_dict["source"]
input_version = config_dict["input_version"]
note = config_dict["note"]


def clean_text(text):
    text = text.strip()
    text = clean_mc4_text(text)

    if text == "":
        return -1, 0, ""

    text = clean_oscar_text(text)

    if text == "":
        return -1, 0, ""

    if not do_perplexity:
        return 0, 0, text

    prediction, log_pp_score = classify_spam(text)

    return prediction[0], log_pp_score, text


def process_chunk_data(chunk):
    n = len(chunk["text"])
    predictions = [-1] * n
    log_pp_scores = [0] * n
    updated_dates = ["None"] * n

    for i, text in enumerate(chunk["text"]):
        prediction, log_pp_score, new_text = clean_text(text)

        predictions[i] = prediction
        log_pp_scores[i] = log_pp_score

        if new_text != text:
            chunk["text"][i] = new_text
            updated_dates[i] = str(
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            )

    chunk["prediction"] = predictions
    chunk["log_pp_score"] = log_pp_scores
    chunk["updated_date"] = updated_dates

    # filter blank
    blank_idx = set([i for i, t in enumerate(chunk["text"]) if t == ""])  # noqa: C403

    for field in chunk:
        chunk[field] = [val for i, val in enumerate(chunk[field]) if i not in blank_idx]

    non_spam_idx = [i for i, p in enumerate(chunk["prediction"]) if p == 0]

    sampled_back_idx = []

    if do_perplexity:
        spam_idx = [i for i, p in enumerate(chunk["prediction"]) if p == 1]
        spam_idx_set = set(spam_idx)

        spam_log_pps = [
            log_pp
            for i, log_pp in enumerate(chunk["log_pp_score"])
            if i in spam_idx_set
        ]
        log_pp_array = np.array(spam_log_pps)

        # sampled some data point classified as spam back
        probs = scipy.stats.norm.pdf(
            log_pp_array,
            loc=np.mean(log_pp_array),
            scale=np.std(log_pp_array),
        )

        sampled_back_idx = sample_text_back(
            probs,
            percentage=float(sampled_back_ratio),
        )

        sampled_back_idx_set = set(sampled_back_idx)
        sampled_back_idx = [
            spam_idx[i] for i in range(len(spam_idx)) if i in sampled_back_idx_set
        ]  # Map Idx Back to the original index

    selected_idx = set(non_spam_idx + sampled_back_idx)
    for field in chunk:
        chunk[field] = [val for i, val in enumerate(chunk[field]) if i in selected_idx]
    return chunk


def filter_field(data, source):
    data["source"] = source
    del data["log_pp_score"], data["prediction"]
    if source != "oscar_cl":
        data["source"] = source
        meta_dict = {"filename": f"{input_based_path}/{input_version}"}

        if source == "mc4":
            data["created_date"] = str(data["timestamp"])
            meta_dict["url"] = data["url"]
            del data["timestamp"], data["url"]

        elif source == "cc100":
            data["created_date"] = "2020-10-23T23:31:11.000Z"

        elif "oscar" in source:
            data["created_date"] = "2023-06-08T14:30:28.000Z"
            data["source_id"] = data["id"]
            del data["id"]

    data["meta"] = str(meta_dict)
    if data["updated_date"] == "None":
        data["updated_date"] = data["created_date"]
    return data


def read_jsonl_zst_files(dir_path):
    for root, _, files in os.walk(dir_path):
        for filename in files:
            if filename.endswith(".jsonl.zst"):
                file_path = os.path.join(root, filename)
                folder_name = root.split("/")[-2]
                try:
                    with zstd.open(open(file_path, "rb"), "rt", encoding="utf-8") as f:
                        id = 0  # Initialize ID for each file
                        for row in f:
                            item = json.loads(row)
                            yield {
                                "text": item["content"],
                                "created_date": item["warc_headers"]["warc-date"],
                                "source": "oscar_colossal_{}".format(folder_name),
                                # Use the ID within the file
                                "source_id": str(id),
                                "meta": str(
                                    {
                                        "url": item["warc_headers"]["warc-target-uri"],
                                        "quality_warnings": item["metadata"][
                                            "quality_warnings"
                                        ],
                                    }
                                ),
                            }
                            id += 1  # Increment ID within the file

                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")


if __name__ == "__main__":
    if not os.path.exists(f"{output_dir}/{version}/data/"):
        os.makedirs(f"{output_dir}/{version}/data/")

    if scratch_location:
        if not os.path.exists(f"{scratch_location}/{version}/data/"):
            os.makedirs(f"{scratch_location}/{version}/data/")
        scratch_writer = jsonlines.open(
            f"{scratch_location}/{version}/data/data.jsonl", "w"
        )

    with jsonlines.open(f"{output_dir}/{version}/data/data.jsonl", "w") as writer:
        print("Loading dataset")

        if source == "mc4":
            dataset = load_dataset(
                "json",
                data_files=[
                    f"{input_based_path}/{input_version}/data/mc4_th_train.json",
                    f"{input_based_path}/{input_version}/data/mc4_th_validation.json",
                ],
                cache_dir=f"{input_based_path}/{input_version}/data/cache",
            )

        elif source == "oscar_cl":
            dataset = Dataset.from_generator(
                lambda: read_jsonl_zst_files(f"{input_based_path}/{input_version}/data")
            )

        else:
            dataset = load_from_disk(f"{input_based_path}/{input_version}/data")

        print(dataset)

        if "train" in dataset.column_names:
            dataset = dataset["train"]
        if "id" not in dataset.column_names and "source_id" not in dataset.column_names:
            dataset = dataset.add_column(
                "source_id", [i for i in range(len(dataset))]  # noqa: C416
            )

        print("Loaded dataset")

        dataset = dataset.map(
            process_chunk_data,
            num_proc=num_proc,
            batched=True,
            batch_size=batch_size,
            # keep_in_memory=True,
            # Incase that I cannot write in public_datasets, so I write in this instead
            # cache_file_name=f"hf_cache/{source}/processed.arrow",
        )

        for data in dataset:
            filtered_data = filter_field(data, source)
            writer.write(filtered_data)
            if scratch_location:
                scratch_writer.write(filtered_data)

        print("Finish processing")

        create_info_file(config_dict)
        create_metadata_file(config_dict, pipeline_name="internet")

        print("Finish Writing the dataset")
