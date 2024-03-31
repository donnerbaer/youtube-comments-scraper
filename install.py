from configparser import ConfigParser
import os
import sqlite3

class Install:
    """This class represents the installation process for the YouTube Comments Scraper.

    It provides methods to initialize the installation, load the configuration,
        connect to the database, overwrite the configuration file, create the
        database file, create the channels file, create the videos file, create
        the necessary tables, check user input, and close the database connection.
    """

    def __init__(self) -> None:
        """Initializes the Install class."""
        self.__config = ConfigParser()

    def __load_config(self) -> None:
        """Load the configuration from the 'config.ini' file."""
        self.__config.read("config.ini")

    def __connect_database(self) -> None:
        """Connects to the database.

        This method establishes a connection to the SQLite database using the database path
        specified in the configuration file.

        Raises:
            sqlite3.OperationalError: If the connection to the database fails.
        """
        db_path = (
            self.__config["APP"]["DATABASE_PATH"]
            + self.__config["APP"]["DATABASE_FILE"]
        )
        try:
            self.__connection = sqlite3.connect(db_path)
            self.__cursor = self.__connection.cursor()
        except sqlite3.OperationalError:
            print("Connection to database: failed")

    def __overwrite_config(self) -> None:
        """Overwrites the existing config file with a template config file.

        This method reads the contents of a template config file and writes
            them to a new config file.
        The new config file will replace the existing config file.

        Args:
            None

        Returns:
            None
        """
        config_file_template = open(
                                "./template/template-config.ini",
                                "r",
                                encoding="utf-8"
                                )
        config_file = open("config.ini", "w", encoding="utf-8")
        config_file.writelines(config_file_template)
        config_file_template.close()
        config_file.close()
        print("Config overwritten")

    def __create_database_file(self) -> None:
        """Create a database file.

        This method creates a database file at the specified path in the configuration.
        If the directory does not exist, it will be created.

        Raises:
            OSError: If there is an error creating the database file or directory.

        """
        try:
            if not os.path.exists(self.__config["APP"]["DATABASE_PATH"]):
                os.makedirs(self.__config["APP"]["DATABASE_PATH"])
        except OSError:
            print("Creating database path failed")

        path = (
            self.__config["APP"]["DATABASE_PATH"]
            + self.__config["APP"]["DATABASE_FILE"]
        )

        db = open(path, "w", encoding="utf-8")
        db.close()
        print("Database file created")

    def __create_channels_file(self) -> None:
        """Create a channels.csv file in the specified import channels path.

        This method creates a channels.csv file in the import channels path
            specified in the configuration.
        If the path does not exist, it creates the necessary directories.
        The channels.csv file is created by copying the contents of the
            template/channels.csv file.

        Raises:
            OSError: If creating the directory fails.

        """
        try:
            if not os.path.exists(self.__config["DATA"]["IMPORT_CHANNELS_PATH"]):
                os.makedirs(self.__config["DATA"]["IMPORT_CHANNELS_PATH"])
        except OSError:
            print("Creating directory failed")

        file_template = open("template/channels.csv",
                             "r",
                             encoding="utf-8"
                             )
        file = open(
            self.__config["DATA"]["IMPORT_CHANNELS_PATH"] + "channels.csv",
            "w",
            encoding="utf-8",
        )
        file.write(file_template.read())
        file.close()
        file_template.close()
        print("Default channels.csv created")

    def __create_videos_file(self) -> None:
        """Create a videos file based on a template.

        This method creates a videos file by copying the contents of a template file.
        The template file should be located at 'template/videos.csv' relative to the 
            current working directory.
        The videos file will be created at the path specified in the configuration
            file under the 'IMPORT_VIDEOS_PATH' key.

        Raises:
            OSError: If creating the directory fails.

        """
        try:
            if not os.path.exists(self.__config["DATA"]["IMPORT_VIDEOS_PATH"]):
                os.makedirs(self.__config["DATA"]["IMPORT_VIDEOS_PATH"])
        except OSError:
            print("Creating directory failed")

        file_template = open("template/videos.csv",
                             "r",
                             encoding="utf-8"
                             )
        file = open(self.__config["DATA"]["IMPORT_VIDEOS_PATH"] + "videos.csv",
                    "w",
                    encoding="utf-8"
                    )
        file.write(file_template.read())
        file.close()
        file_template.close()
        print("Default videos.csv created")

    def __create_tables(self) -> None:
        """Create tables in the database using the provided DDL file.

        This method reads the DDL (Data Definition Language) file specified in
            the configuration, and executes the SQL statements to create the
            necessary tables in the database.

        Raises:
            Exception: If there is an error while creating the tables.

        """
        try:
            ddl = open(self.__config["SETUP"]["DATABASE_DDL"],
                       "r",
                       encoding="utf-8"
                       )
            self.__cursor.executescript(ddl.read())

            ddl.close()
            print("Tables created")
        except Exception:
            print("ERROR: tables not created")

    def __is_user_input_yes(self, user_input) -> bool:
        """Check if the user input is 'yes' or 'y'.

        Args:
            user_input (str): The user input to check.

        Returns:
            bool: True if the user input is 'yes' or 'y', False otherwise.
        """
        if user_input.lower() == "yes" or user_input.lower() == "y":
            return True
        return False

    def __close_database(self) -> None:
        """Closes the database connection and cursor.

        This method closes the connection to the database and the cursor 
            used for executing queries.

        Returns:
            None
        """
        self.__cursor.close()
        self.__connection.close()

    def main(self) -> None:
        """
        This method handles the main installation process.

        It prompts the user for input to determine if it's a new installation,
        and then performs various installation tasks based on the user's input.

        If it's a new installation, it asks for confirmation before proceeding.
        It then checks if the config.ini file needs to be overwritten and loads
            the config.
        It also checks if the default database and CSV files need to be reset
            and creates them if necessary.

        Args:
            None

        Returns:
            None
        """
        user_input = False
        text = 'New installation? [yes][y]/[no]: '
        new_installation = self.__is_user_input_yes(input(text))
        print()

        # hole installation
        if new_installation:
            text = "Are you sure? [yes][y]/[no]: "
            new_installation = self.__is_user_input_yes(input(text))
            print()
        if new_installation:
            print("New installation is executed\n")

        # config file
        if not new_installation:
            text = "Do you want to overwrite config.ini? [yes][y]/[no]: "
            user_input = self.__is_user_input_yes(input(text))
        if user_input or new_installation or not os.path.exists("config.ini"):
            self.__overwrite_config()
        self.__load_config()

        # database
        if not new_installation:
            text = "Do you want to reset the default database if exists? [yes][y]/[no]: "
            user_input = self.__is_user_input_yes(input(text))
        if user_input or new_installation:
            self.__create_database_file()
            self.__connect_database()
            self.__create_tables()
            self.__close_database()
        print()

        # channels.csv
        if not new_installation:
            text = "Do you want to reset the default channels.csv if exists? [yes][y]/[no]: "
            user_input = self.__is_user_input_yes(input(text))
        if user_input or new_installation:
            self.__create_channels_file()

        # videos.csv
        if not new_installation:
            text = "Do you want to reset the default videos.csv if exists? [yes][y]/[no]: "
            user_input = self.__is_user_input_yes(input(text))
        if user_input or new_installation:
            self.__create_videos_file()


if __name__ == "__main__":
    print("Install configuration")
    Install().main()
    print("Installation finished")
