from datetime import datetime
import threading
import sys
import os
import pickle
import re

import requests
from bs4 import BeautifulSoup

import numpy as np
import pandas as pd

# Import parent class
from .FomcBase import FomcBase

class FomcStatement(FomcBase):
    '''
    A convenient class for extracting statement from the FOMC website
    Example Usage:  
        fomc = FomcStatement()
        df = fomc.get_contents()
    '''
    def __init__(self, verbose = True, max_threads = 10, base_dir = '../data/FOMC/'):
        super().__init__('statement', verbose, max_threads, base_dir)

    def _get_links(self, from_year):
        '''
        Override private function that sets all the links for the contents to download on FOMC website
         from from_year (=min(2015, from_year)) to the current most recent year
        '''
        self.links = []
        self.titles = []
        self.speakers = []
        self.dates = []

        r = requests.get(self.calendar_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Getting links from current page. Meetin scripts are not available.
        if self.verbose: print("Getting links for statements...")
        contents = soup.find_all('a', href=re.compile('^/newsevents/pressreleases/monetary\d{8}[ax].htm'))
        self.links = [content.attrs['href'] for content in contents]
        self.speakers = [self._speaker_from_date(self._date_from_link(x)) for x in self.links]
        self.titles = ['FOMC Statement'] * len(self.links)
        self.dates = [datetime.strptime(self._date_from_link(x), '%Y-%m-%d') for x in self.links]
        # Correct some date in the link does not match with the meeting date
        for i, m_date in enumerate(self.dates):
            if m_date == datetime(2019,10,11):
                self.dates[i] = datetime(2019,10,4)

        if self.verbose: print("{} links found in the current page.".format(len(self.links)))

        # Archived before 2015
        if from_year <= 2014:
            print("Getting links from archive pages...")
            for year in range(from_year, 2015):
                yearly_contents = []
                fomc_yearly_url = self.base_url + '/monetarypolicy/fomchistorical' + str(year) + '.htm'
                r_year = requests.get(fomc_yearly_url)
                soup_yearly = BeautifulSoup(r_year.text, 'html.parser')
                yearly_contents = soup_yearly.findAll('a', text = 'Statement')
                for yearly_content in yearly_contents:
                    self.links.append(yearly_content.attrs['href'])
                    self.speakers.append(self._speaker_from_date(self._date_from_link(yearly_content.attrs['href'])))
                    self.titles.append('FOMC Statement')
                    self.dates.append(datetime.strptime(self._date_from_link(yearly_content.attrs['href']), '%Y-%m-%d'))
                    # Correct some date in the link does not match with the meeting date
                    if self.dates[-1] == datetime(2007,6,18):
                        self.dates[-1] = datetime(2007,6,28)
                    elif self.dates[-1] == datetime(2007,8,17):
                        self.dates[-1] = datetime(2007,8,16)
                    elif self.dates[-1] == datetime(2008,1,22):
                        self.dates[-1] = datetime(2008,1,21)
                    elif self.dates[-1] == datetime(2008,3,11):
                        self.dates[-1] = datetime(2008,3,10)
                    elif self.dates[-1] == datetime(2008,10,8):
                        self.dates[-1] = datetime(2008,10,7)

                if self.verbose: print("YEAR: {} - {} links found.".format(year, len(yearly_contents)))

        print("There are total ", len(self.links), ' links for ', self.content_type)

    def _add_article(self, link, index=None):
        '''
        Override a private function that adds a related article for 1 link into the instance variable
        The index is the index in the article to add to. 
        Due to concurrent processing, we need to make sure the articles are stored in the right order
        '''
        if self.verbose:
            sys.stdout.write(".")
            sys.stdout.flush()

        res = requests.get(self.base_url + link)
        html = res.text
        article = BeautifulSoup(html, 'html.parser')
        paragraphs = article.findAll('p')
        self.articles[index] = "\n\n[SECTION]\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])