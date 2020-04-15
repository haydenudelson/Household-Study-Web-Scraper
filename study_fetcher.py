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

ILOLaborForceSurveys = "https://www.ilo.org/surveyLib/index.php/catalog?sort_by=rank&sort_order=desc&sk=#_r=&collection=LFS&country=&dtype=&from=1975&page=1&ps=&sid=&sk=&sort_by=rank&sort_order=desc&to=2018&topic=&view=s&vk="

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

# fetches data for a given study and downloads questionnaire
def get_study_data(url):
    output = {}

    doc = requests.get(url)
    soup = BeautifulSoup(doc.content, features="lxml")

    output["StudyName"] = soup.find("h1").text
    output["ReferenceID"] = soup.find("div", class_="field field-idno").find("span").text
    output["Country"] = soup.find("span", class_="dataset-country").text
    output["Year"] = soup.find("span", class_="dataset-year").text
    output["Producer"] = soup.find("span", class_="producers mb-3").text
    output["StudyWebsiteURL"] = soup.find("a", title="Study website (with all available documentation)").get('href')
    # output["Language"] = soup.find("div", class_="dataset-language").text

# writes data to a csv file
def write_csv(dict):
    file = open('metadata.csv','wb')
    w = csv.DictWriter(file, dict.keys())
    w.writeheader()
    w.writerow(dict)

# Format of URL's:
# https://www.ilo.org/surveyLib/index.php/catalog/ + number 868 - 1423
# includes surveys other than just Labor Force Surveys

def iterate_studies():
    for i in range(868, 1424):
        url = "https://www.ilo.org/surveyLib/index.php/catalog/" + str(i)
        doc = requests.get(url)
        print(i)
        print(doc.status_code)
        if doc.status_code != 200:
            print("failure")
            continue
        else:
            soup = BeautifulSoup(doc.content, features="lxml")
            get_study_data(soup)


iterate_studies()
