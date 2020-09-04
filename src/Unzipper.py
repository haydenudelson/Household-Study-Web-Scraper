from abc import ABC
import os
import zipfile

class Unzipper(ABC):
    """ Class to unzip all zipfiles downloaded to studies """

    def unzip(self):
        docs_path = os.path.join(os.getcwd(), "docs")
        domains = [os.path.join(docs_path, o) for o in os.listdir(docs_path)]
        studies = [os.path.join(domains[0], o) for o in os.listdir(domains[0])] + [os.path.join(domains[1], o) for o in
                                                                                   os.listdir(domains[1])]
        for study in studies:
            files = [f for f in os.listdir(study) if os.path.isfile(os.path.join(study, f))]
            try:
                for file in files:
                    if ".zip" in file:
                        with zipfile.ZipFile(os.path.join(study, file), 'r') as zip_ref:
                            zip_ref.extractall(study)
            except zipfile.BadZipFile:
                print(study)


