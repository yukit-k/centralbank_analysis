from __future__ import print_function
from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
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
                 historical_date = 2014,
                 verbose = True,
                 max_threads = 10):

        self.base_url = base_url
        self.calendar_url = calendar_url
        self.df = None
        self.links = None
        self.dates = None
        self.articles = None
        self.verbose = verbose
        self.HISTORICAL_DATE = historical_date
        self.MAX_THREADS = max_threads
    

    def _get_links(self, from_year):
        '''
        private function that sets all the links for the FOMC meetings from the giving from_year
        to the current most recent year
        '''
        if self.verbose:
            print("Getting links...")
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


    def _date_from_link(self, link):
        date = re.findall('[0-9]{8}', link)[0]
        if date[4] == '0':
            date = "{}/{}/{}".format(date[:4], date[5:6], date[6:])
        else:
            date = "{}/{}/{}".format(date[:4], date[4:6], date[6:])
        return date


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
        statement_socket = urlopen(self.base_url + link)
        statement = BeautifulSoup(statement_socket, 'html.parser')
        paragraphs = statement.findAll('p')
        self.articles[index]= "\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])


    def _get_articles_multi_threaded(self):
        '''
        gets all articles using multi-threading
        '''
        if self.verbose:
            print("Getting articles - Multi-threaded...")

        self.dates, self.articles = [], ['']*len(self.links)
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

        self.df = pd.DataFrame(self.articles, index = pd.to_datetime(self.dates)).sort_index()
        self.df.columns = ['statements']
        return self.df


    def pickle_dump_df(self, filename="../data/FOMC/statements.pickle"):
        if filename:
            if self.verbose:
                print("Writing to", filename)
            with open(filename, "wb") as output_file:
                    pickle.dump(self.df, output_file)

    def save_texts(self, directory="../data/FOMC/statements"):
        if directory:
            if self.verbose:
                print("Writing to", directory)
            for i in range(self.df.shape[0]):
                filename = directory + '/' + "FOMC_Statement_" + self.df.index.strftime('%Y-%m-%d')[i] + ".txt"
                with open(filename, "w") as output_file:
                    output_file.write(self.df.iloc[i]["statements"])

if __name__ == '__main__':
    #Example Usage
    fomc = FOMC()
    df = fomc.get_statements()
    fomc.pickle_dump_df()
    fomc.save_texts()