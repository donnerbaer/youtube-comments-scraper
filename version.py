import sys
import sqlite3
from googleapiclient import version as googleapiclient_version



class Version:
    """A class that represents the version information.

    This class provides methods to print the required version and installed version
    of the needed libraries.

    Attributes:
        None

    Methods:
        __init__(): Initializes the Version object and prints the version information.
    """

    def __init__(self) -> None:
        """Initializes the Version object and prints the version information."""
        print()
        print( 'library          | required | installed ')
        print( '---------------- | -------- | ----------------------------')
        print(f'python           | 3.12.2   | {sys.version}')
        print(f'googleapiclient  | 2.121.0  | {googleapiclient_version.__version__}')
        print(f'sqlite3          | 3.43.1   | {sqlite3.sqlite_version}')



if __name__ == '__main__':
    Version()