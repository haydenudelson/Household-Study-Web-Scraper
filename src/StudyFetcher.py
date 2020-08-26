# Standard Library
from abc import ABC, abstractmethod
from datetime import datetime
import csv
import re
import os

# Third Party Imports
from bs4 import BeautifulSoup
import requests

# Local Imports
import src.constant as constant


class StudyFetcher(ABC):
    """ Abstract class for fetching data for studies from a given domain

        Attributes

            num_hits : int
                Number of studies accessed that return 200 status code
            num_requests : int
                Number of requests that were made to access studies
            num_errors : int
                Number of studies that returned an error while being scraped
            num_datafiles : int
                Number of datafiles downloaded during a pull
            domain : str
                Domain (name of data catalog) on which studies hosted
            docs_path : path
                Path to docs folder
            domain_path : path
                Path to domain folder
            session : requests.Session
                Current Session for data requests

        Methods

            get_table_value_from_key(table, key)
                For JSOUP table object, returns value in cell adjacent to cell with key
            parse_year(txt)
                Returns start and end year for given year range string
            write_csv(dictionary)
                Appends data as row to metadata csv file

            access_study(url)
                Attempts to access study URL, if successful calls get_study_data else writes to run report
            add_error(reference_id, error)
                Appends given error to run report
            get_soup(url)
                Returns Beautiful Soup object for given url
            set_domain_path()
                Creates directory for domain in docs folder if none exists
            set_survey_path(reference_id)
                Creates directory for given reference ID in domain folder, if none exists, returns path
            write_error_report()
                At end of run, fills run report with information about run using class attributes

            get_datafiles(url, survey_path)
                Downloads datafiles for a given survey
            get_questionnaire(url, survey_path)
                Downloads questionnaires for a given survey
            get_study_data(soup, url)
                Retrieves necessary data from a given study and records it in metadata.csv
            iterate_studies(start, end)
                Iterates through all studies within a given range on a class's domain

    """

    # CONSTRUCTOR

    def __init__(self):
        """ Constructs StudyFetcher class, creates metadata and run report file, creates docs folder """
        self.num_errors = 0
        self.num_datafiles = 0
        self.num_hits = 0
        self.num_requests = 0
        self.domain = None
        self.domain_path = None
        self.session = None

        self.docs_path = os.path.join(os.getcwd(), "docs")
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)

        metadata_path = os.path.join(os.getcwd(), constant.METADATA_FILE)
        if not os.path.exists(metadata_path):
            with open(constant.METADATA_FILE, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=constant.HEADERS)
                writer.writeheader()

        now = datetime.now()
        dt_string = now.strftime("%H:%M %m/%d/%Y")

        report_header = 'Run Report ' + dt_string
        runreport_path = os.path.join(os.getcwd(), constant.RUN_REPORT)
        if not os.path.exists(runreport_path):
            with open(constant.RUN_REPORT, 'w') as report:
                report.write(report_header)
                report.close()
        else:
            with open(constant.RUN_REPORT, 'a') as report:
                report.write(report_header)
                report.close()

    # STATIC METHODS

    @staticmethod
    def get_table_value_from_key(table, key):
        """ For a JSOUP table object, returns value in cell adjacent to cell with key"""

        return_cell = False
        for cell in table.find_all("td"):
            if return_cell:
                return cell.text
            elif cell.text == key:
                return_cell = True

    @staticmethod
    def parse_year(txt):
        """ Returns start and end year for given year range string """

        txt = txt.strip()
        if "-" in txt:
            res = re.sub('[^0-9]', '', txt)
            return [res[0:4], res[4:8]]
        else:
            return [txt, txt]

    @staticmethod
    def write_csv(dictionary):
        """ Appends data as row to metadata csv file """

        with open(constant.METADATA_FILE, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=dictionary.keys())
            try:
                writer.writerow(dictionary)
            except Exception:
                writeable = {k: str(v).encode("utf-8") for k, v in dictionary.items()}
                writer.writerow(writeable)

    # UTILITY METHODS

    def access_study(self, url):
        """ Attempts to access study URL, if successful calls get_study_data else writes to run report """

        doc = requests.get(url)
        self.num_requests += 1
        if doc.status_code != 200:
            with open('runReport.txt', 'a') as report:
                report.write('\n')
                report.write(str(doc.status_code) + " for " + url)
            return None
        else:
            soup = BeautifulSoup(doc.content, features="lxml")
            self.num_hits += 1
            return self.get_study_data(soup, url)

    def add_error(self, reference_id, error):
        """ Appends given error to run report """

        with open('runReport.txt', 'a') as report:
            try:
                report.write("\nError: " + self.domain + " " + reference_id + ": " + error)
            except Exception:
                report.write("\nError: " + self.domain + " " + reference_id)

    def get_soup(self, url):
        """ Returns BeautifulSoup object for a given URL """
        if self.session is None:
            return BeautifulSoup(requests.get(url).content, features="xml")
        else:
            return BeautifulSoup(self.session.get(url).content, features="xml")

    def set_domain_path(self):
        """ Creates directory for domain in docs folder if none exists """

        self.domain_path = os.path.join(self.docs_path, self.domain)
        if not os.path.exists(self.domain_path):
            os.makedirs(self.domain_path)

    def set_survey_path(self, reference_id):
        """ Creates directory for given reference ID in domain folder, if none exists, returns path """

        survey_path = os.path.join(self.domain_path, reference_id)
        if not os.path.exists(survey_path):
            os.makedirs(survey_path)
        return survey_path

    def write_error_report(self):
        """ At end of run, fills run report with information about run using class attributes """

        with open('runReport.txt', 'a') as report:
            report.write("Number of Hits: " + str(self.num_hits) + '\n')
            report.write("Number of Requests: " + str(self.num_requests) + '\n')
            report.write("Hit Rate: " + str((self.num_hits / self.num_requests)))
            report.write("Datafiles downloaded: " + str(self.num_datafiles))
            now = datetime.now()
            dt_string = now.strftime("%H:%M %m/%d/%Y")
            report.write("Run finished " + dt_string)

    # ABSTRACT METHODS

    @abstractmethod
    def get_datafiles(self, url, survey_path):
        """ Downloads datafiles for a given survey """
        pass

    @abstractmethod
    def get_questionnaire(self, url, survey_path):
        """ Downloads questionnaires for a given survey """
        pass

    @abstractmethod
    def get_study_data(self, soup, url):
        """ Retrieves necessary data from a given study and records it in metadata.csv """
        pass

    @abstractmethod
    def iterate_studies(self, start, end):
        """ Iterates through all studies within a given range on a class's domain """
        pass
