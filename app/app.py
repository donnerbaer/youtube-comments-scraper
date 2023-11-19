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
            self.process_channel_files(file)
            self.__connection.commit()
            file.close()



    def process_channel_files(self, file:object) -> None:
        """_summary_

        Args:
            file (str): _description_
        """
        file.readline() # header
        for line in file.readlines():
            line = line.replace('\n','')
            data = line.split(',')

            if data[0] == '':
                continue

            if self.is_channel_new(data[0]):
                self.insert_channel(data)



    def load_videos(self) -> None:
        pass



    def process_video_files(self, file:object) -> None:
        pass




    def __close_database(self) -> None:
        """ close the cursor and the connection of the database
        """
        self.__cursor.close()
        self.__connection.close()



    def get_channels(self) -> list[str]: 
        """_summary_

        Returns:
            list[str]: _description_
        """
        if self.__config['CHANNEL']['TIME_SINCE_LAST_VIDEO_FETCH'].isdigit():
            TIME_SINCE_LAST_VIDEO_FETCH = (int)(self.__config['CHANNEL']['TIME_SINCE_LAST_VIDEO_FETCH'])
        else:
            TIME_SINCE_LAST_VIDEO_FETCH = 900

        query = '''SELECT channel_id
                    FROM yt_channel 
                    WHERE 
                        strftime('%s', ?) - strftime('%s', last_time_fetched) > ?
                    OR 
                        last_time_fetched = ""
                '''
        result = self.__cursor.execute(query, (datetime.now(), TIME_SINCE_LAST_VIDEO_FETCH))
        channels = []
        for channel in result.fetchall():
            channels.append(channel[0])
        return channels



    def is_channel_new(self, channel_id: str) -> bool: 
        """_summary_

        Args:
            channel_id (str): _description_

        Returns:
            bool: _description_
        """
        query = '''SELECT channel_id 
                    FROM yt_channel 
                    WHERE channel_id = ?
                '''
        
        result = self.__cursor.execute(query, (channel_id,))
        res = result.fetchone()
        if type(res) == type(None):
            return True
        if len(res) == 0:
            return True
        return False



    def insert_channel(self, channel: dict|list) -> None: 
        """_summary_

        Args:
            channel (dict | list): _description_
        """
        query = '''INSERT INTO yt_channel (channel_id, person, channelTitle, last_time_fetched, about) 
                    VALUES (?, ?, ?, ?, ?);
                    
                '''
        self.__cursor.execute(query, channel)



    def update_channel(self, channel_id: str) -> None:
        """_summary_

        Args:
            channel_id (str): _description_
        """
        query = '''UPDATE yt_channel 
                    SET last_time_fetched = ?
                    WHERE channel_id = ?
                '''
        self.__cursor.execute(query,(channel_id, datetime.now()))
        


    def get_videos(self) -> list[str]: 
        """_summary_

        Returns:
            list[str]: _description_
        """
        query = '''SELECT channel_id
                    FROM yt_channel 
                    WHERE 
                    strftime('%s', ?) - strftime('%s', last_time_fetched)  > ?
                    OR last_time_fetched = ""
                '''
        result = self.__cursor.execute(query, (datetime.now(), self.__config['CHANNEL']['TIME_SINCE_LAST_VIDEO_FETCH']))
        return result



    def fetch_videos(self, channel_id: str) -> list:
        """_summary_

        Args:
            channel_id (str): _description_

        Returns:
            list: _description_
        """
        videos = []
        response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken='')
        while True:
            for video in response['items']:
                try:
                    videos.append(video)
                except:
                    continue

            try:                                                                        
                nextPageToken = response['nextPageToken']      
            except KeyError:                                                   
                break 
            response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken=nextPageToken)

        return videos



    def request_youtube_channel_videos(self, channel_id: str, nextPageToken: str) -> dict:
        """_summary_

        Args:
            channel_id (str): _description_
            nextPageToken (str): _description_

        Returns:
            dict: _description_
        """
        request = self.__youtube.activities().list(
            part = "snippet,contentDetails",
            channelId = channel_id,
            maxResults = 500,
            pageToken = nextPageToken
        )
        return request.execute()



    def is_video_new(self, video_id: str) -> bool:
        """_summary_

        Args:
            video_id (str): _description_

        Returns:
            bool: _description_
        """
        query = '''SELECT id 
                    FROM yt_video
                    WHERE id = ?
                '''
        
        result = self.__cursor.execute(query, (video_id,))
        res = result.fetchone()
        if type(res) == type(None):
            return True
        if len(res) == 0:
            return True
        return False



    def insert_video(self, video: dict) -> None:
        """_summary_

        Args:
            video_dict (dict): _description_
        """
        video_id = self.get_video_id_from_fetch(video)
        snippet = video['snippet']
        query = '''INSERT INTO yt_video (id, title, publishedAt, last_time_fetched, description, channel_id) 
                    VALUES (?, ?, ?, ?, ?, ?);
                '''
        self.__cursor.execute(query, (video_id, snippet['title'], snippet['publishedAt'], datetime.now(), snippet['description'], snippet['channelId']))



    def update_channel_last_time_fetched(self, channel_id: str) -> None:
        """_summary_

        Args:
            channel_id (str): _description_
        """
        query = '''UPDATE yt_channel
                    SET last_time_fetched = ?
                    WHERE channel_id = ?
                '''
        self.__cursor.execute(query,(datetime.now(),channel_id ))



    def fetch_comments(self, video_id: str) -> dict: pass # TODO: implement



    def is_comment_new(self, comment_id: str) -> bool:
        """_summary_

        Args:
            comment_id (str): _description_

        Returns:
            bool: _description_
        """
        query = '''SELECT comment_id 
                    FROM yt_comment
                    WHERE comment_id = ?
                '''
        
        result = self.__cursor.execute(query, (comment_id,))
        res = result.fetchone()
        if type(res) == type(None):
            return True
        if len(res) == 0:
            return True
        return False



    def update_video(self, video: dict) -> None:
        """_summary_

        Args:
            video (dict): _description_
        """
        video_id = self.get_video_id_from_fetch(video)
        snippet = video['snippet']
        query = '''UPDATE yt_video
                    SET
                        title = ?,
                        publishedAt = ?,
                        last_time_fetched = ?,
                        description = ?,
                        channel_id = ?
                    WHERE id = ?
        '''
        self.__cursor.execute(query, ( snippet['title'], snippet['publishedAt'], datetime.now(), snippet['description'], snippet['channelId'], video_id), ) 



    def insert_comment(self, comment_dict: dict) -> None:
        """_summary_

        Args:
            comment_dict (dict): _description_
        """
        # TODO: comment_dict to video: key:value handling
        comment = comment_dict
        query = '''INSERT INTO yt_comment (id, authorChannelId, authorDisplayName, parentId, publishedAt, updatedAt, textOriginal, likecount, totalReplyCpunt, last_time_fetched, video_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                '''
        self.__cursor.execute(query, comment)



    def get_video_id_from_fetch(self, video: dict) -> str:
        """_summary_

        Args:
            video (dict): _description_

        Returns:
            str: _description_
        """
        try:
            return video['contentDetails']['upload']['videoId']
        except:
            pass 

        try:
            return video['contentDetails']['playlistItem']['resourceId']['videoId']
        except:
            return ''
            


    def get_comment_id_from_fetch(self, comment: dict) -> str: # TODO: 
        """_summary_

        Args:
            comment (dict): _description_

        Returns:
            str: _description_
        """
        pass



    def main(self):
        """_summary_
        """
        self.load_channels()
        self.load_videos()
        last_time_load_csv = datetime.now()

        try:
            while True:
                if datetime.now() - last_time_load_csv > timedelta(minutes=5): 
                    self.load_channels()
                    self.load_videos()

                # process channels
                channel_ids = self.get_channels()
                for channel_id in channel_ids:
                    videos = self.fetch_videos(channel_id)
                    for video in videos:
                        video_id = self.get_video_id_from_fetch(video)
                        if not type(video_id) == type(str) and not len(video_id) > 0:
                            continue
                        if self.is_video_new(video_id):
                            self.insert_video(video)
                            #print('new video added')
                        else:
                            self.update_video(video)
                            #print('video updated: {} : {}'.format(video_id, video['snippet']['title']))
                    self.update_channel_last_time_fetched(channel_id)
                    self.__connection.commit()
                
                print('END')
                exit(0)            
                # process videos
                #video_ids = self.get_videos()
                #for video_id in video_ids:
                #    comments = self.fetch_comments(video_id)
                #    for comment in comments:
                #        comment_id = ''
                #        if not self.is_comment_new(comment_id):
                #            self.insert_comment(comment)
                #    self.update_video_last_time_fetched(video_id)
                #    self.__connection.commit()
                            
        except KeyboardInterrupt:
            self.__close_database()
            exit(0)

