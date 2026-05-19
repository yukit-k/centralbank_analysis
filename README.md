# FedSpeak — How to build a NLP pipeline to predict central bank policy changes

## Table of Contents
1. [Project Description](#1-project-description)
2. [Getting Started](#2-getting-started)
3. [Data Understanding](#3-data-understanding)
4. [Code Description](#4-code-description)
5. [Changelog](#5-changelog)
6. [Licensing, Authors, Acknowledgements](#6-licensing-authors-acknowledgements)

## 1. Project Description
Posted a Medium Blog here:
https://yuki678.medium.com/fedspeak-how-to-build-a-nlp-pipeline-to-predict-central-bank-policy-changes-a2f157ca0434?sk=989433349aed4e6dd1faf5a72e848e35

Please refer to the post for business understanding, project overview and analysis result.

## 2. Getting Started

### Requirements

- Python 3.11+
- macOS: `brew install libomp` (required for XGBoost)

### Installation

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Download NLTK data (required by notebooks 1 and 6-7)
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"
```

> **Conda alternative:**
> ```bash
> conda create -n fomc python=3.11 jupyter
> conda activate fomc
> pip install -r src/requirements.txt
> ```

### Download Input Data

1. Create the data directory structure:
   ```bash
   cd data
   mkdir -p FOMC/statement FOMC/minutes FOMC/presconf_script \
            FOMC/meeting_script FOMC/speech FOMC/testimony \
            MarketData/Quandl LoughranMcDonald GloVe \
            preprocessed train_data result models
   cd ..
   ```

2. Scrape text data from the FOMC website (specify document type and start year):
   ```bash
   cd src
   python FomcGetData.py all 1980
   python FomcGetCalendar.py 1980
   ```

3. Download economic data from FRED (St. Louis Fed). The original project used Quandl;
   the FRED API is now the preferred alternative. Download the following CSV files from
   https://fred.stlouisfed.org/ and place them in `data/MarketData/Quandl/`:

   | File | Series | Frequency |
   |---|---|---|
   | `FRED_DFEDTAR.csv` | Federal Funds Target Rate (pre-2008) | Daily |
   | `FRED_DFEDTARU.csv` | Federal Funds Target Rate Upper (post-2008) | Daily |
   | `FRED_DFEDTARL.csv` | Federal Funds Target Rate Lower (post-2008) | Daily |
   | `FRED_DFF.csv` | Effective Federal Funds Rate | Daily |
   | `FRED_GDPC1.csv` | Real GDP | Quarterly |
   | `FRED_GDPPOT.csv` | Real Potential GDP | Quarterly |
   | `FRED_PCEPILFE.csv` | Core PCE | Monthly |
   | `FRED_CPIAUCSL.csv` | CPI | Monthly |
   | `FRED_UNRATE.csv` | Unemployment Rate | Monthly |
   | `FRED_PAYEMS.csv` | Total Nonfarm Employment | Monthly |
   | `FRED_RRSFS.csv` | Advance Retail Sales | Monthly |
   | `FRED_HSN1F.csv` | New Home Sales | Monthly |
   | `ISM_MAN_PMI.csv` | ISM Manufacturing PMI | Monthly |
   | `ISM_NONMAN_NMI.csv` | ISM Non-Manufacturing Index | Monthly |

4. Download the Loughran-McDonald Sentiment Word List CSV from
   https://sraf.nd.edu/textual-analysis/resources/ and place it in
   `data/LoughranMcDonald/`.

5. Download GloVe word vectors (used in notebook 6):
   https://nlp.stanford.edu/projects/glove/ — place `glove.6B.50d.txt` and
   `glove.6B.100d.txt` in `data/GloVe/`.

### Run the Notebooks

```bash
# From the repo root
jupyter notebook
```

Open notebooks **1 through 8** in order. Each notebook reads outputs produced by
the previous one, so they must be run sequentially.

| Notebook | Description | Est. runtime |
|---|---|---|
| `1_FOMC_Analysis_Preliminary.ipynb` | Sentiment analysis on statements | < 1 min |
| `2_FOMC_Analysis_Preprocess_NonText.ipynb` | Preprocess economic data | < 1 min |
| `3_FOMC_Analysis_Preprocess_Text.ipynb` | Preprocess text data | 2–5 min |
| `4_FOMC_Analysis_EDA_FE_NonText.ipynb` | EDA and feature engineering | < 1 min |
| `5_FOMC_Analysis_Baseline.ipynb` | Baseline ML models (sklearn, XGBoost) | 10–30 min |
| `6_FOMC_Analysis_Model_Train.ipynb` | LSTM and BERT model training | Hours (GPU recommended) |
| `7_FOMC_Analysis_By_Sentence.ipynb` | Sentence-level BERT sentiment scoring | Hours (GPU recommended) |
| `8_FOMC_Analysis_Summary.ipynb` | Summary visualisations | < 1 min |

> **GPU note:** Notebooks 6 and 7 train deep learning models (LSTM, BERT). On CPU they
> may take several hours; a CUDA-capable GPU is strongly recommended.
>
> **Google Colab:** All notebooks support Colab. Upload them and the data to Google Drive
> and set `IN_COLAB = True` at the top of each notebook.

### Notebook 7 — Pre-trained BERT Model

Notebook 7 uses a FinancialPhraseBank fine-tuned BERT model. The file
`data/models/finphrase_bert_trained.dict` is stored in Git LFS and may not be present.
The notebook will fall back to `data/tmp/finphrase_bert_trained_2.dict` if available,
and otherwise use the base `bert-base-uncased` weights.

---

## 3. Data Understanding
Text data is scraped from the FOMC website. Economic and market data are downloaded from
the FRB of St. Louis (FRED) database. Data used for each prediction includes only
information available before the meeting date.

#### Text Data
* `FOMC/fomc_calendar.pickle` — all FOMC calendar dates
* `FOMC/statement.pickle` — FOMC statement text with date, speaker, and title. Each text is also saved as a `.txt` file. Statements include the rate decision and target rate. From 2008, the target rate became a range instead of a single value.
* `FOMC/minutes.pickle` — Minutes text with date, speaker, and title. Minutes are structured in sections; released three weeks after each meeting.
* `FOMC/presconf_script.pickle` — Press conference transcript text. Available from 2011. Filtered to chairperson's words only.
* `FOMC/meeting_script.pickle` — Full meeting transcript text. Published five years after each meeting. Not usable for live prediction.
* `FOMC/speech.pickle` — Chairperson speech text.
* `FOMC/testimony.pickle` — Chairperson congressional testimony text.

#### Market Data
Files are in `MarketData/Quandl/`, named by FRED series code. See the table in
[Download Input Data](#download-input-data) for the full list.

#### Loughran-McDonald Dictionary
* `LoughranMcDonald/LoughranMcDonald_SentimentWordLists_2018.csv` — used in the
  preliminary analysis and for building TF-IDF sentiment feature vectors.

---

## 4. Code Description

#### `1_FOMC_Analysis_Preliminary.ipynb`
**Input:** `FOMC/statement.pickle`, FED rate CSVs  
**Output:** plots only  
**Process:**
1. Analyze statement sentiment using the Loughran-McDonald word list
2. Plot positive/negative word counts and net sentiment over time
3. Map FED rate and rate decisions to each statement date
4. Overlay sentiment moving average with FED rate and recession periods
5. Annotate Quantitative Easing events and chairperson tenures

#### `2_FOMC_Analysis_Preprocess_NonText.ipynb`
**Input:** `FOMC/fomc_calendar.pickle`, all market data CSVs  
**Output:** `preprocessed/nontext_data`, `nontext_ma2/3/6/12`, `treasury`, `fomc_calendar`  
**Process:**
1. Load and plot all numerical economic indices
2. Add FED rate and rate decisions to the FOMC meeting calendar
3. Mark QE announcements as lowering events and tapering as raising events
4. Attach the most-recently-available economic indices to each meeting date
5. Calculate Taylor rule variants
6. Calculate moving averages

#### `3_FOMC_Analysis_Preprocess_Text.ipynb`
**Input:** `fomc_calendar.pickle`, all FOMC text pickles  
**Output:** `preprocessed/text_no_split`, `text_split_200`, `text_keyword`  
**Process:**
1. Add QE announcement to the statement corpus
2. Attach rate and decision labels to each document
3. Add word count, next-meeting date, next-meeting rate and decision
4. Clean text (strip section markers, newlines)
5. Split long documents into 200-word windows with 50-word overlap
6. Filter to paragraphs containing policy keywords (≥ 2 occurrences)

#### `4_FOMC_Analysis_EDA_FE_NonText.ipynb`
**Input:** `preprocessed/nontext_data.pickle`, moving average pickles  
**Output:** `train_data/nontext_train_small`, `nontext_train_large`  
**Process:**
1. Correlation analysis to identify predictive features
2. Compare feature distributions across rate-decision classes
3. Impute missing values
4. Build a small dataset (9 selected features) and a large one (all features)

#### `5_FOMC_Analysis_Baseline.ipynb`
**Input:** `train_data/nontext_train_small.pickle`  
**Output:** `result/result_scores`, `baseline_predictions`, `training_data`  
**Process:**
1. Balance classes (Hold / Raise / Lower)
2. Train/test split (shuffle=False to preserve time order)
3. Benchmark 14 classifiers with stratified k-fold cross-validation
4. Hyperparameter search (random + grid) for AdaBoost, ExtraTrees, RandomForest,
   GradientBoosting, and SVM
5. Feature importance analysis
6. Ensemble models: VotingClassifier and XGBoost stacking

#### `6_FOMC_Analysis_Model_Train.ipynb`
**Input:** `train_data/nontext_train_small.pickle`, text pickles, LoughranMcDonald CSV  
**Output:** trained model files  
**Process:**
1. Merge text and non-text data; explore word frequencies
2. Sentiment scoring via TF-IDF against the LM word list
3. Lemmatize, tokenize, and vectorize text
4. Model A — Cosine similarity features → RandomForest
5. Model B — TF-IDF + meta → RandomForest
6. Model C — LSTM with meta concatenation
7. Model D — GloVe embeddings + LSTM + meta
8. Model E — BERT + meta

#### `7_FOMC_Analysis_By_Sentence.ipynb`
**Input:** `preprocessed/text_no_split.pickle`, `text_keyword.pickle`,
pre-trained BERT model, `train_data/train_df.pickle`  
**Output:** `train_data/fomc_sentiment_bert_*`  
**Process:**
1. Split each document into sentences
2. Score each sentence with a FinancialPhraseBank fine-tuned BERT model
3. Aggregate sentence-level sentiment counts per meeting
4. Combine with non-text features and re-run baseline ML models

#### `8_FOMC_Analysis_Summary.ipynb`
**Input:** all preprocessed pickles, `train_data/train_df.pickle`,
`FOMC/statement.pickle`  
**Output:** summary plots  
**Process:**
1. Visualize FED rate history and chairperson tenures
2. Plot economic indices (GDP, CPI, employment, PMI, …)
3. Visualize FOMC text characteristics (word count, document type distribution)
4. Overlay sentiment scores with rate decisions
5. Correlation heatmaps and Taylor rule comparison
6. Final model performance comparison

### Helper Scripts
| File | Purpose |
|---|---|
| `FomcGetData.py` | Scrapes all FOMC document types from the website |
| `FomcGetCalendar.py` | Builds the FOMC meeting calendar pickle |
| `QuandlGetData.py` | Legacy: downloads market data via Quandl API |
| `fomc_get_data/FomcBase.py` | Abstract base class for FOMC web scrapers |
| `fomc_get_data/FomcStatement.py` | Scraper for FOMC statements |
| `fomc_get_data/FomcMinutes.py` | Scraper for minutes |
| `fomc_get_data/FomcPresConfScript.py` | Scraper for press-conference transcripts |
| `fomc_get_data/FomcMeetingScript.py` | Scraper for meeting transcripts |
| `fomc_get_data/FomcSpeech.py` | Scraper for speeches |
| `fomc_get_data/FomcTestimony.py` | Scraper for testimonies |

The following notebooks are exploratory prototypes and not part of the main pipeline:
`FOMC_analyse_website.ipynb`, `FOMC_analyse_website_2.ipynb`,
`FOMC_check_FEDRate.ipynb`, `FOMC_Analysis_BERT_MultiSampleDropoutModel.ipynb`,
`FOMC_Analysis_BERT_Tensorflow.ipynb`, `FOMC_Post_Training_BERT.ipynb`,
`FOMC_Text_Summarization.ipynb`.

---

## 5. Changelog

### 2026-05 — Library upgrade to modern versions

The entire codebase was updated from its original 2020-era dependencies to work with
current library versions. All core notebooks (1–5, 8) now execute without errors on
Python 3.11.

**Dependencies updated** (`src/requirements.txt`):

| Package | Old | New |
|---|---|---|
| numpy | 1.19.4 | ≥ 1.26 |
| pandas | 1.1.4 | ≥ 2.2 |
| scikit-learn | 0.23 | ≥ 1.6 |
| seaborn | 0.11.0 | ≥ 0.13 |
| torch | 1.7.0 | ≥ 2.6 |
| transformers | 3.5.0 | ≥ 4.40 |
| xgboost | 1.2.1 | ≥ 2.0 |
| matplotlib | (implicit) | ≥ 3.9 |
| lxml, python-dateutil, scipy | missing | added |
| textract, quandl | listed | removed (unmaintained / deprecated) |

**Breaking API fixes applied:**

- **seaborn 0.13:** `sns.distplot` → `sns.histplot`; positional barplot args → keyword args; style `'seaborn-whitegrid'` → `'seaborn-v0_8-whitegrid'`
- **sklearn 1.2–1.8:** `plot_confusion_matrix` → `ConfusionMatrixDisplay.from_estimator`; `get_feature_names()` → `get_feature_names_out()`; `base_estimator` → `estimator` in AdaBoost; `algorithm='SAMME.R'` removed; `loss='deviance'` → `'log_loss'`
- **numpy 2.0:** `np.float(x)` → `float(x)`
- **pandas 2.0:** `DataFrame.append()` → `pd.concat()`; nullable `Int64` dtype with `pd.NA` handled before plotting
- **matplotlib 3.9:** string dates in `ax.set_xlim()` / `ax.annotate()` replaced with `pd.Timestamp()`
- **XGBoost 3.x:** `nthread` → `n_jobs`; `LabelEncoder` added for 0-indexed multi-class labels
- **PyTorch 2.6:** `torch.load(..., weights_only=False)` added where full checkpoints are loaded
- **scikit-plot 0.3.7:** patched `scipy.interp` → `numpy.interp` (removed in scipy 1.14)
- **tqdm:** `from tqdm import tqdm_notebook` → `from tqdm.notebook import tqdm`
- **FomcBase.py:** Powell's chairmanship end date updated (reappointed 2022)

**System dependency:** macOS users must run `brew install libomp` for XGBoost support.

---

## 6. Licensing, Authors, Acknowledgements
Data is sourced from FRED (Federal Reserve Bank of St. Louis), ISM, US Treasury, and Quandl.
The Loughran-McDonald sentiment dictionary is from https://sraf.nd.edu/textual-analysis/resources/
at the University of Notre Dame.

Feel free to use the source code as you like!
