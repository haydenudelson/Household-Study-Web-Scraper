# Standard Library
import re
import sys

#Third Party
import requests

#Local Imports
from src.StudyFetcher import StudyFetcher

class ILOFetcher(StudyFetcher):

    def __init__(self):
        """ Constructor for DataFirst class """
        super(ILOFetcher, self).__init__()
        self.domain = "ILO"
        self.set_domain_path()

    def get_datafiles(self, url, survey_path):
        """ Downloads datafiles for a given survey and calls get_interviewer_variable for each datafile """
        soup = self.get_soup(url + "/data-dictionary")
        datafiles = soup.find("ul", class_="nada-list-group").find_all("a")
        res = []
        int_var = []

        for f in datafiles:
            int_var.append(self.get_interviewer_variable(f.get("href")))
            res.append(f.text.strip())

        return res, int_var

    def get_questionnaire(self, url, reference_id):
        """ Downloads questionnaires for a given survey """
        soup = self.get_soup(url + "/related-materials")
        links = soup.find("fieldset").find_all("a", {"target": "_blank"})
        questionnaires = []

        if len(links) > 0:
            survey_path = self.set_survey_path(reference_id)
            for link in links:
                file = requests.get(link.get("href"), allow_redirects=True)
                title = link.get("title")
                open(survey_path + "/" + title, 'wb').write(file.content)
                questionnaires.append(title)

        return questionnaires

    def get_study_data(self, soup, url):
        """ Pulls survey metadata and returns dict """
        ret = {"Domain": self.domain,
               "URL": url,
               "StudyName": soup.find("h1").text,
               "ReferenceID": soup.find("div", class_="field field-idno").find("span").text,
               "Country": soup.find("table",
                                    class_="table table-bordered table-striped table-condensed xsl-table table-grid") \
                   .find("td").text.strip()
               }

        year = self.parse_year(soup.find("span", {"id": "dataset-year"}).text)
        ret["StartYear"] = year[0]
        ret["EndYear"] = year[1]
        ret["Producer"] = soup.find("div", class_="producers mb-3").text.strip()
        # Study website URL not available for all surveys
        study_website_url = soup.find("a", title="Study website (with all available documentation)")
        ret["StudyWebsiteURL"] = study_website_url.get('href') if study_website_url is not None else ""
        ret["DataFile"], int_var = self.get_datafiles(url, ret["ReferenceID"])
        ret["Questionnaire"] = self.get_questionnaire(url, ret["ReferenceID"])
        ret["InterviewerVariable"] = int_var
        self.write_csv(ret)
        return ret

    def iterate_studies(self, start, end):
        """ Iterates through all studies within a given range on a class's domain """
        for i in range(start, end):
            url = "https://www.ilo.org/surveyLib/index.php/catalog/" + str(i)
            try:
                self.access_study(url)
            except Exception:
                print("Error: ", sys.exc_info())
                self.add_error(str(i), str(sys.exc_info()))
                self.num_errors += 1
        self.write_error_report()

    # Domain-Specific Functions

    def get_interviewer_variable(self, url):
        """ Checks if any variables or their descriptions contain Interviewer/Enumerator keywords """
        soup = self.get_soup(url)
        rows = list(map(lambda x: [x.find("div", class_="var-td p-1").text.strip(),
                                   x.find("div", class_="p-1").text.strip()],
                        soup.find_all("div", class_="row var-row ")))
        reg_ex = re.compile("((I|i)nterviewer|(E|e)numerator)s?")
        return [row for row in rows if reg_ex.search(row[0]) is not None or reg_ex.search(row[1]) is not None]

