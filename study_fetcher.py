from bs4 import BeautifulSoup
import requests
import csv
import re

#Gambia - Labour Force Survey 2012, with ILO standard variables
gambiaURL = "https://www.ilo.org/surveydata/index.php/catalog/1350"

bangladeshURL= "https://www.ilo.org/surveydata/index.php/catalog/2046"

bangladeshDataDescURL= "https://www.ilo.org/surveydata/index.php/catalog/2046/data_dictionary"

def get_value(cells, label):
    for i in range(0, len(cells)):
        if cells[i].text == label:
            return cells[i + 1].text

def fetch_data_desc(url):
    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")


    cells = soup.find("table", class_="ddi-table data-dictionary").find_all("td")
    datalink = cells[0].find("a").get('href')
    output = {"DataFile": cells[0].text}
    varNum = cells[3].text

    varDoc = requests.get(datalink + "?limit=" + varNum)
    varSoup = BeautifulSoup(varDoc.content, features="lxml")
    matches = varSoup.body.find_all(string=re.compile("(Interviewer|Enumerator)s?"))
    output["InterviewerQuestion"] = True if len(matches) > 0 else output["InterviewerQuestion"] = False


def fetch_study(url):
    output = {}

    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")
    cells = soup.table.find_all("td")

    output["StudyName"] = soup.title.string
    output["ReferenceID"] = get_value(cells, "Reference ID")
    output["Country"] = get_value(cells, "Country")
    output["Year"] = get_value(cells, "Year")
    output["Producer"] = get_value(cells, "Producer(s)")
    output["StudyWebsiteURL"] = soup.find("a", title="Study website (with all available documentation)").get('href')

    questionnaireCells = soup.find("fieldset").find_all("td")

    output["Language"] = get_value(questionnaireCells, "Language")

    # output["InterviewerQuestion"]
    # output["DataFile"]

    print(output)


#fetch_study(bangladeshURL)

fetch_data_desc(bangladeshDataDescURL)
