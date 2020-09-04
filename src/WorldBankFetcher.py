from enum import Enum
import os
import re
import sys
import time

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver

from src.StudyFetcher import StudyFetcher
import src.constant as constant

class DataFileType(Enum):
    OPEN = 0
    DIRECT = 1
    PUBLIC_USE = 2

class WorldBankFetcher(StudyFetcher):

    def __init__(self):
        """ Constructor for DataFirst class """
        super(WorldBankFetcher, self).__init__()
        self.domain = "WorldBank"
        self.session = None
        self.set_domain_path()

    def get_datafiles(self, url, survey_path):
        soup = self.get_soup(url + "/data-dictionary")
        datafiles = soup.find("ul", class_="nada-list-group").find_all("a")
        res = []
        int_var = []

        for f in datafiles:
            int_var += self.get_interviewer_variable(f.get('href'))
            res.append(f.text.strip())

        return int_var

    def get_questionnaire(self, url, reference_id):
        req = self.session.get(url + "/related-materials")
        soup = BeautifulSoup(req.content, features="xml")
        links = soup.find("fieldset").find_all("a", {"target": "_blank"})
        questionnaires = []
        if len(links) > 0:
            survey_path = self.set_survey_path(reference_id)
            for link in links:
                file = self.session.get(link.get("href"), allow_redirects=True)
                title = link.get("title")
                open(survey_path + "/" + title, 'wb').write(file.content)
                questionnaires.append(title)

        return questionnaires

    def get_study_data(self, soup, url):
        ret = {"Domain": self.domain,
               "URL": url,
               "StudyName": soup.find("h1").text,
               "ReferenceID": soup.find("div", class_="field field-idno").find("span").text,
               "Country": soup.find("span", {'id': 'dataset-country'}).text.strip()
               }

        year = self.parse_year(soup.find("span", {"id": "dataset-year"}).text)
        ret["StartYear"] = year[0]
        ret["EndYear"] = year[1]
        ret["Producer"] = soup.find("div", class_="producers mb-3").text.strip()

        study_url = soup.find("a", title="Study website (with all available documentation)")
        ret["StudyWebsiteURL"] = study_url.get('href') if study_url is not None else ""
        ret["DataFile"] = self.download_datafiles(url, ret["StudyName"], ret["ReferenceID"])
        try:
            if ret["DataFile"] is not None: self.num_datafiles += 1
        except requests.exceptions.ConnectionError:
            self.add_error(url, str(sys.exc_info()))
            self.num_errors += 1
        ret["Questionnaire"] = self.get_questionnaire(url, ret["ReferenceID"])
        ret["InterviewerVariable"] = self.get_datafiles(url, ret["ReferenceID"])
        self.write_csv(ret)
        return ret

    def iterate_studies(self, start, end):
        driver = webdriver.Firefox()
        catalog_page_start = "https://microdata.worldbank.org/index.php/catalog#_r=&collection=&country=&dtype=1,2&from=1890&page="
        catalog_page_end = "&ps=100&sid=&sk=&sort_by=nation&sort_order=&to=2020&topic=&view=s&vk="
        links = []

        for i in range(1, 14):
            url = catalog_page_start + str(i) + catalog_page_end
            driver.get(url)
            time.sleep(5)
            results = driver.find_elements_by_tag_name("h5")
            for result in results:
                link = result.find_element_by_tag_name("a")
                page_link = link.get_attribute('href')
                links.append(page_link)
        driver.quit()

        for link in links:
            try:
                self.access_study(link)
            except Exception:
                print("Error: ", sys.exc_info())
                self.add_error(link, str(sys.exc_info()))
                self.num_errors += 1
        self.write_error_report()


    # Domain-Specific Functions


    def get_interviewer_variable(self, url):
        """ Determines if any variables contain the keywords interviewer/enumerator """
        soup = self.get_soup(url)
        rows = list(map(lambda x: [x.find("div", class_="var-td p-1").text.strip(),
                                   x.find("div", class_="p-1").text.strip()],
                        soup.find_all("div", class_="row var-row ")))
        reg_ex = re.compile("((I|i)nterviewer|(E|e)numerator)s?")
        return [row for row in rows if reg_ex.search(row[0]) is not None or reg_ex.search(row[1]) is not None]

    def authenticate(self):
        """ Log in to WorldBank website """
        auth_url = "https://microdata.worldbank.org/index.php/auth/login"
        form_data = {
            "email": os.getenv("DATAFIRST_USERNAME"),
            "password": os.getenv("DATAFIRST_PASSWORD")",
            "submit": "Login"
        }

        self.session = requests.Session()
        retry = Retry(total=5, backoff_factor=4)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.session.post(auth_url, data=form_data, headers=dict(referer=auth_url))


    def download_datafiles(self, url, title, reference_id):
        """ Download all documentation for a given study """
        micro_url = url + "/get-microdata"
        resp = self.session.get(micro_url)
        soup = BeautifulSoup(resp.content, features="xml")
        forms = soup.find_all("h1")
        form_title = ""
        for i in range(0, len(forms)): form_title += forms[i].text
        if form_title is None:
            None
        elif "Application for Access to a Public Use Dataset" in form_title:
            length = len(url)
            ind = url.index("catalog/") + 8
            survey_id = url[ind: length]
            form_data = {
                "surveytitle": title,
                "surveyid": survey_id,
                "id": "",
                "abstract": constant.STUDY_ABSTRACT,
                "chk_agree": "on",
                "submit": "Submit"
            }
            self.session.post(micro_url, data=form_data, headers=dict(referer=url))
            resp = self.session.get(micro_url)
        elif "Terms and conditions" in form_title:
            form_data = {
                "accept": "Accept"
            }

            resp = self.session.post(micro_url, data=form_data, headers=dict(referer=url))


        soup = BeautifulSoup(resp.content, features="xml")
        data_files = soup.find("div", class_="resources data-files").find_all("a")
        files_dict = {}
        for file in data_files:
            files_dict[file.get("title")] = file.get('href')

        combined_titles = '\t'.join(files_dict.keys())
        if len(files_dict) > 0:
            survey_path = self.set_survey_path(reference_id)
        else:
            return ""

        if 'stata' in combined_titles.lower():
            for file in files_dict:
                if 'stata' in file.lower():
                    self.zip_download(files_dict[file], file, survey_path)
                    return file
                else:
                    continue
        elif 'csv' in combined_titles.lower():
            for file in files_dict:
                if 'csv' in file.lower():
                    self.zip_download(files_dict[file], file, survey_path)
                    return file
                else:
                    continue
        else:
            return ""

    def zip_download(self, url, name, path):
        """ Download zip file """
        self.num_datafiles += 1
        r = self.session.get(url)
        with open(path + "/" + name, 'wb') as fd:
            fd.write(r.content)