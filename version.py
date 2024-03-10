import sys
import sqlite3
from googleapiclient import version as googleapiclient_version



class Version:
    """_summary_
    """

    def __init__(self) -> None:
        """ print version required version and installed version of needed libraries
        """
        print()
        print(f'library          | required | installed ')
        print(f'---------------- | -------- | ----------------------------')
        print(f'python           | 3.12.2   | {sys.version}')
        print(f'googleapiclient  | 2.121.0  | {googleapiclient_version.__version__}')
        print(f'sqlite3          | 3.43.1   | {sqlite3.sqlite_version}')



if __name__ == '__main__':
    Version()