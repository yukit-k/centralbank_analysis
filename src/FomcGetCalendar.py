from datetime import datetime
import os
import sys
import pickle
import re

import pandas as pd

import requests
from bs4 import BeautifulSoup

from tqdm import tqdm

def dump_df(df, filename="output"):
        '''
        Dump an internal DataFrame df to a pickle file and csv
        '''
        filepath = filename + '.pickle'
        print("")
        print("Writing to ", filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as output_file:
            pickle.dump(df, output_file)
        filepath = filename + '.csv'
        print("Writing to ", filepath)
        df.to_csv(filepath, index=False)

def is_integer(n):
    '''
    Check if an input string can be converted to integer
    '''
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()

if __name__ == '__main__':
    '''
    This program get all calendar date of the past and announced FOMC meetings.
    The first argument is optional to specify from which year to get the date.
    It creates a dataframe and saves a pickle file and csv file.
    '''
    # FOMC website URLs
    base_url = 'https://www.federalreserve.gov'
    calendar_url = base_url + '/monetarypolicy/fomccalendars.htm'

    date_list = []
    pg_name = sys.argv[0]

    if len(sys.argv) != 2:
        print("Usage: ", pg_name)
        print("Please specify the first argument between 1936 and 2015")
        sys.exit(1)    
        
    from_year = sys.argv[1]

    # Handles the first argument, from_year
    if from_year:
        if is_integer(from_year):
            from_year = int(from_year)
        else:
            print("Usage: ", pg_name)
            print("Please specify the first argument between 1936 and 2015")
            sys.exit(1)
        
        if (from_year < 1936) or (from_year>2015):
            print("Usage: ", pg_name)
            print("Please specify the first argument between 1936 and 2015")
            sys.exit(1)
    else:
        from_year = 1936
        print("From year is set as 1936. Please specify the year as the first argument if required.")

    # Retrieve FOMC Meeting date from current page - from 2015 to 2020
    r = requests.get(calendar_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    panel_divs = soup.find_all('div', {"class": "panel panel-default"})

    for panel_div in panel_divs:
        m_year = panel_div.find('h4').get_text()[:4]
        m_months = panel_div.find_all('div', {"class": "fomc-meeting__month"})
        m_dates = panel_div.find_all('div', {"class": "fomc-meeting__date"})
        print("YEAR: {} - {} meetings found.".format(m_year, len(m_dates)))

        for (m_month, m_date) in zip(m_months, m_dates):
            month_name = m_month.get_text().strip()
            date_text = m_date.get_text().strip()
            is_forecast = False
            is_unscheduled = False
            is_month_short = False

            if ("cancelled" in date_text):
                continue
            elif "notation vote" in date_text:
                date_text = date_text.replace("(notation vote)", "").strip()
            elif "unscheduled" in date_text:
                date_text = date_text.replace("(unscheduled)", "").strip()
                is_unscheduled = True
            
            if "*" in date_text:
                date_text = date_text.replace("*", "").strip()
                is_forecast = True
            
            if "/" in month_name:
                month_name = re.findall(r".+/(.+)$", month_name)[0]
                is_month_short = True
            
            if "-" in date_text:
                date_text = re.findall(r".+-(.+)$", date_text)[0]
            
            meeting_date_str = m_year + "-" + month_name + "-" + date_text
            if is_month_short:
                meeting_date = datetime.strptime(meeting_date_str, '%Y-%b-%d')
            else:
                meeting_date = datetime.strptime(meeting_date_str, '%Y-%B-%d')

            date_list.append({"date": meeting_date, "unscheduled": is_unscheduled, "forecast": is_forecast, "confcall": False})

    # Retrieve FOMC Meeting date older than 2015
    for year in range(from_year, 2015):
        hist_url = base_url + '/monetarypolicy/fomchistorical' + str(year) + '.htm'
        r = requests.get(hist_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        if year in (2011, 2012, 2013, 2014):
            panel_headings = soup.find_all('h5', {"class": "panel-heading"})
        else:
            panel_headings = soup.find_all('div', {"class": "panel-heading"})
        print("YEAR: {} - {} meetings found.".format(year, len(panel_headings)))
        for panel_heading in panel_headings:
            date_text = panel_heading.get_text().strip()
            #print("Date: ", date_text)
            regex = r"(January|February|March|April|May|June|July|August|September|October|November|December).*\s(\d*-)*(\d+)\s+(Meeting|Conference Calls?|\(unscheduled\))\s-\s(\d+)"
            date_text_ext = re.findall(regex, date_text)[0]
            meeting_date_str = date_text_ext[4] + "-" + date_text_ext[0] + "-" + date_text_ext[2]
            #print("   Extracted:", meeting_date_str)
            if meeting_date_str == '1992-June-1':
                meeting_date_str = '1992-July-1'
            elif meeting_date_str == '1995-January-1':
                meeting_date_str = '1995-February-1'
            elif meeting_date_str == '1998-June-1':
                meeting_date_str = '1998-July-1'
            elif meeting_date_str == '2012-July-1':
                meeting_date_str = '2012-August-1'
            elif meeting_date_str == '2013-April-1':
                meeting_date_str = '2013-May-1'

            meeting_date = datetime.strptime(meeting_date_str, '%Y-%B-%d')
            is_confcall = "Conference Call" in date_text_ext[3]
            is_unscheduled = "unscheduled" in date_text_ext[3]
            date_list.append({"date": meeting_date, "unscheduled": is_unscheduled, "forecast": False, "confcall": is_confcall})

    df = pd.DataFrame(date_list).sort_values(by=['date'])
    df.reset_index(drop=True, inplace=True)
    print(df)

    # Save
    dump_df(df, "../data/FOMC/fomc_calendar")