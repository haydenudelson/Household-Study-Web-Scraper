# from src.DataFirstFetcher import DataFirstFetcher
from src.ILOFetcher import ILOFetcher
from src.DataFirstFetcher import DataFirstFetcher

def main():
    fetcher = DataFirstFetcher()
    fetcher.iterate_studies(0, 100)
if __name__ == "__main__":
    main()