# FedSpeak — How to build a NLP pipeline to predict central bank policy changes

## Table of Contents
1. Project Description
2. Installation
3. Data Understanding
4. Code Description
5. Licensing, Authors, Acknowledgements

## 1. Project Description
Posted a Medium Blog here:
https://yuki678.medium.com/fedspeak-how-to-build-a-nlp-pipeline-to-predict-central-bank-policy-changes-a2f157ca0434?sk=989433349aed4e6dd1faf5a72e848e35

Please refer to the post for business understanding, project overview and analysis result.

## 2. Installation
#### Libraries
Required libraries are described in requirements.txt. The code should run with no issues using Python versions 3.6+.
Create a virtual environment of your choice. Here uses Anaconda:
```
conda create -n fomc python=3.6 jupyter
conda activate fomc
pip install -r requirements.tx
```
#### Download input data
1. Create data directory
   ```
   cd data
   mkdir FOMC MarketData LoughranMcDonald GloVe preprocessed train_data result
   cd FOMC
   mkdir statement minutes presconf_script meeting_script script_pdf speech testimony chair
   cd ../MarketData
   mkdir Quandl
   ```
2. Move to src directory
   `cd ../../src`
3. Get data from FOMC Website. Specify document type. You can also specify from year.
   `python FomcGetData.py all 1980`
4. Get calendar from FOMC Website. Specify from year.
   `python FomcGetCalendar.py 1980`
5. Get data from Quandl. Specify your API Key and From Date (yyyy-mm-dd). You can specify Quandl Code, otherwise all required data are downloaded.
   `python QuandlGetData.py [your API Key] 1980-01-01`
