from utility import get_soup
import requests
from bs4 import BeautifulSoup

botswanaURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/635"
kenyaURL = "https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/721"
kenyaAuthUrl = "https://www.datafirst.uct.ac.za/dataportal/index.php/auth/login/?destination=catalog/721/get_microdata"
kenyaMicroDataUrl = 'https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/721/get_microdata';

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

    getMicroData(url)

    if dfCreatedOn == createdOn and dfYear == year and dfCountry == country: return True

def getMicroData(url):
    """Downloads the microdata from a given DataFirst soup object"""

    dataURL = url + "/get_microdata"

    soup = get_soup(dataURL)
    remote = soup.find("div", class_="remote-access-link")
    if remote is not None:
        print(remote.find("a").get("href"))
    else:
        return None

        # Log in to website
            # make POST request to DF
            # set env variables w username/password
            # Status Code 302 - log in ?
            # name:
            # no form data?
        # fill out questions
        # download data
        # Form Data
        # email: haydenudelson2020@u.northwestern.edu
        # password: UNENCRYPTED lol
        # submit: Login

def authScraper(url):
    loginData = {
        "email": "haydenudelson2020@u.northwestern.edu",
        "password": "",
        "submit": "Login"
    }

    session_requests = requests.session()
    session_requests.post(url, data=loginData, headers=dict(referer=url))
    resp = session_requests.get(kenyaMicroDataUrl)
    soup = BeautifulSoup(resp.content, features="xml")

    print(soup.prettify())


    # get auth cookie from POST request then make a second GET request to DF to get access



#matchSurvey("Nov 16, 2017", "2020", "Botswana", kenyaURL)
authScraper(kenyaAuthUrl)