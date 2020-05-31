# Central Bank analysis (FRB)

## Table of Contents
1. Installation
2. Project Description
3. File Description
4. Results
5. Licensing, Authors, Acknowledgements

## 1. Installation
Required libraries are described in requirements.txt. Please pip install those. The code should run with no issues using Python versions 3.*.

## 2. Project Description
### 2.1 Business Understanding
FOMC has eight regular meetings to determine the monetary policy.
At each meeting, it publishes press conference minutes, statements as well as scripts in text.
In addition to this regular meetings, the members' speeches are also scripted on the website.

At each meeting, the policy makers decide monetary policy and publish the decision along with their view on current economic situation and forecast, including Forward Guidance since 2012.
There are a number of researches conducted in this field how this affects to financial market such return and volatility of rates, credit, equity, FX, etc. before and after the meeting, including short-term to long-term effects.
Others focuses on predicting the target FED rate to be announced in advance using impulse analysis, theoretical rate like Taylor rule, etc.
In fact, FRB itself publishes how the policy makers use the policy rules here:
https://www.federalreserve.gov/monetarypolicy/policy-rules-and-how-policymakers-use-them.htm

The central banks intend to indicate their potential future monetary policy in their publications as a measure of market communication. 

The objective of this project is to apply NLP on those text published by FOMC to find latent features.
In this project, I examined whether the prediction of rate hike/lower at each FOMC meeting is possible at meaningful level along with other publicly available economic data.
I also used daily price of market instruments to see whether the same can be used as an alpha factor to gain excess return.

Note that I do not have historical tick data available, so short-term impact during a post-meeting press conference could not be tested.
Also, avoided predicting actual FED rate due to the data availability such as the long-term forecast for the three-month Treasury bill rate and that for inflation of the implicit GDP price deflator.

### 2.2 Data Understanding
Text data is scraped from FOMC Website. Other economic and market data are downloaded from FRB of St. Louis website (FRED)

Data used for each prediction are only those available before the meeting.

### 2.3 Data Preparation
To clean up the data for the analysis, performed the followings.
#### 

### 2.4 Modelling
-- To Do --

### 2.5 Evaluation
The outcome of the analysis are summarised as follows.
-- To Do --

### 2.6 Deployment
The main findings of the code can be found at the post available here.
-- To Do --

## File Description
-- To Do --

## Licensing, Authors, Acknowledgements
Data attributes to FRED. Otherwise, feel free to use the code here as you would like!