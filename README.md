# Household Study Web Scraper
#### Developed by Hayden Udelson for the Global Poverty Research Lab, Kellog Institute of Management at Northwestern University

### Purpose
Household definitions used in multi-topic household surveys vary between surveys but have potentially significant implications for household composition, production, and poverty statistics. Standard definitions of the household usually include some intersection of keywords relating to residency requirements, common food consumption, and intermingling of income or production decisions. Despite best practices intending to standardize the definition of the household, it is unclear which types of definitions or which intersections of keywords in a definition result in different household compositions. We would like to compare many different household surveys, and their household composition definitions, with the resulting data from the study to see how these different definitions impact the data output itself.

This web scraper pulls household survey data from the ILO, WorldBank, and DataFirst websites to analyze a large variety of surveys.

### Implementation
The webscraper is implemented in Python 3.8.0, relying heavily on the BeautifulSoup and Selenium packages for data extraction.

### Set-Up
 - Download or pull this repository onto your local machine, wherever you would like to download study data
 - Create accounts on both [DataFirst](https://www.datafirst.uct.ac.za/dataportal/index.php/auth/register) and [WorldBank](https://microdata.worldbank.org/index.php/auth/register) if you wish to download data from these catalogs
 - Set the following environment variables with your credentials: 
   - DATAFIRST_PASSWORD, DATAFIRST_USERNAME, WORLDBANK_PASSWORD, WORLDBANK_USERNAME
 - Install necessary third party packages using pip
    - `pip install -r requirements.txt`
 - Run main.py to download all data from all three domains
    
