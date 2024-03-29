import configparser
import sqlite3
from datetime import datetime, timedelta
import googleapiclient.discovery
import json
import os
import sys





class App:
    """_summary_
    """

    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    __number_of_api_requests_left = 10_000
    

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



    def get_all_video_files(self) -> list[str]:
        """_summary_

        Returns:
            list[str]: _description_
        """
        files_in_dir = os.listdir(self.__config['DATA']['IMPORT_VIDEOS_PATH'])
        files = []
        for file in files_in_dir:
            if '.csv' in file:
                files.append(file)
        return files



    def load_videos(self) -> None:  # TODO:
        """_summary_
        """
        files:list = self.get_all_video_files()
        for file_name in files:
            file = open(self.__config['DATA']['IMPORT_VIDEOS_PATH'] + file_name,'r')
            self.process_video_files(file)
            self.__connection.commit()
            file.close()



    def process_video_files(self, file:object) -> None:  # TODO:
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

            if self.is_video_new(data[0]):
                query = '''INSERT INTO yt_video (id, title, publishedAt, last_time_fetched, description, channel_id) VALUES (?, ?, ?, ?, ?, ?)'''
                self.__cursor.execute(query, data)




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
        


    def get_videos(self) -> set[str]: 
        """_summary_

        Returns:
            list[str]: _description_
        """
        # oldest newest diff(last_fetch)
        deltas = [
            [timedelta(days=3), timedelta(minutes=15), 30*60],
            [timedelta(days=7), timedelta(days=3), 1*24*60*60],
            [timedelta(days=30), timedelta(days=7), 7*24*60*60],
            [timedelta(days=10*365), timedelta(days=30), 30*24*60*60]
        ]

        query = '''SELECT id
            FROM yt_video 
            WHERE 
                (
                    (publishedAt BETWEEN ? AND ?)
                    AND
                    strftime('%s', ?) - strftime('%s', last_time_fetched) > ?
                )	
                OR 
                    last_time_fetched = ""
        '''
        videos = set()
        for delta in deltas:
            now = datetime.now()
            result = self.__cursor.execute(query, (now - delta[0], now - delta[1], now, delta[2]))
            
            for video in result.fetchall():
                videos.add(video[0])
        return videos



    def fetch_videos(self, channel_id: str) -> list:
        """_summary_

        Args:
            channel_id (str): _description_

        Returns:
            list: _description_
        """
        videos = []
        self.check_api_requests_left()
        response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken='')
        while True:
            if 'items' in response:
                for video in response['items']:
                    if not self.is_video_upload(video):
                        continue
                    try:
                        videos.append(video)
                    except:
                        continue

                try:
                    nextPageToken = response['nextPageToken']
                    self.check_api_requests_left()
                    response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken=nextPageToken)

                except KeyError:
                    break
            else:
                break

        return videos



    def request_youtube_channel_videos(self, channel_id: str, nextPageToken: str) -> dict:
        """_summary_

        Args:
            channel_id (str): _description_
            nextPageToken (str): _description_

        Returns:
            dict: _description_
        """
        self.__number_of_api_requests_left = self.__number_of_api_requests_left - 1
        request = self.__youtube.activities().list(
            part = "snippet,contentDetails",
            channelId = channel_id,
            maxResults = 500,
            pageToken = nextPageToken
        )
        try:
            return request.execute()
        except:
            return {}



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



    def is_video_upload(self, video: dict) -> bool:
        """_summary_

        Args:
            video (dict): _description_

        Returns:
            bool: _description_
        """
        if video['snippet']['type'] == 'upload':
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
        publishedAt = snippet['publishedAt'][:19] + '.000000'
        self.__cursor.execute(query, (video_id, snippet['title'], publishedAt, '', snippet['description'], snippet['channelId']))



    def update_channel_last_time_fetched(self, channel_id: str) -> None:
        """_summary_

        Args:
            channel_id (str): _description_
        """
        query = '''UPDATE yt_channel
                    SET last_time_fetched = ?
                    WHERE channel_id = ?
                '''
        self.__cursor.execute(query,(datetime.now(), channel_id) )


        
    def update_video_last_time_fetched(self, video_id: str) -> None:
        """_summary_

        Args:
            video_id (str): _description_
        """
        query = '''UPDATE yt_video
                    SET last_time_fetched = ?
                    WHERE id = ?
                '''
        self.__cursor.execute(query,(datetime.now(), video_id) )



    def check_api_requests_left(self) -> None:
        """_summary_
        """
        if self.__number_of_api_requests_left == 0:
            print('{} no token requests left '.format(datetime.now()))
            os._exit(0)
        if self.__number_of_api_requests_left % 100 == 0:
            print('{} token requests left {}'.format(datetime.now(), self.__number_of_api_requests_left))



    def fetch_comments(self, video_id: str) -> list:
        """_summary_

        Args:
            video_id (str): _description_

        Returns:
            list: _description_
        """
        comments = []
        
        try:
            self.check_api_requests_left()
            response = self.request_youtube_video_comment(video_id=video_id, nextPageToken='')
        except googleapiclient.errors.HttpError:
            print('{} comments disabled @video_id {}'.format(datetime.now(), video_id))
            return comments
        except:
            # if e.g. comments are disabled
            print('{} error api_key: tried fetching @video_id {}'.format(datetime.now(), video_id))
            self.update_video_last_time_fetched(video_id)
            return comments
        
        while True:
            
            for comment in response['items']:
                try:
                    comments.append(comment)
                except:
                    continue

            try:                                                                        
                nextPageToken = response['nextPageToken']
            except KeyError:                                                   
                break 
            
            try:
                self.check_api_requests_left()
                response = self.request_youtube_video_comment(video_id=video_id, nextPageToken=nextPageToken)
            except googleapiclient.errors.HttpError:
                print('{} comments disabled @video_id {}'.format(datetime.now(), video_id))
                return comments
            except:
                # if e.g. comments are disabled
                print('{} error api_key: tried fetching @video_id {}'.format(datetime.now(), video_id))
                self.update_video_last_time_fetched(video_id)
                return comments
            
        return comments



    def request_youtube_video_comment(self, video_id:str, nextPageToken:str) -> dict:
        """_summary_

        Args:
            video_id (str): _description_
            nextPageToken (str): _description_

        Returns:
            dict: _description_
        """
        self.__number_of_api_requests_left = self.__number_of_api_requests_left - 1
        request = self.__youtube.commentThreads().list(
            part = "snippet,replies",
            videoId = video_id,
            maxResults = 500,
            pageToken = nextPageToken
        )
        return request.execute()



    def is_comment_new(self, comment_id: str) -> bool:
        """_summary_

        Args:
            comment_id (str): _description_

        Returns:
            bool: _description_
        """
        query = '''SELECT id 
                    FROM yt_comment
                    WHERE id = ?
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
                        description = ?,
                        channel_id = ?
                    WHERE id = ?
        '''
        publishedAt = snippet['publishedAt'][:19] + '.000000'
        self.__cursor.execute(query, ( snippet['title'], publishedAt, snippet['description'], snippet['channelId'], video_id), ) 



    def insert_comment(self, comment: dict) -> None:
        """_summary_

        Args:
            comment (dict): _description_
        """
        if 'youtube#commentThread' in comment['kind']:
            snippet = comment['snippet']['topLevelComment']['snippet']
            id = comment['snippet']['topLevelComment']['id']
        else:
            snippet = comment['snippet']
            id = comment['id']

        publishedAt = snippet['publishedAt'][:19] + '.000000'
        updatedAt = snippet['updatedAt'][:19] + '.000000'
        if 'totalReplyCount' not in snippet:
            totalReplyCount = 0
        else:
            totalReplyCount = snippet['totalReplyCount']

        if 'parentId' not in snippet:
            parentId = ''
        else:
            parentId = snippet['parentId']
        

        try:
            authorChannelId = snippet['authorChannelId']['value']
        except:
            authorChannelId = ''

        attributes = [id, 
                      authorChannelId, 
                      snippet['authorDisplayName'], 
                      parentId, 
                      publishedAt, 
                      updatedAt, 
                      snippet['textOriginal'], 
                      snippet['likeCount'], 
                      totalReplyCount, 
                      datetime.now(), 
                      snippet['videoId']
                      ]
        
        query = '''INSERT INTO yt_comment (
                    id, 
                    authorChannelId, 
                    authorDisplayName, 
                    parentId, 
                    publishedAt, 
                    updatedAt, 
                    textOriginal, 
                    likecount, 
                    totalReplyCount, 
                    last_time_fetched, 
                    video_id
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                '''
        self.__cursor.execute(query, attributes)



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
            


    def get_comment_id_from_fetch(self, comment: dict) -> str:
        """_summary_

        Args:
            video (dict): _description_

        Returns:
            str: _description_
        """
        try:
            return comment['topLevelComment']['id']
        except:
            pass 

        try:
            return comment['id']
        except:
            return ''



    def update_comment(self, comment) -> None:
        """_summary_

        Args:
            comment (_type_): _description_
        """
        #comment_id = self.get_comment_id_from_fetch(comment)
        if 'youtube#commentThread' in comment['kind']:
            snippet = comment['snippet']['topLevelComment']['snippet']
            id = comment['snippet']['topLevelComment']['id']
        else:
            snippet = comment['snippet']
            id = comment['id']
            
        query = '''UPDATE yt_comment
                    SET
                        authorChannelId = ?,
                        authorDisplayName = ?,
                        parentId = ?,
                        publishedAt = ?,
                        updatedAt = ?,
                        textOriginal = ?,
                        likeCount = ?,
                        totalReplyCount = ?,
                        last_time_fetched = ?,
                        video_id = ?
                    WHERE id = ?
        '''
        publishedAt = snippet['publishedAt'][:19] + '.000000'
        updatedAt = snippet['updatedAt'][:19] + '.000000'
        if 'totalReplyCount' not in snippet:
            totalReplyCount = 0
        else:
            totalReplyCount = snippet['totalReplyCount']

        parentId = ''
        if 'parentId' in snippet:
            parentId = snippet['parentId']

        authorChannelId = ''
        if 'authorChannelId' in snippet:
            authorChannelId = snippet['authorChannelId']['value']

        self.__cursor.execute(query, ( authorChannelId, 
                                        snippet['authorDisplayName'], 
                                        parentId, 
                                        publishedAt, 
                                        updatedAt, 
                                        snippet['textOriginal'], 
                                        snippet['likeCount'], 
                                        totalReplyCount,
                                        datetime.now(), 
                                        snippet['videoId'], 
                                        id
                                      ) 
                            )



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
                    last_time_load_csv = datetime.now()
                    print('{} csv loaded'.format(datetime.now()))

                # process channels
                channel_ids = self.get_channels()
                for channel_id in channel_ids:
                    print('{} process channel: {}'.format(datetime.now(), channel_id))
                    videos = self.fetch_videos(channel_id)
                    for video in videos:
                        video_id = self.get_video_id_from_fetch(video)
                        #if not type(video_id) == type(str) and not len(video_id) > 0:
                        #    continue
                        if self.is_video_new(video_id):
                            self.insert_video(video)
                            print('{} new video added: {}'.format(datetime.now(), video_id))
                        else:
                            self.update_video(video)
                    self.update_channel_last_time_fetched(channel_id)
                    self.__connection.commit()
                    if datetime.now() - last_time_load_csv > timedelta(minutes=5):
                        break
                

                # process videos
                video_ids = self.get_videos()
                for video_id in video_ids:
                    print('{} process video: {}'.format(datetime.now(), video_id))
                    comments = self.fetch_comments(video_id)
                    

                    for comment in comments:
                        if 'error' in comments:
                            print('no comments allowed')
                            comments = []
                            self.update_video_last_time_fetched(video_id)
                            self.__connection.commit()
                            continue

                        if 'snippet' in comment:
                            comment_id = comment['snippet']['topLevelComment']['id']
                            if self.is_comment_new(comment_id):
                                self.insert_comment(comment)
                            else:
                                self.update_comment(comment)

                        if 'replies' in comment:
                            for reply in comment['replies']['comments']:
                                reply_id = reply['id']
                                if self.is_comment_new(reply_id):
                                    self.insert_comment(reply)
                                else:
                                    self.update_comment(reply)  

                    self.update_video_last_time_fetched(video_id)
                    self.__connection.commit()
                    if datetime.now() - last_time_load_csv > timedelta(minutes=120):
                        break

        except KeyboardInterrupt:
            self.__close_database()
            exit(0)

