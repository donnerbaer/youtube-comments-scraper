import configparser
import sqlite3

class App:
    """_summary_
    """

    def __init__(self, __config: configparser.ConfigParser) -> None:
        """_summary_
        """
        self.__config = __config
        self.__API_SECRET = self.__config['YOUTUBE']['API_SECRET']
        

        db_path = self.__config['APP']['DATABASE_PATH'] + self.__config['APP']['DATABASE_FILE']
        try:
            self.__connection = sqlite3.connect(db_path)
            self.__cursor = self.__connection.cursor()
        except sqlite3.OperationalError:
            print(f'Connection to database:     failed')





    def load_data(self) -> None:
        """_summary_
        """
        file_path = self.__config['DATA']['IMPORT_CHANNELS_FILE']

        file = open(file_path,'r')
        file.readline() # header

        for line in file.readlines():
            line = line.replace('\n','')
            data = line.split(',')


            #insert_content_creator = "INSERT INTO content_creator (person,about) VALUES (?,?)"
            insert_yt_channel = "INSERT INTO yt_channel (yt_channel_id, person, channelTitle, last_time_fetched, about) VALUES (?,?,?,?,?)"

            try:
                self.__cursor.execute(insert_yt_channel,data)
            except:
                print(data)
        
        self.__connection.commit()
        file.close()

        
    def __close_database(self) -> None:
        """_summary_
        """
        self.__cursor.close()
        self.__connection.close()







    def main(self):
        """_summary_
        """
        print(f'APP.py is running')
        self.load_data()

        self.__close_database