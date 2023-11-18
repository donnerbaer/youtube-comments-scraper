from app import app
from configparser import ConfigParser



class App:
    """_summary_
    """

    def __init__(self) -> None:
        """_summary_
        """
        self.__config = ConfigParser()
        self.__config.read('config.ini')
        


    def run(self) -> None:
        """_summary_
        """
        app.App(self.__config).main()
        




if __name__ == '__main__':
    print(f'App is running')
    App().run()
    print(f'\nApp has stopped working')
