import configparser
import sqlite3
from datetime import datetime, timedelta
import googleapiclient.discovery
import json
import os





class App:
    """_summary_
    """

    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self, config: configparser.ConfigParser) -> None:
        """_summary_
        """
        self.__config = config

        api_key = self.__config['YOUTUBE']['API_SECRET']
        api_service_name = "youtube"
        api_version = "v3"

        self.__youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

        db_path = self.__config['APP']['DATABASE_PATH'] + self.__config['APP']['DATABASE_FILE']
        try:
            self.__connection = sqlite3.connect(db_path)
            self.__cursor = self.__connection.cursor()
        except sqlite3.OperationalError:
            print(f'Connection to database:     failed')



    def get_all_channel_files(self) -> list[str]:
        """_summary_

        Returns:
            list[str]: _description_
        """
        files_in_dir = os.listdir(self.__config['DATA']['IMPORT_CHANNELS_PATH'])
        files = []
        for file in files_in_dir:
            if '.csv' in file:
                files.append(file)
        return files
        


    def load_channels(self) -> None:
        """_summary_
        """
        files = self.get_all_channel_files()
        for file_name in files:
            file = open(self.__config['DATA']['IMPORT_CHANNELS_PATH'] + file_name,'r')
            file.readline() # header

            for line in file.readlines():
                line = line.replace('\n','')
                data = line.split(',')

                # TODO: 
                # db_response = 'select video_id from yt_video where id = ?'
                # if len(db_response) > 0:
                #   self.update_channel(yt_channel_id)
                # else:
                #   self.insert_channel(channel) # channel : list[str]


                # ignore channels without channel_id in .csv-files
                if data[0] == '':
                    continue

                insert_yt_channel = "INSERT INTO yt_channel (channel_id, person, channelTitle, last_time_fetched, about) VALUES (?,?,?,?,?)"
                self.__cursor.execute(insert_yt_channel,data)

            self.__connection.commit()
            file.close()



    def __close_database(self) -> None:
        """ close the cursor and the connection of the database
        """
        self.__cursor.close()
        self.__connection.close()



    def get_channels(self) -> list[str]: pass # TODO: implement
    def is_channel_new(self, channel_id: str) -> bool: pass # TODO: implement
    def insert_video(self, channel: dict) -> None: pass # TODO: implement
    def update_channel(self, channel_id: str) -> None: pass # TODO: implement


    def get_videos(self) -> list[str]: pass # TODO: implement
    def fetch_videos(self, channel_id: str) -> dict: pass # TODO: implement
    def is_video_new(self, video_id: str) -> bool: pass # TODO: implement
    def insert_video(self, video: dict) -> None: pass # TODO: implement
    def update_video(self, video_id: str) -> None: pass # TODO: implement


    def fetch_comments(self, video_id: str) -> dict: pass # TODO: implement
    def is_comment_new(self, comment_id: str) -> bool: pass # TODO: implement
    def insert_comment(self, comment: dict) -> None: pass # TODO: implement



    def main(self):
        """_summary_
        """
        self.load_channels()
        
        try:
            while True:
                # TODO: if datetime.now() - last_time_load_channels > timedelta(time=?): self.load_channels()

                # process channels
                channel_ids = self.get_channels()
                for channel_id in channel_ids:
                    videos = self.fetch_videos(channel_id)
                    for video in videos:
                        video_id = ''
                        if not self.is_video_new(video_id):
                            self.insert_video(video)
                        else:
                            self.update_video(video_id)
                    self.update_channel(channel_id)
                    self.__connection.commit()
                            
                # process videos
                video_ids = self.get_videos()
                for video_id in video_ids:
                    comments = self.fetch_comments(video_id)
                    for comment in comments:
                        comment_id = ''
                        if not self.is_comment_new(comment_id):
                            self.insert_comment(comment)
                    self.update_video(video_id)
                    self.__connection.commit()
                            
        except KeyboardInterrupt:
            self.__close_database()
            exit(0)

