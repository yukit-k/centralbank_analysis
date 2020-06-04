from datetime import date
import re
import threading
import pickle
import sys
import os

import requests
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

from abc import ABCMeta, abstractmethod

class FomcBase(metaclass=ABCMeta):
    '''
    A base class for extracting documents from the FOMC website
    '''

    def __init__(self, content_type, verbose, max_threads, base_dir):
        
        # Set arguments to internal variables
        self.content_type = content_type
        self.verbose = verbose
        self.MAX_THREADS = max_threads
        self.base_dir = base_dir

        # Initialization
        self.df = None
        self.links = None
        self.dates = None
        self.articles = None
        self.speakers = None
        self.titles = None

        # FOMC website URLs
        self.base_url = 'https://www.federalreserve.gov'
        self.calendar_url = self.base_url + '/monetarypolicy/fomccalendars.htm'

        # FOMC Chairperson's list
        self.chair = pd.DataFrame(
            data=[["Greenspan", "Alan", "1987-08-11", "2006-01-31"], 
                  ["Bernanke", "Ben", "2006-02-01", "2014-01-31"], 
                  ["Yellen", "Janet", "2014-02-03", "2018-02-03"],
                  ["Powell", "Jerome", "2018-02-05", "2022-02-05"]],
            columns=["Surname", "FirstName", "FromDate", "ToDate"])
        
    def _date_from_link(self, link):
        date = re.findall('[0-9]{8}', link)[0]
        if date[4] == '0':
            date = "{}-{}-{}".format(date[:4], date[5:6], date[6:])
        else:
            date = "{}-{}-{}".format(date[:4], date[4:6], date[6:])
        return date

    def _speaker_from_date(self, article_date):
        if self.chair.FromDate[0] < article_date and article_date < self.chair.ToDate[0]:
            speaker = self.chair.FirstName[0] + " " + self.chair.Surname[0]
        elif self.chair.FromDate[1] < article_date and article_date < self.chair.ToDate[1]:
            speaker = self.chair.FirstName[1] + " " + self.chair.Surname[1]
        elif self.chair.FromDate[2] < article_date and article_date < self.chair.ToDate[2]:
            speaker = self.chair.FirstName[2] + " " + self.chair.Surname[2]
        elif self.chair.FromDate[3] < article_date and article_date < self.chair.ToDate[3]:
            speaker = self.chair.FirstName[3] + " " + self.chair.Surname[3]
        else:
            speaker = "other"
        return speaker
        
    @abstractmethod
    def _get_links(self, from_year):
        '''
        private function that sets all the links for the FOMC meetings
         from the giving from_year to the current most recent year
         from_year is min(2015, from_year)
        '''
        # Implement in sub classes
        pass
    
    @abstractmethod
    def _add_article(self, link, index=None):
        '''
        adds the related article for 1 link into the instance variable
        index is the index in the article to add to. Due to concurrent
        prcessing, we need to make sure the articles are stored in the
        right order
        '''
        # Implement in sub classes
        pass

    def _get_articles_multi_threaded(self):
        '''
        gets all articles using multi-threading
        '''
        if self.verbose:
            print("Getting articles - Multi-threaded...")

        self.articles = ['']*len(self.links)
        jobs = []
        # initiate and start threads:
        index = 0
        while index < len(self.links):
            if len(jobs) < self.MAX_THREADS:
                t = threading.Thread(target=self._add_article, args=(self.links[index],index,))
                jobs.append(t)
                t.start()
                index += 1
            else:    # wait for threads to complete and join them back into the main thread
                t = jobs.pop(0)
                t.join()
        for t in jobs:
            t.join()

        #for row in range(len(self.articles)):
        #    self.articles[row] = self.articles[row].strip()

    def get_contents(self, from_year=1990):
        '''
        Returns a Pandas DataFrame with the date as the index for a date range of from_year to the most current.
        Save the same to internal df as well.
        '''
        self._get_links(from_year)
        self._get_articles_multi_threaded()
        dict = {
            'date': self.dates,
            'contents': self.articles,
            'speaker': self.speakers, 
            'title': self.titles
        }
        self.df = pd.DataFrame(dict).sort_values(by=['date'])
        self.df.reset_index(drop=True, inplace=True)
        return self.df

    def pickle_dump_df(self, filename="output.pickle"):
        '''
        Dump an internal DataFrame df to a pickle file
        '''
        filepath = self.base_dir + filename
        print("")
        if self.verbose: print("Writing to ", filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as output_file:
            pickle.dump(self.df, output_file)

    def save_texts(self, prefix="FOMC_", target="contents"):
        '''
        Save an internal DataFrame df to text files
        '''
        tmp_dates = []
        tmp_seq = 1
        for i, row in self.df.iterrows():
            cur_date = row['date'].strftime('%Y-%m-%d')
            if cur_date in tmp_dates:
                tmp_seq += 1
                filepath = self.base_dir + prefix + cur_date + "-" + str(tmp_seq) + ".txt"
            else:
                tmp_seq = 1
                filepath = self.base_dir + prefix + cur_date + ".txt"
            tmp_dates.append(cur_date)
            if self.verbose: print("Writing to ", filepath)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as output_file:
                output_file.write(row[target])