from enum import Enum

# Different Domains we pull data from
class Domain(Enum):
    DATAFIRST = "DataFirst"
    ILO = "ILO"
    WORLDBANK = "WorldBank"

# File names for storing fetched data
METADATA_FILE = "metadata.csv"
RUN_REPORT = "runReport.txt"

MIN_INDEX = 0
MAX_INDEX = 2000

# Column names for metadata file, what metadata we pull for each study
HEADERS = ["Domain",
           "URL",
           "StudyName",
           "ReferenceID",
           "Country",
           "StartYear",
           "EndYear",
           "Producer",
           "StudyWebsiteURL",
           "DataFile",
           "Questionnaire",
           "InterviewerVariable"]

# Justification for study we give to download study data
STUDY_ABSTRACT = "Household definitions used in multi-topic household surveys vary between surveys but have \
                  potentially significant implications for household composition, production, and poverty statistics. \
                  Standard definitions of the household usually include some intersection of keywords relating to \
                  residency requirements, common food consumption, and intermingling of income or production decisions.\
                  Despite best practices intending to standardize the definition of the household, it is unclear which \
                  types of definitions or which intersections of keywords in a definition result in different household \
                  compositions. We would like to compare many different household surveys, and their household \
                  composition definitions, with the resulting data from the study to see how these different definitions \
                  impact the data output itself."
