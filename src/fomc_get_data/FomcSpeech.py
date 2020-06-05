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

class FomcSpeech(FomcBase):
    '''
    A convenient class for extracting speech from the FOMC website
    Example Usage:  
        fomc = FomcSpeech()
        df = fomc.get_contents()
    '''
    def __init__(self, verbose = True, max_threads = 10, base_dir = '../data/FOMC/'):
        super().__init__('speech', verbose, max_threads, base_dir)
        self.speech_base_url = self.base_url + '/newsevents/speech'

    def _get_links(self, from_year):
        '''
        Override private function that sets all the links for the contents to download on FOMC website
         from from_year (=min(2015, from_year)) to the current most recent year
        '''
        self.links = []
        self.titles = []
        self.speakers = []
        self.dates = []

        res = requests.get(self.calendar_url)
        soup = BeautifulSoup(res.text, 'html.parser')

        if self.verbose: print("Getting links for speeches...")
        to_year = datetime.today().strftime("%Y")

        if from_year <= 1995:
            print("Archive only from 1996, so setting from_year as 1996...")
            from_year = 1996
        for year in range(from_year, int(to_year)+1):
            # Archived between 1996 and 2005, URL changed from 2011
            if year < 2011:
                speech_url = self.speech_base_url + '/' + str(year) + 'speech.htm'
            else:
                speech_url = self.speech_base_url + '/' + str(year) + '-speeches.htm'

            res = requests.get(speech_url)
            soup = BeautifulSoup(res.text, 'html.parser')
            speech_links = soup.findAll('a', href=re.compile('^/?newsevents/speech/.*{}\d\d\d\d.*.htm|^/boarddocs/speeches/{}/|^{}\d\d\d\d.*.htm'.format(str(year), str(year), str(year))))
            for speech_link in speech_links:
                # Sometimes the same link is put for watch live video. Skip those.
                if speech_link.find({'class': 'watchLive'}):
                    continue

                # Add link, title and date
                self.links.append(speech_link.attrs['href'])
                self.titles.append(speech_link.get_text())
                self.dates.append(datetime.strptime(self._date_from_link(speech_link.attrs['href']), '%Y-%m-%d'))

                # Add speaker
                # Somehow the speaker is before the link in 1997 only, whereas the others is vice-versa
                if year == 1997:
                    # Somehow only the linke for December 15 speech has speader after the link in 1997 page.
                    if speech_link.get('href') == '/boarddocs/speeches/1997/19971215.htm':
                        tmp_speaker = speech_link.parent.next_sibling.next_element.get_text().replace('\n', '').strip()
                    else:
                        tmp_speaker = speech_link.parent.previous_sibling.previous_sibling.get_text().replace('\n', '').strip()
                else:
                    # Somehow 20051128 and 20051129 are structured differently
                    if speech_link.get('href') in ('/boarddocs/speeches/2005/20051128/default.htm', '/boarddocs/speeches/2005/20051129/default.htm'):
                        tmp_speaker = speech_link.parent.previous_sibling.previous_sibling.get_text().replace('\n', '').strip()
                    tmp_speaker = speech_link.parent.next_sibling.next_element.get_text().replace('\n', '').strip()
                    # When a video icon is placed between the link and speaker
                    if tmp_speaker in ('Watch Live', 'Video'):
                        tmp_speaker = speech_link.parent.next_sibling.next_sibling.next_sibling.next_element.get_text().replace('\n', '').strip()
                self.speakers.append(tmp_speaker)
            if self.verbose: print("YEAR: {} - {} speeches found.".format(year, len(speech_links)))

    def _add_article(self, link, index=None):
        '''
        Override a private function that adds a related article for 1 link into the instance variable
        The index is the index in the article to add to. 
        Due to concurrent prcessing, we need to make sure the articles are stored in the right order
        '''
        if self.verbose:
            sys.stdout.write(".")
            sys.stdout.flush()

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
            if fn.parent:
                fn.parent.decompose()
            else:
                fn.decompose()
        # Get all p tag
        paragraphs = article.findAll('p')
        self.articles[index] = "\n\n[SECTION]\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])