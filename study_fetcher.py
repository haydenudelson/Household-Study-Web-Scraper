from bs4 import BeautifulSoup
import requests
import csv
import re

#Gambia - Labour Force Survey 2012, with ILO standard variables
gambiaURL = "https://www.ilo.org/surveydata/index.php/catalog/1350"

bangladeshURL= "https://www.ilo.org/surveydata/index.php/catalog/2046"

bangladeshDataDescURL= "https://www.ilo.org/surveydata/index.php/catalog/2046/data_dictionary"

newURL = "https://www.ilo.org/surveyLib/index.php/catalog/2595/"

newURLDataDesc = "https://www.ilo.org/surveyLib/index.php/catalog/2595/data-dictionary"

def get_value(cells, label):
    for i in range(0, len(cells)):
        if cells[i].text == label:
            return cells[i + 1].text

def fetch_data_desc(url):
    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")

    print(soup.find("table", class_="ddi-table data-dictionary"))

    cells = soup.find("table", class_="ddi-table data-dictionary").find_all("td")
    datalink = cells[0].find("a").get('href')
    output = {"DataFile": cells[0].text}
    varNum = cells[3].text

    varDoc = requests.get(datalink + "?limit=" + varNum)
    varSoup = BeautifulSoup(varDoc.content, features="lxml")
    matches = varSoup.body.find_all(string=re.compile("(Interviewer|Enumerator)s?"))
    if len(matches) > 0:
        output["InterviewerQuestion"] = True
    else:
        output["InterviewerQuestion"] = False

    #output["InterviewerQuestion"] = True if len(matches) > 0 else output["InterviewerQuestion"] = False


def fetch_study(url):
    output = {}

    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")
    #cells = soup.table.find_all("td")

    output["StudyName"] = soup.find("h1").text
    output["ReferenceID"] = soup.find("div", class_="field field-idno").find("span").text
    output["Country"] = soup.find("span", class_="dataset-country").text
    output["Year"] = soup.find("span", class_="dataset-year").text
    output["Producer"] = soup.find("span", class_="producers mb-3").text
    output["StudyWebsiteURL"] = soup.find("a", title="Study website (with all available documentation)").get('href')
    output["Language"] = 

def write_csv(dict):
    file = open('metadata.csv','wb')
    w = csv.DictWriter(f, dict.keys())
    w.writeheader()
    w.writerow(dict)


fetch_study(newURL)

#fetch_data_desc(newURLDataDesc)
