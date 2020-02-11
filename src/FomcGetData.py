from __future__ import print_function
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import date
import re
import numpy as np
import pandas as pd
import pickle
import threading
import sys

class FOMC (object):
    '''
    A convenient class for extracting meeting minutes from the FOMC website
    Example Usage:  
        fomc = FOMC()
        df = fomc.get_statements()
        fomc.pickle("./df_minutes.pickle")
    '''

    def __init__(self, base_url='https://www.federalreserve.gov', 
                 calendar_url='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm',
                 presconf_url='https://www.federalreserve.gov/mediacenter/files/',
                 speech_base_url='https://www.federalreserve.gov/newsevents/speech',
                 historical_date = 2014,
                 historical_date_speech = 2010,
                 verbose = True,
                 max_threads = 10):

        self.base_url = base_url
        self.calendar_url = calendar_url
        self.speech_base_url = speech_base_url
        self.df = None
        self.links = None
        self.dates = None
        self.speaker = None
        self.articles = None
        self.verbose = verbose
        self.HISTORICAL_DATE = historical_date
        self.HISTORICAL_DATE_SPEECH = historical_date_speech
        self.MAX_THREADS = max_threads
    

    def _get_links(self, from_year):
        '''
        private function that sets all the links for the FOMC meetings from the giving from_year
        to the current most recent year
        '''
        if self.verbose:
            print("Getting links for statements...")
        self.links = []
        fomc_meetings_socket = urlopen(self.calendar_url)
        soup = BeautifulSoup(fomc_meetings_socket, 'html.parser')

        statements = soup.find_all('a', href=re.compile('^/newsevents/pressreleases/monetary\d{8}a.htm'))
        self.links = [statement.attrs['href'] for statement in statements] 

        if from_year <= self.HISTORICAL_DATE:        
            for year in range(from_year, self.HISTORICAL_DATE + 1):
                fomc_yearly_url = self.base_url + '/monetarypolicy/fomchistorical' + str(year) + '.htm'
                fomc_yearly_socket = urlopen(fomc_yearly_url)
                soup_yearly = BeautifulSoup(fomc_yearly_socket, 'html.parser')
                statements_historical = soup_yearly.findAll('a', text = 'Statement')
                for statement_historical in statements_historical:
                    self.links.append(statement_historical.attrs['href'])

    def _get_speech_links(self, from_year):
        if self.verbose:
            print("Getting links for speeches...")
        self.links = []
        to_year = date.today().strftime("%Y")
        if from_year < 1996:
            print("Archive only exist up to 1996, so setting from_year as 1996...")
            from_year = 1996
        
        if from_year <= 2010:
            for year in range(from_year, 2011):
                fomc_speeches_yearly_url = self.speech_base_url + '/' + str(year) + 'speech.htm'
                print(fomc_speeches_yearly_url)
                fomc_speeches_yearly_socket = urlopen(fomc_speeches_yearly_url)
                soup_speeches_yearly = BeautifulSoup(fomc_speeches_yearly_socket, 'html.parser')
                speeches_historical = soup_speeches_yearly.findAll('a', href=re.compile('newsevents/speech/[a-zA-z0-9+.-]+d{8}a.htm'))
                for speech_historical in speeches_historical:
                    self.links.append(speech_historical.attrs['href'])
            from_year = 2011
        from_year = np.max([from_year, 2011])
        for year in range(from_year, int(to_year)+1):
            fomc_speeches_yearly_url = self.speech_base_url + '/' + str(year) + '-speeches.htm'
            print(fomc_speeches_yearly_url)
            fomc_speeches_yearly_socket = urlopen(fomc_speeches_yearly_url)
            soup_speeches_yearly = BeautifulSoup(fomc_speeches_yearly_socket, 'html.parser')
            speeches_historical = soup_speeches_yearly.findAll('a', href=re.compile('newsevents/speech/.*\d{8}a.htm'))
            print(speeches_historical)
            for speech_historical in speeches_historical:
                self.links.append(speech_historical.attrs['href'])

    def _date_from_link(self, link):
        date = re.findall('[0-9]{8}', link)[0]
        if date[4] == '0':
            date = "{}/{}/{}".format(date[:4], date[5:6], date[6:])
        else:
            date = "{}/{}/{}".format(date[:4], date[4:6], date[6:])
        return date

    def _speaker_from_link(self, link):
        speaker_search = re.search('newsevents/speech/(.*)\d{8}(.*)', link)
        if speaker_search:
            speaker = speaker_search.group(1)
        else:
            speaker = "None"
        return speaker

    def _add_article(self, link, index=None):
        '''
        adds the related article for 1 link into the instance variable
        index is the index in the article to add to. Due to concurrent
        prcessing, we need to make sure the articles are stored in the
        right order
        '''
        if self.verbose:
            sys.stdout.write(".")
            sys.stdout.flush()

        # date of the article content
        self.dates.append(self._date_from_link(link))
        self.speaker.append(self._speaker_from_link(link))
        article_socket = urlopen(self.base_url + link)
        article = BeautifulSoup(article_socket, 'html.parser')
        paragraphs = article.findAll('p')
        self.articles[index]= "\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])


    def _get_articles_multi_threaded(self):
        '''
        gets all articles using multi-threading
        '''
        if self.verbose:
            print("Getting articles - Multi-threaded...")

        self.dates, self.speaker, self.articles = [], [], ['']*len(self.links)
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

        for row in range(len(self.articles)):
            self.articles[row] = self.articles[row].strip()


    def get_statements(self, from_year=1990):
        '''
        Returns a Pandas DataFrame of meeting minutes with the date as the index
        uses a date range of from_year to the most current
        Input from_year is ignored if it is within the last 5 years as this is meant for 
        parsing much older years
        '''
        self._get_links(from_year)
        print("There are", len(self.links), 'statements')
        self._get_articles_multi_threaded()

        self.df = pd.DataFrame(self.articles, index=pd.to_datetime(self.dates)).sort_index()
        self.df.columns = ['statements']
        self.df.speaker = self.speaker
        return self.df

    def get_speeches(self, from_year=1990):
        self._get_speech_links(from_year)
        print("There are ", len(self.links), 'speeches')
        self._get_articles_multi_threaded()

        self.df = pd.DataFrame(self.articles, index=pd.to_datetime(self.dates)).sort_index()
        self.df.columns = ['speeches']
        self.df.speaker = self.speaker
        return self.df

    def pickle_dump_df(self, filename="output.pickle"):
        if filename:
            if self.verbose:
                print("Writing to", filename)
            with open(filename, "wb") as output_file:
                    pickle.dump(self.df, output_file)

    def save_texts(self, directory="output", prefix="FOMC_", target="statement"):
        if directory:
            if self.verbose:
                print("Writing to", directory)
            for i in range(self.df.shape[0]):
                filename = directory + '/' + prefix + self.df.index.strftime('%Y-%m-%d')[i] + '_' + self.df.speaker[i] + ".txt"
                with open(filename, "w") as output_file:
                    output_file.write(self.df.iloc[i][target])

if __name__ == '__main__':
    pg_name = sys.argv[0]
    args = sys.argv[1:]
    
    if len(sys.argv) != 2:
        print("Usage: ", pg_name)
        print("Please specify ONE argument")
        sys.exit(1)
    
    fomc = FOMC()
    if args[0].lower() == 'statement':
        df = fomc.get_statements(1990)
        fomc.pickle_dump_df("../data/FOMC/statements.pickle")
        fomc.save_texts("../data/FOMC/statements", "FOMC_Statement_", "statements")
    elif args[0].lower() == 'speech':
        df = fomc.get_speeches(1990)
        fomc.pickle_dump_df("../data/FOMC/speeches.pickle")
        fomc.save_texts("../data/FOMC/speeches", "FOMC_Speech_", "speeches")
