import os
import sys
import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import src.constant as constant
from src.StudyFetcher import StudyFetcher

class DataFirstFetcher(StudyFetcher):
    """ Class to pull survey data from DataFirst

        Catalog: https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/central

        Methods



    """

    auth_url = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login"

    def __init__(self):
        """ Constructor for DataFirst class """
        super(DataFirstFetcher, self).__init__()
        self.domain = "DataFirst"
        self.set_domain_path()

    def get_datafiles(self, url, reference_id):
        """Downloads the microdata from a given DataFirst soup object"""
        data_url = url + "/get_microdata"

        soup = self.get_soup(data_url)
        remote = soup.find("div", class_="remote-access-link")
        if remote is not None:
            return remote.find("a").get("href")
        else:
            return self.request_data(data_url, reference_id)

    def get_questionnaire(self, url, reference_id):
        soup = self.get_soup(url)

        questionnaires = []

        for legend in soup.find_all("legend"):
            survey_path = self.set_survey_path(reference_id)
            links = legend.parent.find_all("a", class_="download")
            for link in links:
                title = link.get("title")
                file = self.session.get(link.get("href"), allow_redirects=True)
                if "Questionnaire" in legend.text:
                    open(survey_path + "/" + title, 'wb').write(file.content)
                else:
                    other_docs = os.path.join(survey_path, "Other Docs")
                    if not os.path.exists(other_docs):
                        os.makedirs(other_docs)
                    open(other_docs + "/" + title, 'wb').write(file.content)
                questionnaires.append(title)
        return questionnaires

    def get_study_data(self, soup, url):

        ret = {
            "Domain": self.domain,
            "URL": url,
            "StudyName": soup.find('title').text,
        }

        table = soup.find("table", class_="grid-table survey-info")

        ret["ReferenceID"] = self.get_table_value_from_key(table, "Reference ID")
        ret["Country"] = self.get_table_value_from_key(table, "Country")

        year = self.parse_year(self.get_table_value_from_key(table, "Year"))
        ret["StartYear"] = year[0]
        ret["EndYear"] = year[1]

        ret["Producer"] = self.get_table_value_from_key(table, "Producer(s)").strip()
        ret["StudyWebsiteURL"] = ""

        ret["DataFile"] = self.get_datafiles(url, ret["ReferenceID"])
        ret["Questionnaire"] = self.get_questionnaire(url, ret["ReferenceID"])
        ret["InterviewerVariable"] = self.get_interviewer_var(soup)

        self.write_csv(ret)
        print(ret)

        return ret

    def iterate_studies(self, start, end):
        urls = ["https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=1&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=2&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=3&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=4&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk="]

        self.authenticate()
        pagedriver = webdriver.Firefox()
        for url in urls:
            pagedriver.get(url)
            time.sleep(5)
            res = pagedriver.find_element_by_id("surveys")
            surveys = res.find_elements_by_tag_name("h2")
            for survey in surveys:
                link = survey.find_element_by_tag_name("a")
                print(link.get_attribute("title"))
                try:
                    self.access_study(link.get_attribute("href"))
                except:
                    print("Error: ", sys.exc_info())
                    self.add_error(url, str(sys.exc_info()))
                    self.num_errors += 1

        pagedriver.quit()
        self.session.close()
        self.write_error_report()

    # Class-Specific Methods
    # TO DO- isolate just the .dta data if it exists, otherwise download the first ?
    def authenticate(self):
        login_data = {
            "email": os.getenv("DATAFIRST_USERNAME"),
            "password": os.getenv("DATAFIRST_PASSWORD"),
            "submit": "Login"
        }

        session_requests = requests.session()
        session_requests.post(self.auth_url,
                              data=login_data,
                              headers=dict(referer=self.auth_url))
        self.session = session_requests

    def request_data(self, url, reference_id):
        form_data = {
            "surveytitle": "Ageing, Well-being and Development Project 2002-2008",
            "surveyid": 442,
            "id": "",  # this field was empty,
            "abstract": constant.STUDY_ABSTRACT,
            "chk_agree": "on",
            "submit": "Submit"
        }

        self.session.post(url, data=form_data, headers=dict(referer=url))
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.content, features="xml")

        data_files = soup.find("div", class_="resources data-files").find_all("a")

        files_dict = {}

        for file in data_files:
            files_dict[file.get("title")] = file.get('href')

        combined_titles = '\t'.join(files_dict.keys())

        survey_path = ""
        if len(files_dict) > 0: survey_path = self.set_survey_path(reference_id)
        if 'stata' in combined_titles:
            for file in files_dict:
                if 'stata' in file:
                    self.zip_download(files_dict[file], file, survey_path)
                    return file
                else: continue

        else:
            for file in files_dict:
                self.zip_download(files_dict[file], file, survey_path)
                return file

    def zip_download(self, url, name, path):
        r = self.session.get(url)
        print(r.status_code)
        with open(path + "/" + name, 'wb') as fd:
            fd.write(r.content)

    def get_interviewer_var(self, soup):
        tabs = soup.find("ul", attrs={"role": "tablist"})
        tab = tabs.find("a", attrs={"title": "Description of data files and variables"})
        ret = []

        if tab:
            driver = webdriver.Firefox()
            data_desc_soup = BeautifulSoup(self.session.get(tab.get('href')).content, features="xml")
            links = data_desc_soup.find("li", class_="filetree").find_all("a")
            reg_ex = re.compile("((I|i)nterviewer|(E|e)numerator)s?")

            for link in links:
                if "Data Description" in link.text: continue
                print(link)
                driver.get(link.get('href'))
                time.sleep(2)
                rows = list(map(lambda x: [x.find_elements_by_tag_name("td")[0].text.strip(),
                                           x.find_elements_by_tag_name("td")[1].text.strip()],
                                driver.find_elements_by_class_name("row-color1") +
                                driver.find_elements_by_class_name("row-color2")))
                ret += [row for row in rows if reg_ex.search(row[0]) is not None or reg_ex.search(row[1]) is not None]
            driver.quit()
        print(ret)
        return ret


# fetcher = DataFirstFetcher()
# fetcher.iterate_studies(0, 100)

fetcher = DataFirstFetcher()
fetcher.iterate_studies(0, 100)