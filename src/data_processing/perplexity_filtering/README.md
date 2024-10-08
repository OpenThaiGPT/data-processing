# Perplexity preprocessing code

This folder contains codes to preprocess data using the perplexity score computed from a kenlm 5-gram language model trained on Thai wikipedia data.

The main code is in `perplexity.py`

The `notebook` folder contains the experiments, observations and EDA notebooks for perplexity method.

## How does the code work ?

1. The perplexity score of texts will be computed from the language model and taken log.

2. The log-perplexity score will be used as a feature of DecisionTree classifier to predict if the text is garbage. 

3. After classified the amount of text, sampled set of garbage text **S** from step 2 will be sample back and add to training set to teach inappropriate terms to our LLM. Here are the detailed steps.

    - The normal distribution of log-perplexity score will be formed.
    - Compute the PDF (Probability Density Function) of the each log score.
    - Softmax(1-PDF) will be used as probability list for `np.choice` to sample text back. 

## Preparation
- Download model from google drive
```
gdown 1OBbo21v_-esL31rxtNtsMHrA8T1JYqAd
unzip core.zip -d src/data_processing/perplexity_filtering
```

## How to use
For details, see [How to use guide](../../../scripts/pattern_perplexity/README.md).

## Note

- The idea of using perplexity score are originally from [Perplexed by Quality](https://arxiv.org/pdf/2212.10440.pdf).
- **_However, we decided to try another method on the score since the perplexity score and thresholding is not enough to classify bad data acoording to the observation._**
- DecisionTree classifier was train on the sampled OSCAR2023.



