from bs4 import BeautifulSoup
import requests
import csv
import re
import os
from utility import clean_text, get_soup
import constant
import datetime

def get_year(txt):
    if txt[len(txt) - 6] == "-":
        res = txt[len(txt) - 11 : len(txt)]
    else:
        res = txt[len(txt) - 4: len(txt)]
    return res

# writes data to a csv file
def write_csv(dict):
    with open('metadata.csv', 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=dict.keys())
        writer.writerow(dict)

# determines if any variables contain the keywords interviewer/enumerator
def has_interviewer_question(url):
    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")
    matches = soup.body.find_all(string=re.compile("((I|i)nterviewer|(E|e)numerator)s?"))
    return True if len(matches) > 0 else False

def grab_datafile(url):
    doc = requests.get(url + "/data-dictionary")
    soup = BeautifulSoup(doc.content, features="lxml")

    datafiles = soup.find("table").find_all("a")
    res = []
    hasIntQ = False

    for f in datafiles:
        if not hasIntQ:
            hasIntQ = has_interviewer_question(f.get("href"))
        res.append(f.text)

    return res, hasIntQ

# finds and downloads the questionnaire
def download_questionnaire(url, refID, docsPath):
    doc = requests.get(url + "/related-materials")
    soup = BeautifulSoup(doc.content, features="xml")

    links = soup.find("fieldset").find_all("a")

    refFolder = os.path.join(docsPath, refID)

    if not os.path.exists(refFolder):
        os.makedirs(refFolder)

    for link in links:
        file = requests.get(link.get("href"), allow_redirects=True)
        open(refFolder + "/" + link.get("title"), 'wb').write(file.content)


# fetches data for a given study and downloads questionnaire
def get_study_data(soup, url, docsPath):
    output = {}

    output["URL"] = url
    output["StudyName"] = soup.find("h1").text
    output["ReferenceID"] = soup.find("div", class_="field field-idno").find("span").text
    output["Country"] = clean_text(soup.find("table",
                                             class_="table table-bordered table-striped table-condensed xsl-table table-grid")
                                   .find("td").text)
    output["Year"] = get_year(output["StudyName"])
    output["Producer"] = clean_text(soup.find("div", class_="producers mb-3").text)

    StudyWebsiteURL = soup.find("a", title="Study website (with all available documentation)")
    output["StudyWebsiteURL"] = StudyWebsiteURL.get('href') if StudyWebsiteURL is not None else ""
    # pull interviewer question variable name
    output["DataFile"], output["InterviewerVariable"] = grab_datafile(url)
    # get language from questionnaire info


    download_questionnaire(url, output["ReferenceID"], docsPath)
    print(type(output))
    print(output)
    write_csv(output)

# Format of URL's:
# https://www.ilo.org/surveyLib/index.php/catalog/ + number 868 - 1423
# includes surveys other than just Labor Force Surveys

#1920, 1620
def iterate_studies():

    currDir = os.getcwd()
    docsPath = os.path.join(currDir, "docs")
    if not os.path.exists(docsPath):
        os.makedirs(docsPath)

    with open('metadata.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=constant.HEADERS)
        writer.writeheader()

    reportHeader = 'Run Report + ' + datetime.datetime.now()
    with open('runReport.txt', 'w') as report:
        report.write(reportHeader)
        report.close()

    numHits = 0

    for i in range(constant.MIN_INDEX, constant.MAX_INDEX):
        url = "https://www.ilo.org/surveyLib/index.php/catalog/" + str(i)
        doc = requests.get(url)
        if doc.status_code != 200:
            with open('runReport.txt', 'a') as report:
                report.write('\n')
                report.write(doc.status_code + " error for index " + i)
            continue
        else:
            soup = BeautifulSoup(doc.content, features="lxml")
            get_study_data(soup, url, docsPath)
            ++numHits

    with open('runReport.txt', 'a') as report:
        report.write("Number of Hits: " + numHits + '\n')
        numRequests = constant.MAX_INDEX - constant.MIN_INDEX
        report.write("Number of Requests: " + numRequests + '\n')
        report.write("Hit Rate: " + (numHits / numRequests))