6. Download Sentiment Dictionary in data/LoughranMcDonald directory in csv
   * Loughran and McDonald Sentiment Word Lists (https://sraf.nd.edu/textual-analysis/resources/) 

#### To Run Notebook (Local)

1. Go to top directory
   `cd ../`
2. Run the jupyter notebooks 
   `jupyter notebook`
3. Open and run notebooks No.1 to No.8 for analysis

#### To Run Notebook (Google Colab)
All notebooks can be executed on Google Colab. 
1. Upload notebooks to your Google Drive
2. Upload downloaded data to your Google Drive (Colab Data dir)
3. Execute each notebook (Note: You need to authorize the access to your Google Drive when asked to input the code)


## 3. Data Understanding
Text data is scraped from FOMC Website. Other economic and market data are downloaded from FRB of St. Louis website (FRED)
Data used for each prediction are only those available before the meeting.

#### Text Data
* FOMC/fomc_calendar.pickle - all FOMC calendar dates
* FOMC/statement.pickle - Statement text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. Statements are available post press conference for almost all meetings, which include rate decision and target rate. From 2008, target rate became a range instead of a single value.
* FOMC/minutes.pickle - Minutes text along with basic attributes such as dates, speaker, title. Each text is also available
 in the directory with the same name. Minutes are summary of FOMC Meeting and contents are structured in sections and paragraphs, most of which were updated in 2011 and 2012. The minutes of regularly scheduled meetings are released three weeks after the date of the policy decision.
* FOMC/presconf_script.pickle - Press conference scripts text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. This is available from 2011. Starting with the speaker name, so extract those spoken by the chairperson because the other person's words are more likely to be questions and not FOMC's view. It is in pdf form, so download pdf and then process the text.
* FOMC/meeting_script.pickle - Meeting scripts text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. FOMC decided to publish this five years after each meeting. It contains all the words spoken during the meeting. It will contain some insight about FOMC discussions and how the consensus about monetary policy is built, but cannot be used in prediction as this is not published for five years.  It is in pdf form, so download pdf and then process the text.
* FOMC/speech.pickle -  Speech text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. There are many speeches published but some of them are not related to monetary policies but various topics such as regulations and governance. Some speeches may contain indication of FOMC policy, so use only those by the chairperson.
* FOMC/testimony.pickle -  Testimony text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. Like speeches, testimony is not necessarily related to monetary policy. There are semi-annual testimony in the congress, which can be a good inputs of FOMC's view by chairperson, so use only those by the chairperson.

#### Market Data
In MarketData/Quandl, csv is saved with Quandl Code as the file name.
* FED Rate
  * FRED_DFEDTAR.csv - Target FED Rate till 2008, Daily
  * FRED_DFEDTARU.csv - Target Upper FED Rate from 2008, Daily
  * FRED_DFEDTARL.csv - Target Lower FED Rate from 2008, Daily
  * FRED_DFF.csv - Effective FED Rate, Daily
* GDP
  * FRED_GDPC1.csv - Real GDP, Quarterly
  * FRED_GDPPOT.csv - Real potential GDP, Quarterly
* CPI
  * FRED_PCEPILFE.csv - Core PCE excluding Food and Energy, Monthly
  * FRED_CPIAUCSL.csv - Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
* Employment
  * FRED_UNRATE.csv - Unemployment Rate, Monthly
  * FRED_PAYEMS.csv - Employment, Monthly
* Sales
  * FRED_RRSFS.csv - Advance Real Retail and Food Services Sales, monthly
  * FRED_HSN1F.csv - New Home Sales, monthly
* ISM
  * ISM_MAN_PMI.csv - ISM Purchasing Managers Index
  * ISM_NONMAN_NMI.csv - ISM Non-manufacturing Index
* Treasury
  * USTREASURY_YIELD.csv - This is optional as not used in the final analysis.

#### Loughran-McDonald Dictionary
* LoughranMcDonald/LoughranMcDonald_SentimentWordLists_2018.csv - This is used in preliminary analysis and creating Tfidf vectors.

## 4. Code Description
#### 1_FOMC_Analysis_Preliminary.ipynb
First, take a glance at the FOMC statement to see if it contains any meaningful information.
##### Input: 
* ../data/FOMC/statement.pickle
* ../data/MarketData/Quandl/FRED_DFEDTAR.csv
* ../data/MarketData/Quandl/FRED_DFEDTARU.csv
* ../data/MarketData/Quandl/FRED_DFEDTARL.csv
##### Output:
* None
##### Process:
1. Analyze sentiment of the statement text using Loughran and McDonald Sentiment Word Lists
2. Plot sentiment (count of positive words with negation, negative words and net over time series, normalized by the number of words
3. Load FED Rate, map the rate and decision to statement
4. Plot the moving average of the sentiment along with FED rate and recession period
5. Plot the same with Quantitative Easing and Chairpersons

#### 2_FOMC_Analysis_Preprocess_NonText.ipynb
Next, preprocess nontext meta data. Do necessary calculations and add to the calendar dataframe to map those latest available indices as input to the FOMC Fed rate decision.

##### Input: 
* ../data/FOMC/fomc_calendar.pickle
* All Market Data and Economic Indices
##### Output:
* ../data/preprocessed/nontext_data
* ../data/preprocessed/nontext_ma2
* ../data/preprocessed/nontext_ma3
* ../data/preprocessed/nontext_ma6
* ../data/preprocessed/nontext_ma12
* ../data/preprocessed/treasury
* ../data/preprocessed/fomc_calendar
##### Process:
1. Load and plot all numerical data
2. Add FED Rate and rate decisions to FOMC Meeting Calendar
3. Add QE as Lowering event and Tapering as Raising event
4. Add the economic indices to the FOMC Meeting Calendar
5. Calculate Taylor rule
6. Calculate moving average
7. Save data

#### 3_FOMC_Analysis_Preprocess_Text.ipynb
##### Input: 
* ../data/preprocessed/fomc_calendar.pickle
* ../data/FOMC/statement.pickle
* ../data/FOMC/minutes.pickle
* ../data/FOMC/meeting_script.pickle
* ../data/FOMC/presconf_script.pickle
* ../data/FOMC/speech.pickle
* ../data/FOMC/testimony.pickle
##### Output: 
* ../data/preprocessed/text_no_split
* ../data/preprocessed/text_split_200
* ../data/preprocessed/text_keyword

##### Process: 
1. Add QE announcement to statement
2. Add Rate and Decision to Statement, Minutes, Meeting Script and Presconf Script
3. Add Word Count, Next Meeting Date, Next Meeting Rate and Next Meeting Decision to all inputs
4. Remove return code and separate text by sections
5. Remove short sections - having less number of words that threshold as it is unlikely to hold good information
6. Split text of Step 5 to maximum of 200 words with 50 words overlap
7. Filter text of Step 5 for those having keyword at least 2 times only

#### 4_FOMC_Analysis_EDA_FE_NonText.ipynb
##### Input: 
* ../data/preprocessed/nontext_data.pickle
* ../data/preprocessed/nontext_ma2.pickle
* ../data/preprocessed/nontext_ma3.pickle
* ../data/preprocessed/nontext_ma6.pickle
* ../data/preprocessed/nontext_ma12.pickle
##### Output: 
* ../data/train_data/nontext_train_small
* ../data/train_data/nontext_train_large

##### Process: 
1. Check correlation to find good feature to predict Rate Decision
2. Check correlation of moving average to Rate Decision
3. Check correlation of calculated rates and changes by taylor rules
4. Compare distribution of each feature between Rate Decision
5. Fill missing values
6. Create small dataset with selected 9 features and large dataset, which contains all

#### 5_FOMC_Analysis_Baseline.ipynb
##### Input: 
* ../data/train_data/nontext_train_small.pickle or
* ../data/train_data/nontext_train_large.pickle
##### Output: 
* ../data/result/result_scores
* ../data/result/baseline_predictions
* ../data/result/training_data

##### Process: 
1. Balancing the classes
2. Convert the target to integer starting from 0
3. Train test split
4. Apply 14 different classifiers to see how they perform
5. Build and run random search and grid search cross validation models for the following classifiers
   1. ADA Boost on Decision Tree
   2. Extra Tree
   3. Random Forest
   4. Gradient Boosting
   5. Support Vector Machine
6. Check Feature Importance
7. Build and run Ensemble models
   1. Voting Classifier
   2. Stacking by XG Boost

#### 6_FOMC_Analysis_Model_Train.ipynb
##### Input: 
* ../data/train_data/nontext_train_small.pickle
* ../data/preprocessed/text_no_split.pickle
* ../data/preprocessed/text_split_200.pickle
* ../data/preprocessed/text_keyword.pickle
* ../data/LoughranMcDonald/LoughranMcDonald_SentimentWordLists_2018.csv

##### Output: 

##### Process: 
1. Check the record count, drop meeting scripts
2. Select which text to use and merge the text to nontext train dataframe
3. View text by creating corpus to see word frequencies
4. Load LoughranMcDonald Sentiment word list and analyze the sentiment of each text
5. Lemmatize, remove stop words, tokenize texts as well as sentiment word
6. Vectorize the text by Tfidf
7. Calculate Cosine Similarity and add difference from the previous text
8. Convert the target to integer starting from 0, use Stratified KFold
9. Model A - Use Cosine Similarity for Random Forest
10. Model B - Use Tfidf vector and merge with meta data to perform Random Forest
11. Model C - Use LSTM (RNN) based text analysis, then merge with meta data at the last dense layer
12. Model D - Use GloVe Word Embedding for Model C
13. Further split of training data to max 200 words with 50 words overlap and perform Model D again
14. Model E - User BERT, then merge with meta data at the last dense layer

#### 7_FOMC_Analysis_By_Sentence.ipynb
##### Input: 
* ../data/preprocessed/text_no_split.pickle
* ../data/preprocessed/text_keyword.pickle
* ../data/models/finphrase_bert_trained.dict
* ../train_data/train_df.pickle

##### Output: 
* ../train_data/sentiment_bert_result
* ../train_data/sentiment_bert_all
* ../train_data/sentiment_bert_stmt
* ../train_data/sentiment_bert_minutes
* ../train_data/sentiment_bert_presconf
* ../train_data/sentiment_bert_m_script
* ../train_data/sentiment_bert_speech
* ../train_data/sentiment_bert_testimony

##### Process: 
1. Check the record count, combine meeting scripts by speaker
2. Split each text by sentence
3. Load a trained BERT model and run prediction
4. Count the number of sentences per predicted sentiment for each FOMC Meeting
5. Visualize the result
6. Combine the result with Non-text data
7. Perform the same machine learning as the baseline model

#### 8_FOMC_Analysis_Summary.ipynb
##### Input:
* ../data/preprocessed/fomc_calendar.pickle
* ../data/preprocessed/nontext_data.pickle
* ../data/preprocessed/text_no_split.pickle
* ../data/train_data/train_df.pickle
* ../data/FOMC/statement.pickle

##### Input:
1. Visualize FED Rate
2. Visualize Economic Indices
3. Visualize FOMC Text
4. Visualize Sentiment
5. Visualize Correlation, Taylor Rule
6. Visualize the final result

### Other Files
* FomcGetCalendar.py - From FOMC Website, create fomc_calendar to save in pickle and csv
* FomcGetData.py - Calls relevant classes to get data from FOMC Website
* QuandlGetData.py - Get market data from Quandl.
* fomc_get_data/FomcBase.py - Base abstract class to scrape FOMC Website to download text data
* fomc_get_data/FomcStatement.py - Child class of FomcBase to retrieve statement texts
* fomc_get_data/FomcMinutes.py - Child class of FomcBase to retrieve minutes texts
* fomc_get_data/FomcPresConfScript.py - Child class of FomcBase to retrieve press conference script texts
* fomc_get_data/FomcMeetingScript.py - Child class of FomcBase to retrieve meeting script texts
* fomc_get_data/FomcSpeech.py - Child class of FomcBase to retrieve speech texts
* fomc_get_data/FomcTestimony.py - Child class of FomcBase to retrieve testimonny texts

The followings are used only for initial check and not required to run:
* FOMC_analyse_website.ipynb
* FOMC_analyse_website_2.ipynb
* FOMC_check_FEDRate.ipynb
* FOMC_Analysis_BERT_MultiSampleDropoutModel.ipynb
* FOMC_Analysis_BERT_Tensorflow.ipynb
* FOMC_Post_Training_BERT.ipynb
* FOMC_Text_Summarization.ipynb

## 5. Licensing, Authors, Acknowledgements
Data attributes to the source (FRED, ISM, US Treasury and Quandl). Loughran McDonald dictionary attributes to https://sraf.nd.edu/textual-analysis/resources/ in University of Notre Dame.
Feel free to use the source code as you would like!
