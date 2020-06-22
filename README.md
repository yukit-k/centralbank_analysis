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

##### Output: 

##### Process: 

#### 4_FOMC_Analysis_EDA_NonText.ipynb
##### Input: 

##### Output: 

##### Process: 

### 2.4 Modelling
#### 5_FOMC_Analysis_ML_NonText.ipynb
##### Input: 

##### Output: 

##### Process: 

#### 6_FOMC_Analysis_ML_Text.ipynb
##### Input: 

##### Output: 

##### Process: 

### 2.5 Evaluation
The outcome of the analysis are summarised as follows.
-- To Do --

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
