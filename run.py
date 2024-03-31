from app import app
from configparser import ConfigParser



class App:
    """A class representing the main application.

    This class initializes the application and runs it.

    Attributes:
        __config (ConfigParser): The configuration parser object.

    """

    def __init__(self) -> None:
        """Initialize the App class.

        Reads the configuration file.

        """
        self.__config = ConfigParser()
        self.__config.read('config.ini')

    def run(self) -> None:
        """Run the application.

        Calls the main method of the app module.

        """
        app.App(self.__config).main()
        




if __name__ == '__main__':
    print(f'App is running')
    App().run()
    print(f'\nApp has stopped working')
