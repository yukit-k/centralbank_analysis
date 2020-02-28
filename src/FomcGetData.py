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
from tika import parser
import requests

class FOMC (object):
    '''
    A convenient class for extracting documents from the FOMC website
    Example Usage:  
        fomc_chair = FOMCChair()
        df = fomc.get_statements()
        fomc.pickle("./df_minutes.pickle")
    '''

    def __init__(self,
                 content_type = 'statement',
                 verbose = True,
                 max_threads = 10,
                 base_dir = '../data/FOMC/'):

        self.df = None
        self.links = None
        self.dates = None
        self.articles = None
        self.speaker = None
        self.title = None

        self.content_type = content_type
        self.verbose = verbose
        self.MAX_THREADS = max_threads
        self.base_dir = base_dir

        self.base_url = 'https://www.federalreserve.gov'
        self.calendar_url = 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
        self.speech_base_url = 'https://www.federalreserve.gov/newsevents/speech'

        self.chair = pd.DataFrame(
            data=[["Greenspan", "Alan", "1987-08-11", "2006-01-31"], 
                  ["Bernanke", "Ben", "2006-02-01", "2014-01-31"], 
                  ["Yellen", "Janet", "2014-02-03", "2018-02-03"],
                  ["Powell", "Jerome", "2018-02-05", "2022-02-05"]],
            columns=["Surname", "FirstName", "FromDate", "ToDate"])
        
    def _date_from_link(self, link):
        #print(link)
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

    def _get_links(self, from_year):
        '''
        private function that sets all the links for the FOMC meetings
         from the giving from_year to the current most recent year
         from_year is min(2015, from_year)

        '''
        self.links = []
        self.title = []
        self.speaker = []

        fomc_meetings_socket = urlopen(self.calendar_url)
        soup = BeautifulSoup(fomc_meetings_socket, 'html.parser')
        
        # Differentiate the process for Speech from the others
        if self.content_type in ('statement', 'minutes', 'script', 'meeting_script'):
            # Getting links from current page. Meetin scripts are not available.
            if self.content_type in ('statement', 'minutes'):
                if self.content_type == 'statement':
                    if self.verbose: print("Getting links for statements...")
                    contents = soup.find_all('a', href=re.compile('^/newsevents/pressreleases/monetary\d{8}[ax].htm'))
                else:
                    if self.verbose: print("Getting links for minutes...")
                    contents = soup.find_all('a', href=re.compile('^/monetarypolicy/fomcminutes\d{8}.htm'))
                self.links = [content.attrs['href'] for content in contents]
                self.speaker = [self._speaker_from_date(self._date_from_link(x)) for x in self.links]
                self.title = [self.content_type] * len(self.links)
                if self.verbose: print("{} links found in the current page.".format(len(self.links)))
            elif self.content_type == 'script':
                if self.verbose: print("Getting links for press conference scripts...")
                presconfs = soup.find_all('a', href=re.compile('^/monetarypolicy/fomcpresconf\d{8}.htm'))
                presconf_urls = [self.base_url + presconf.attrs['href'] for presconf in presconfs]
                for presconf_url in presconf_urls:
                    # print(presconf_url)
                    presconf_socket = urlopen(presconf_url)
                    soup_presconf = BeautifulSoup(presconf_socket, 'html.parser')
                    contents = soup_presconf.find_all('a', href=re.compile('^/mediacenter/files/FOMCpresconf\d{8}.pdf'))
                    for content in contents:
                        #print(content)
                        self.links.append(content.attrs['href'])
                        self.speaker.append(self._speaker_from_date(self._date_from_link(content.attrs['href'])))
                        self.title.append('Press Conference Transcript')
            if self.verbose: print("{} links found in current page.".format(len(self.links)))
            # Archived before 2015
            if from_year <= 2014:
                for year in range(from_year, 2015):
                    yearly_contents = []
                    fomc_yearly_url = self.base_url + '/monetarypolicy/fomchistorical' + str(year) + '.htm'
                    fomc_yearly_socket = urlopen(fomc_yearly_url)
                    soup_yearly = BeautifulSoup(fomc_yearly_socket, 'html.parser')
                    if self.content_type in ('statement', 'minutes'):
                        if self.content_type == 'statement':
                            yearly_contents = soup_yearly.findAll('a', text = 'Statement')
                        elif self.content_type == 'minutes':
                            yearly_contents = soup_yearly.find_all('a', href=re.compile('(^/monetarypolicy/fomcminutes|^/fomc/minutes|^/fomc/MINUTES)'))
                        for yearly_content in yearly_contents:
                            self.links.append(yearly_content.attrs['href'])
                            self.speaker.append(self._speaker_from_date(self._date_from_link(yearly_content.attrs['href'])))
                            self.title.append(self.content_type)
                        if self.verbose: print("YEAR: {} - {} links found.".format(year, len(yearly_contents)))
                    elif self.content_type == 'script':
                        if self.verbose: print("Getting links for historical press conference scripts...")
                        presconf_hists = soup_yearly.find_all('a', href=re.compile('^/monetarypolicy/fomcpresconf\d{8}.htm'))
                        presconf_hist_urls = [self.base_url + presconf_hist.attrs['href'] for presconf_hist in presconf_hists]
                        for presconf_hist_url in presconf_hist_urls:
                            #print(presconf_hist_url)
                            presconf_hist_socket = urlopen(presconf_hist_url)
                            soup_presconf_hist = BeautifulSoup(presconf_hist_socket, 'html.parser')
                            yearly_contents = soup_presconf_hist.find_all('a', href=re.compile('^/mediacenter/files/FOMCpresconf\d{8}.pdf'))
                            for yearly_content in yearly_contents:
                                #print(yearly_content)
                                self.links.append(yearly_content.attrs['href'])
                                self.speaker.append(self._speaker_from_date(self._date_from_link(yearly_content.attrs['href'])))
                                self.title.append('Press Conference Transcript')
                        if self.verbose: print("YEAR: {} - {} links found.".format(year, len(presconf_hist_urls)))
                    elif self.content_type == 'meeting_script':
                        meeting_scripts = soup_yearly.find_all('a', href=re.compile('^/monetarypolicy/files/FOMC\d{8}meeting.pdf'))
                        for meeting_script in meeting_scripts:
                            self.links.append(meeting_script.attrs['href'])
                            self.speaker.append(self._speaker_from_date(self._date_from_link(meeting_script.attrs['href'])))
                            self.title.append('Meeting Transcript')
                        if self.verbose: print("YEAR: {} - {} meeting scripts found.".format(year, len(meeting_scripts)))
            print("There are total ", len(self.links), ' links for ', self.content_type)

        # Speech 
        elif self.content_type == 'speech':
            if self.verbose: print("Getting links for speeches...")
            to_year = date.today().strftime("%Y")

            if from_year <= 1995:
                print("Archive only from 1996, so setting from_year as 1996...")
                from_year = 1996

            # Archived between 1996 and 2005, URL changed from 2011

            for year in range(from_year, int(to_year)+1):
                if year < 2011:
                    speech_url = self.speech_base_url + '/' + str(year) + 'speech.htm'
                else:
                    speech_url = self.speech_base_url + '/' + str(year) + '-speeches.htm'

                speech_socket = urlopen(speech_url)
                soup_speech = BeautifulSoup(speech_socket, 'html.parser')
                speech_links = soup_speech.findAll('a', href=re.compile('^/?newsevents/speech/.*{}\d\d\d\d.*.htm|^/boarddocs/speeches/{}/|^{}\d\d\d\d.*.htm'.format(str(year), str(year), str(year))))
                for speech_link in speech_links:
                    self.links.append(speech_link.attrs['href'])
                    self.title.append(speech_link.get_text())
                    # print(speech_url)
                    # print(speech_link.attrs['href'])

                    self.speaker.append(speech_link.parent.next_sibling.next_element.get_text().replace('\n', '').strip())
                if self.verbose: print("YEAR: {} - {} speeches found.".format(year, len(speech_links)))
        else:
            print("Wrong Content Type")

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

        link_url = self.base_url + link
        article_date = self._date_from_link(link)

        #print(link_url)

        # date of the article content
        self.dates.append(article_date)

        # Scripts are provided only in pdf. Save the pdf and pass the content
        if self.content_type in ('script', 'meeting_script'):
            res = requests.get(link_url)
            if self.content_type == 'script':
                pdf_filepath = self.base_dir + 'script_pdf/FOMC_PresConfScript_' + article_date + '.pdf'
            elif self.content_type == 'meeting_script':
                pdf_filepath = self.base_dir + 'script_pdf/FOMC_MeetingScript_' + article_date + '.pdf'
            with open(pdf_filepath, 'wb') as f:
                f.write(res.content)
            pdf_file_parsed = parser.from_file(pdf_filepath)
            paragraphs = re.sub('(\n)(\n)+', '\n', pdf_file_parsed['content'].strip())
            paragraphs = paragraphs.split('\n')

            section = -1
            paragraph_sections = []
            for paragraph in paragraphs:
                if not re.search('^(page|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', paragraph.lower()):
                    if len(re.findall(r'[A-Z]', paragraph[:10])) > 5 and not re.search('(present|frb/us|abs cdo|libor|rp–ioer|lsaps|cusip|nairu|s cpi|clos, r)', paragraph[:10].lower()):
                        section += 1
                        paragraph_sections.append("")
                    if section >= 0:
                        paragraph_sections[section] += paragraph
            self.articles[index] = "\n\n[SECTION]\n\n".join([paragraph for paragraph in paragraph_sections])
        else:
            article_socket = urlopen(self.base_url + link)
            article = BeautifulSoup(article_socket, 'html.parser')
            if str(article).count('</p>') < 5:
                article = BeautifulSoup(str(article).replace('<p>', '</p><p>'), 'html.parser')
            paragraphs = article.findAll('p')
            self.articles[index] = "\n\n[SECTION]\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])

            # self.articles[index]= ""
            # for paragraph in paragraphs:
        #         text = paragraph.get_text().strip()
        #         input_words = re.findall(r'\b([a-zA-Z]+n\'t|[a-zA-Z]+\'s|[a-zA-Z]+)\b', text.lower())
        #         if len(input_words) > 150:
        #             self.articles[index] += "\n\n[SECTION]\n\n" + text
        # else:
        #     article_socket = urlopen(self.base_url + link)
        #     article = BeautifulSoup(article_socket, 'html.parser')
        #     paragraphs = article.findAll('p')
        #     self.articles[index]= "\n\n".join([paragraph.get_text().strip() for paragraph in paragraphs])

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

        #for row in range(len(self.articles)):
        #    self.articles[row] = self.articles[row].strip()

    def get_contents(self, from_year=1990):
        '''
        Returns a Pandas DataFrame with the date as the index
        uses a date range of from_year to the most current
        '''
        self._get_links(from_year)
        self._get_articles_multi_threaded()
        dict = {
            'contents': self.articles,
            'speaker': self.speaker, 
            'title': self.title
        }
        self.df = pd.DataFrame(dict, index=pd.to_datetime(self.dates)).sort_index()
        return self.df

    def pickle_dump_df(self, filename="output.pickle"):
        filepath = self.base_dir + filename
        if self.verbose: print("Writing to ", filepath)
        with open(filepath, "wb") as output_file:
            pickle.dump(self.df, output_file)

    def save_texts(self, prefix="FOMC_", target="contents"):
        for i in range(self.df.shape[0]):
            filepath = self.base_dir + prefix + self.df.index.strftime('%Y-%m-%d')[i] + ".txt"
            if self.verbose: print("Writing to ", filepath)
            with open(filepath, "w") as output_file:
                output_file.write(self.df.iloc[i][target])

if __name__ == '__main__':
    pg_name = sys.argv[0]
    args = sys.argv[1:]
    
    if len(sys.argv) != 2:
        print("Usage: ", pg_name)
        print("Please specify ONE argument from ('statement', 'minutes', 'script', 'meeting_script', 'speech')")
        sys.exit(1)
    if args[0].lower() not in ('statement', 'minutes', 'script', 'meeting_script', 'speech'):
        print("Usage: ", pg_name)
        print("Please specify ONE argument from ('statement', 'minutes', 'script', 'meeting_script', 'speech')")
        sys.exit(1)
    else:
        fomc = FOMC(content_type=args[0])
        df = fomc.get_contents(1990)
        fomc.pickle_dump_df(filename = fomc.content_type + ".pickle")
        fomc.save_texts(prefix = fomc.content_type + "/FOMC_" + fomc.content_type + "_")