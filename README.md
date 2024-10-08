# Data Processing Pipeline Overview
This pipeline is designed to address data contamination issues, which can degrade model performance and introduce bias. Therefore, it is essential to manage this problem through the following methods:

* `Pattern Filtering`: Uses rule-based techniques to filter out inappropriate content (e.g., gambling, advertisements) by detecting prohibited words and filtering out text with a high number of such words.
  * For details, see [How to use Pattern Filtering](src/scripts/pattern_perplexity/README.md).
* `Perplexity Filtering`: This step filters out spam or out-of-context sentences that may negatively affect model performance by computing the perplexity of text chunks using a language model.
  * For details, see [How to use Perplexity Filtering](src/scripts/pattern_perplexity/README.md).
* `Deduplication`: Further removes exact duplicates using hash functions to ensure no repeated sentences remain.
  * For details, see [How to use Deduplication](src/scripts/deduplication/README.md).
* `Decontamination`: Aims to prevent training data from leaking into test sets by applying N-Gram MinHash and LSH techniques across both training and evaluation datasets.
  * For details, see [How to use Decontamination](src/scripts/decontamination/README.md).
* `Anonymization`: Uses Named Entity Recognition (NER) models to filter out sensitive information, such as names and ID numbers, from the datasets.
  * For details, see [How to use Anonymization](src/scripts/anonymization/README.md).

Folder `scripts` contains the main program which will call function in folder `data_processing`
