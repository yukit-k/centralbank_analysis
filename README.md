# Central Bank analysis (FRB)

## Table of Contents
1. Installation
2. Project Description
3. File Description
4. Results
5. Licensing, Authors, Acknowledgements

## 1. Installation
Required libraries are described in requirements.txt. Please pip install those. The code should run with no issues using Python versions 3.*.
1. Move to src directory
   1. cd src
2. Get data from FOMC Website. You can specify document type and from year.
   1. e.g. python FomcGetData.py all
3. Get calendar from FOMC Website.
   1. python FomcGetCalendar.py
4. Download Market Data
   1.  Economic Indices from FRB of St. Louis
       1.  https://fred.stlouisfed.org/searchresults?nasw=0&st=FED%20Rate&t=rate%3Bfederal%3Binterest%20rate&ob=sr&od=desc&types=gen
   2.  Treasury Yields
       1.  https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yieldAll
5. Download Sentiment Dictionary
   1. Loughran and McDonald Sentiment Word Lists (https://sraf.nd.edu/textual-analysis/resources/) 
6. Install necessary versions - you can create own virtual environment
   1. pip install numpy==1.16.4
   2. pip install pandas==0.25.0
   3. pip install torch==1.4.0
   4. pip install tqdm==4.43.0
   5. pip install scikit-plot
   6. pip install transformers
7. Run the jupyter notebooks from No.1 to No.6 for analysis

## 2. Project Description
### 2.1 Business Understanding
FOMC has eight regular meetings to determine the monetary policy.
At each meeting, it publishes press conference minutes, statements as well as scripts in text.
In addition to this regular meetings, the members' speeches and testimonies are also scripted on the website.

At each meeting, the policy makers decide monetary policy and publish the decision along with their view on current economic situation and forecast, including Forward Guidance since 2012.
There are a number of researches conducted in this field how this affects to financial market such return and volatility of rates, credit, equity, FX, etc. before and after the meeting, including short-term to long-term effects.
Others focuses on predicting the target FED rate to be announced in advance using impulse analysis, theoretical rate like Taylor rule, etc.
In fact, FRB itself publishes how the policy makers use the policy rules here:
https://www.federalreserve.gov/monetarypolicy/policy-rules-and-how-policymakers-use-them.htm

The central banks intend to indicate their potential future monetary policy in their publications as a measure of market communication. 

The objective of this project is to apply NLP on those text published by FOMC to find latent features.
In this project, I examined whether the prediction of rate hike/lower at each FOMC meeting is possible at meaningful level along with other publicly available economic data.
I also used daily price of market instruments to see whether the same can be used as an alpha factor to gain excess return.

Note that I do not have historical tick data available, so short-term impact of a post-meeting press conference and published statements could not be tested.

### 2.2 Data Understanding
Text data is scraped from FOMC Website. Other economic and market data are downloaded from FRB of St. Louis website (FRED)
Data used for each prediction are only those available before the meeting.

#### Text Data (scraped by the scripts)
* FOMC/fomc_calendar.pickle - all FOMC calendar dates
* FOMC/statement.pickle - Statement text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. Statements are available post press conference for almost all meetings, which include rate decision and target rate. From 2008, target rate became a range instead of a single value.
* FOMC/minutes.pickle - Minutes text along with basic attributes such as dates, speaker, title. Each text is also available
 in the directory with the same name. Minutes are summary of FOMC Meeting and contents are structured in sections and paragraphs, most of which were updated in 2011 and 2012. The minutes of regularly scheduled meetings are released three weeks after the date of the policy decision.
* FOMC/presconf_script.pickle - Press conference scripts text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. This is available from 2011. Starting with the speaker name, so extract those spoken by the chairperson because the other person's words are more likely to be questions and not FOMC's view. It is in pdf form, so download pdf and then process the text.
* FOMC/meeting_script.pickle - Meeting scripts text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. FOMC decided to publish this five years after each meeting. It contains all the words spoken during the meeting. It will contain some insight about FOMC discussions and how the consensus about monetary policy is built, but cannot be used in prediction as this is not published for five years.  It is in pdf form, so download pdf and then process the text.
* FOMC/speech.pickle -  Speech text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. There are many speeches published but some of them are not related to monetary policies but various topics such as regulations and governance. Some speeches may contain indication of FOMC policy, so use only those by the chairperson.
* FOMC/testimony.pickle -  Testimony text along with basic attributes such as dates, speaker, title. Each text is also available in the directory with the same name. Like speeches, testimony is not necessarily related to monetary policy. There are semi-annual testimony in the congress, which can be a good inputs of FOMC's view by chairperson, so use only those by the chairperson.
#### Meta Data (downloaded from FRB website)
* MarketData/FEDRates
  * DFEDTAR.csv - Target FED Rate till 2008, Daily
  * DFEDTARU.csv - Target Upper FED Rate from 2008, Daily
  * DFEDTARL.csv - Target Lower FED Rate from 2008, Daily
  * DFF.csv - Effective FED Rate, Daily
* MarketData/GDP
  * GDPC1.csv - Real GDP, Quarterly
  * GDPPOT.csv - Real potential GDP, Quarterly
* MarketData/CPI
  * PCEPILFE.csv - Core PCE excluding Food and Energy, Monthly
  * CPIAUCSL.csv - Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
* MarketData/Employment
  * UNRATE.csv - Unemployment Rate, Monthly
  * PAYEMS.csv - Employment, Monthly
* MarketData/Sales
  * RRSFS.csv - Advance Real Retail and Food Services Sales, monthly
  * HSN1F.csv - New Home Sales, monthly
* MarketData/ISM
  * ISM-MAN_PMI.csv - ISM Purchasing Managers Index
  * ISM-NONMAN_NMI.csv - ISM Non-manufacturing Index
* MarketData/Treasury
  * DailyTreasuryYieldCurveRateData.xml - This is downloaded from US Treasury website (https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yieldAll). This is optional as not used in the final analysis.

* LoughranMcDonald/LoughranMcDonald_SentimentWordLists_2018.csv

### 2.3 Data Preparation
To clean up the data for the analysis, performed the followings.
#### 1_FOMC_Analysis_Sentiment_Lexicon.ipynb
First, take a glance at the FOMC statement to see if it contains any meaningful information.

##### Input: 
* ../data/FOMC/statement.pickle
* ../data/MarketData/FEDRates/DFEDTAR.csv
* ../data/MarketData/FEDRates/DFEDTARU.csv
* ../data/MarketData/FEDRates/DFEDTARL.csv
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

#### 4_FOMC_Analysis_EDA_NonText.ipynb
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

### 2.4 Modelling
#### 5_FOMC_Analysis_ML_NonText.ipynb
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
#### 6_FOMC_Analysis_ML_Text.ipynb
##### Input: 
* ../data/train_data/nontext_train_small.pickle
* ../data/preprocessed/text_no_split
* ../data/preprocessed/text_split_200
* ../data/preprocessed/text_keyword
* ../data/LoughranMcDonald/LoughranMcDonald_SentimentWordLists_2018.csv

##### Output: 
* ../train_data/train_df
* ../train_data/text_df
* ../train_data/split_train_df

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

### 2.5 Evaluation
The outcome of the analysis are summarised as follows.
We examined whether FOMC text data contains useful insight to predict the FED target rate decision (i.e. Raise, Hold or Lower) at the next FOMC meeting.
The data is imbalanced to have more than 60% as Hold, that is. no rate change, therefore we used F1 score in addition to accuracy to measure the performance.
First, we took major economic indices to predict the FOMC decision using various classification algorithms.
Some estimator simply fail to overfit to train data and failed in test data. Others just predict most of the result as Hold, which is natural from accuracy perspective. As a result of grid search cross validation, Random Forest performed the best with Accuracy of 0.625 and f1 (macro) score of 0.497. Also tried ensembling methods such as voting classifier but did not perform well.
Then, we took text data to build ML model with the non-text economic indices above, then train and performed the learning.  A model using cosine similarity of Tfidf vectors on Loughran McDonald sentiment vocabulary was promissing, achieved Accuracy of 0.67 with F1 score of 0.53. Cosine similarity on Negative word list was used as once of important feature in the model. Then we tried Tfidf itself but only achieved Accuary 0.5 and F1 score 0.39.
To improve the performance of text understanding, we then tried RNN - LSTM with fully connected layer with the non-text data inputs at the end. The result was Accuracy of 0.54 and F1 score of 0.38 - in fact there are too less number of training data to train neural network. We only used the first 200 words where each text is avarage 10,000 words length!
To mitigate this, we then split the text by 200 words with 50 words overlap - one drawback of this approach is the non-text part of inputs are repeated many times and not representing actual frequency any more. The result was Accuracy of 0.64 and F1 score of 0.43. We also tried BERT to represent the text latent features but could not improve the overall performance.
As a conclusion, we could observe some useful information in the text to predict FOMC decision better. However, we could not improve the text based prediction performance by Neural Network. This is partly because there are small number of test data to train with each text very long. This can be potentially improved by splitting text more appropriately for relevant content with proper labelling.

### 2.6 Deployment
No deployment as of now but the main findings of the code can be found in each notebook.
The details of findings will be compiled as blog post in the future.

## File Description
* FomcGetCalendar.py - Scraping FOMC Website, create fomc_calendar to save in pickle and csv
* FomcGetData.py - Calls relevant classes to get data from FOMC Website
* fomc_get_data/FomcBase.py - Base abstract class to scrape FOMC Website to download text data
* fomc_get_data/FomcStatement.py - Child class of FomcBase to retrieve statement texts
* fomc_get_data/FomcMinutes.py - Child class of FomcBase to retrieve minutes texts
* fomc_get_data/FomcPresConfScript.py - Child class of FomcBase to retrieve press conference script texts
* fomc_get_data/FomcMeetingScript.py - Child class of FomcBase to retrieve meeting script texts
* fomc_get_data/FomcSpeech.py - Child class of FomcBase to retrieve speech texts
* fomc_get_data/FomcTestimony.py - Child class of FomcBase to retrieve testimonny texts
* 1_FOMC_Analysis_Sentiment_Lexicon.ipynb - Jupyter notebook to briefly check statement sentiment
* 2_FOMC_Analysis_Preprocess_NonText.ipynb - Jupytet notebook to preprocess calendar and market data (non text data)
* 3_FOMC_Analysis_Preprocess_Text.ipynb - Jupyter notebook to preprocess text data downloaded from FOMC website
* 4_FOMC_Analysis_EDA_NonText.ipynb - Jupyter notebook for EDA on meta data 
* 5_FOMC_Analysis_ML_NonText.ipynb - Jupyter notebook for Machine Learning on meta data
* 6_FOMC_Analysis_ML_Text.ipynb - Jupyter notebook for Machine Learning including textual data


The followings are used only for initial check and not required to run:
* FOMC_analyse_website.ipynb
* FOMC_analyse_website_2.ipynb
* FOMC_check_FEDRate.ipynb
* FOMC_Analysis_BERT_MultiSampleDropoutModel.ipynb
* FOMC_Analysis_BERT_Tensorflow.ipynb
* FOMC_Post_Training_BERT.ipynb
* FOMC_Text_Summarization.ipynb

## Licensing, Authors, Acknowledgements
Data attributes to FRED. Loughran McDonald dictionary attributes to https://sraf.nd.edu/textual-analysis/resources/ in University of Notre Dame.
Feel free to use the source code as you would like!
