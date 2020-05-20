import requests
from bs4 import BeautifulSoup
import src.constant as constant
import os
import sys
import src.links as links
from src.StudyFetcher import StudyFetcher

class DataFirstFetcher(StudyFetcher):

    auth_url = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login"
    public_access_url = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=1&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk="

    def __init__(self):
        """ Constructor for DataFirst class """
        super(DataFirstFetcher, self).__init__()
        self.domain = "DataFirst"
        self.set_domain_path()

    def get_datafiles(self, url, survey_path):
        """Downloads the microdata from a given DataFirst soup object"""
        data_url = url + "/get_microdata"

        soup = self.get_soup(data_url)
        remote = soup.find("div", class_="remote-access-link")
        if remote is not None:
            return remote.find("a").get("href")
        else:
            return self.request_data(data_url, survey_path)

    def get_questionnaire(self, url, survey_path):
        soup = self.get_soup(url)
        for legend in soup.find_all("legend"):
            if "Questionnaire" not in legend.text: continue
            else:
                link = legend.parent.find("a", class_="download")
                file = requests.get(link.get("href"), allow_redirects=True)
                open(survey_path + "/" + link.get("title"), 'wb').write(file.content)
                return link.get("title")
        return ""

    def get_study_data(self, soup, url):

        ret = {
            "Domain": self.domain,
            "URL": url,
            "StudyName": soup.find('title').text,
        }

        table = soup.find("table", class_="grid-table survey-info")

        ret["ReferenceID"] = self.get_table_value_from_key(table, "Reference ID")
        ret["Country"] = self.get_table_value_from_key(table, "Country")
        ret["Year"] = self.get_table_value_from_key(table, "Year").strip()
        ret["Producer"] = self.get_table_value_from_key(table, "Producer(s)").strip()
        ret["StudyWebsiteURL"] = ""

        survey_path = os.path.join(self.domain_path, ret["ReferenceID"])
        if not os.path.exists(survey_path):
            os.makedirs(survey_path)

        ret["DataFile"] = self.get_datafiles(url, survey_path)
        ret["Questionnaire"] = self.get_questionnaire(url, survey_path)
        ret["InterviewerVariable"] = ""

        self.write_csv(ret)
        print(ret)

        return ret

    def iterate_studies(self, min, max):
        urls = ["https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=1&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=2&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=3&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk=",
                "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog#_r=&collection=&country=&dtype=2&from=1947&page=4&ps=&sk=&sort_by=nation&sort_order=&to=2019&topic=&view=s&vk="]

        self.authenticate()

        for url in urls:
            soup = self.get_soup(url)
            surveys = soup.find_all("h2", class_="title")
            for survey in surveys:
                link = survey.find("a")
                print(link.get("title"))
                try:
                    self.access_study(link.get("href"))
                except:
                    error = "Error: " + sys.exc_info()[0]
                    print(error)

        self.session.close()

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

    def request_data(self, url, survey_path):
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
        if '.dta' in combined_titles:
            for file in files_dict:
                if '.dta' in file:
                    r = requests.get(files_dict[file], allow_redirects=True)
                    with open(survey_path + "/" + file, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=128):
                            fd.write(chunk)
                    return file
                else: continue

        elif '.csv' in combined_titles:
            for file in files_dict:
                if '.csv' in file:
                    r = requests.get(files_dict[file], allow_redirects=True)
                    with open(survey_path + "/" + file, 'wb') as fd:
                        for chunk in r.iter_content(chunk_size=128):
                            fd.write(chunk)
                    return file
                else: continue
        else:
            for file in files_dict:
                r = requests.get(files_dict[file], allow_redirects=True)
                with open(survey_path + "/" + file, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)
                return file


fetcher = DataFirstFetcher()
fetcher.iterate_studies(0, 100)