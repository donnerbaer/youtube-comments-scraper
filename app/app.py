import configparser


class App:
    """_summary_
    """

    def __init__(self, __config: configparser.ConfigParser) -> None:
        """_summary_
        """
        self.__API_SECRET = __config['YOUTUBE']['API_SECRET']
        
        pass


    def main(self):
        """_summary_
        """
        pass