# Standard Library
from abc import ABC, abstractmethod
from datetime import datetime
import requests
import csv
import re
import os

# Third Party Imports
from bs4 import BeautifulSoup

# Local Imports
import src.constant as constant

class StudyFetcher(ABC):
    """ Abstract class for fetching data for studies hosted on a generic domain
        Instance Variables:
            docs_path
            domain_path
    """

# CONSTRUCTOR

    def __init__(self):
        """ Constructor for StudyFetcher class """
        self.num_hits = 0
        self.num_requests = 0

        self.docs_path = os.path.join(os.getcwd(), "docs")
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)

        self.domain_path = None

        with open(constant.METADATA_FILE, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=constant.HEADERS)
            writer.writeheader()

        now = datetime.now()
        dt_string = now.strftime("%H:%M %m/%d/%Y")

        report_header = 'Run Report ' + dt_string
        with open(constant.RUN_REPORT, 'w') as report:
            report.write(report_header)
            report.close()

# UTILITY METHODS

    @staticmethod
    def get_soup(url):
        """ Returns BeautifulSoup object for a given URL """
        return BeautifulSoup(requests.get(url).content, features="xml")

    @staticmethod
    def get_table_value_from_key(table, key):
        """ For a JSOUP table object, returns value in cell adjacent to cell with key"""
        return_cell = False

        for cell in table.find_all("td"):
            if return_cell:
                return cell.text
            elif cell.text == key:
                return_cell = True

    def set_domain_path(self):
        self.domain_path = os.path.join(self.docs_path, self.domain)
        if not os.path.exists(self.domain_path):
            os.makedirs(self.domain_path)

    @staticmethod
    def get_year(txt):
        """ Isolates last year from range of years in string """
        if txt[len(txt) - 6] == "-":
            res = txt[len(txt) - 11: len(txt)]
        else:
            res = txt[len(txt) - 4: len(txt)]
        return res

    # DATA PARSING METHODS

    def access_study(self, url):
        """ Attempts to access URL, returns True if successful and calls get_study_data & returns False otherwise """
        doc = requests.get(url)
        ++self.num_requests

        if doc.status_code != 200:
            with open('runReport.txt', 'a') as report:
                report.write('\n')
                report.write(doc.status_code + " for " + url)

            ++self.num_hits
            return None
        else:
            soup = BeautifulSoup(doc.content, features="lxml")
            return self.get_study_data(soup, url)

    @staticmethod
    def write_csv(dictionary):
        """ Writes relevant data to 'metadata.csv' """
        with open(constant.METADATA_FILE, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=dictionary.keys())
            writer.writerow(dictionary)

    def write_error_report(self):
        """ Fills error report with information about run on study """
        with open('runReport.txt', 'a') as report:
            report.write("Number of Hits: " + self.num_hits + '\n')
            report.write("Number of Requests: " + self.num_requests + '\n')
            report.write("Hit Rate: " + (self.num_hits / self.num_requests))

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
    def iterate_studies(self, min, max):
        """ Iterates through all studies within a given range on a class's domain
            Should call writer_error_report
        """
        pass