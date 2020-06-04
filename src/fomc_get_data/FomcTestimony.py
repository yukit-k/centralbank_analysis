from datetime import datetime
import threading
import sys
import os
import pickle
import re

import requests
from bs4 import BeautifulSoup
import json

import numpy as np
import pandas as pd

# Import parent class
from .FomcBase import FomcBase

class FomcTestimony(FomcBase):
    '''
    A convenient class for extracting testimony from the FOMC website.
    Among testimonies, there are semi annual monetary policy report to the Congress by chairperson.
    Example Usage:  
        fomc = FomcTestimony()
        df = fomc.get_contents()
    '''
    def __init__(self, verbose = True, max_threads = 10, base_dir = '../data/FOMC/'):
        super().__init__('testimony', verbose, max_threads, base_dir)

    def _get_links(self, from_year):
        '''
        Override private function that sets all the links for the contents to download on FOMC website
         from from_year (=min(1996, from_year)) to the current most recent year
        '''
        self.links = []
        self.titles = []
        self.speakers = []
        self.dates = []

        if self.verbose: print("Getting links for testimony...")
        to_year = datetime.today().strftime("%Y")

        if from_year < 1996:
            print("Archive only from 1996, so setting from_year as 1996...")
            from_year = 1996
        elif from_year > 2006:
            print("All data from 2006 is in a single json, so return all from 2006 anyway though specified from year is ", from_year)

        url = self.base_url + '/json/ne-testimony.json'
        res = requests.get(url)
        res_list = json.loads(res.text)
        for record in res_list:
            doc_link = record.get('l')
            if doc_link:
                self.links.append(doc_link)
                self.titles.append(record.get('t'))
                self.speakers.append(record.get('s'))
                date_str = record.get('d').split(" ")[0]
                self.dates.append(datetime.strptime(date_str, '%m/%d/%Y'))

        if from_year < 2006:
            for year in range(from_year, 2006):
                url = self.base_url + '/newsevents/testimony/' + str(year) + 'testimony.htm'

                res = requests.get(url)
                soup = BeautifulSoup(res.text, 'html.parser')

                doc_links = soup.findAll('a', href=re.compile('^/boarddocs/testimony/{}/|^/boarddocs/hh/{}/'.format(str(year), str(year))))
                for doc_link in doc_links:
                    # Sometimes the same link is put for watch live video. Skip those.
                    if doc_link.find({'class': 'watchLive'}):
                        continue
                    # Add links
                    self.links.append(doc_link.attrs['href'])

                    # Handle mark-up mistakes
                    if doc_link.get('href') in ('/boarddocs/testimony/2005/20050420/default.htm'):
                        title = doc_link.get_text()
                        speaker = doc_link.parent.parent.next_element.next_element.get_text().replace('\n', '').strip()
                        date_str = doc_link.parent.parent.next_element.replace('\n', '').strip()
                    elif doc_link.get('href') in ('/boarddocs/testimony/1997/19970121.htm'):
                        title = doc_link.parent.parent.find_next('em').get_text().replace('\n', '').strip()
                        speaker = doc_link.parent.parent.find_next('strong').get_text().replace('\n', '').strip()
                        date_str = doc_link.get_text()
                    else:
                        title = doc_link.get_text()
                        speaker = doc_link.parent.find_next('div').get_text().replace('\n', '').strip()
                        # When a video icon is placed between the link and speaker
                        if speaker in ('Watch Live', 'Video'):
                            speaker = doc_link.parent.find_next('p').find_next('p').get_text().replace('\n', '').strip()
                        date_str = doc_link.parent.parent.next_element.replace('\n', '').strip()

                    self.titles.append(doc_link.get_text())
                    self.speakers.append(speaker)
                    self.dates.append(datetime.strptime(date_str, '%B %d, %Y'))
                    
                if self.verbose: print("YEAR: {} - {} testimony docs found.".format(year, len(doc_links)))

    def _add_article(self, link, index=None):
        '''
        Override a private function that adds a related article for 1 link into the instance variable
        The index is the index in the article to add to. 
        Due to concurrent prcessing, we need to make sure the articles are stored in the right order
        '''
        if self.verbose:
            sys.stdout.write(".")
            sys.stdout.flush()

        link_url = self.base_url + link
        # article_date = self._date_from_link(link)

        #print(link_url)

        # date of the article content
        # self.dates.append(article_date)

        res = requests.get(self.base_url + link)
        html = res.text
        # p tag is not properly closed in many cases
        html = html.replace('<P', '<p').replace('</P>', '</p>')
        html = html.replace('<p', '</p><p').replace('</p><p', '<p', 1)
        # remove all after appendix or references
        x = re.search(r'(<b>references|<b>appendix|<strong>references|<strong>appendix)', html.lower())
        if x:
            html = html[:x.start()]
            html += '</body></html>'
        # Parse html text by BeautifulSoup
        article = BeautifulSoup(html, 'html.parser')
        # Remove footnote
        for fn in article.find_all('a', {'name': re.compile('fn\d')}):
            # if fn.parent:
            #     fn.parent.decompose()
            # else:
            fn.decompose()
        # Get all p tag
        paragraphs = article.findAll('p')
        self.articles[index] = "\n\n[SECTION]\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])