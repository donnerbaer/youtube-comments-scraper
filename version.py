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
        print(f'python           | 3.11.3   | {sys.version}')
        print(f'googleapiclient  | 2.108.0  | {googleapiclient_version.__version__}')
        print(f'sqlite3          | 2.6.0    | {sqlite3.version}')



if __name__ == '__main__':
    Version()