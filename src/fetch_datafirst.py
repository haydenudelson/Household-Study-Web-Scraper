from utility import get_soup
import requests
from bs4 import BeautifulSoup
import constant
import os


authenticateURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login"
botswanaURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/635"
kenyaURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/721"
kenyaAuthUrl = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login/?destination=catalog/721/get_microdata"
kenyaMicroDataUrl = 'https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/721/get_microdata';

brazilURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/442"
brazilAuthURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login/?destination=catalog/442/get_microdata"
brazilRequestData = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/442/get_microdata"



def getTableValueFromKey(table, key):
    """ for a JSOUP table object, returns value in cell adjacent to cell w key"""

    returnCell = False

    for cell in table.find_all("td"):
        if returnCell: return cell.text
        elif cell.text == key: returnCell = True

def matchSurvey(createdOn, year, country, url):
    """ Returns true if DataFirst survey matches provided 'created on' date,
        year, and country provided. Returns false otherwise """

    soup = get_soup(url)
    primaryTable = soup.find("table", class_="grid-table survey-info")
    secondaryTable = soup.find("table", class_="grid-table")


    dfCreatedOn = getTableValueFromKey(secondaryTable, "Created on")
    dfYear = getTableValueFromKey(primaryTable, "Year")
    dfCountry = getTableValueFromKey(primaryTable, "Country")

    if dfCreatedOn == createdOn and dfYear == year and dfCountry == country: return True

def getMicroData(url):
    """Downloads the microdata from a given DataFirst soup object"""

    dataURL = url + "/get_microdata"

    soup = get_soup(dataURL)
    remote = soup.find("div", class_="remote-access-link")
    if remote is not None:
        print(remote.find("a").get("href"))
    else:
        requestData(dataURL)

# TO DO- isolate just the .dta data if it exists, otherwise download the first ?
def requestData(url):
    loginData = {
        "email": os.getenv("DATAFIRST_USERNAME"),
        "password": os.getenv("DATAFIRST_PASSWORD"),
        "submit": "Login"
    }

    formData = {
        "surveytitle": "Ageing, Well-being and Development Project 2002-2008",
        "surveyid": 442,
        "id": "",  # this field was empty,
        "abstract": constant.STUDY_ABSTRACT,
        "chk_agree": "on",
        "submit": "Submit"
    }

    session_requests = requests.session()
    session_requests.post(authenticateURL, data=loginData, headers=dict(referer=authenticateURL))
    session_requests.post(url, data=formData, headers=dict(referer=url))
    resp = session_requests.get(url)
    soup = BeautifulSoup(resp.content, features="xml")

    dataFiles = soup.find("div", class_="resources data-files").find_all("a")
    currDir = os.getcwd()
    filePath = os.path.join(currDir, "DataFirst")
    if not os.path.exists(filePath):
        os.mkdir(filePath)


    for file in dataFiles:
        r = requests.get(file.get('href'), allow_redirects=True)
        open(filePath + "/" + file.get("title"), 'wb').write(r.content)

