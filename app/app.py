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



    def load_videos(self) -> None:  # TODO:
        pass



    def process_video_files(self, file:object) -> None:  # TODO:
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
        


    def get_videos(self) -> set[str]: 
        """_summary_

        Returns:
            list[str]: _description_
        """
        # oldest newest diff(last_fetch)
        deltas = [
            [timedelta(hours=12), timedelta(hours=0), 5*60],
            [timedelta(days=1), timedelta(hours=12), 10*60],
            [timedelta(days=3), timedelta(days=1), 30*60],
            [timedelta(days=7), timedelta(days=3), 4*60*60],
            [timedelta(days=30), timedelta(days=7), 1*24*60*60],
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
        response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken='')
        while True:
            for video in response['items']:
                try:
                    videos.append(video)
                except:
                    continue

            try:
                nextPageToken = response['nextPageToken']
                response = self.request_youtube_channel_videos(channel_id=channel_id, nextPageToken=nextPageToken)

            except KeyError:
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



    def fetch_comments(self, video_id: str) -> list:
        """_summary_

        Args:
            video_id (str): _description_

        Returns:
            list: _description_
        """
        comments = []
        try:
            response = self.request_youtube_video_comment(video_id=video_id, nextPageToken='')
        except:
            # if e.g. comments are disabled
            print('{} error video disabled comments'.format(datetime.now()))
            return comments
        
        while True:
            for comment in response['items']:
                try:
                    comments.append(comment)
                except:
                    continue

            try:                                                                        
                nextPageToken = response['nextPageToken']
                response = self.request_youtube_video_comment(video_id=video_id, nextPageToken=nextPageToken)
            except KeyError:                                                   
                break 

        return comments



    def request_youtube_video_comment(self, video_id:str, nextPageToken:str) -> dict:
        """_summary_

        Args:
            video_id (str): _description_
            nextPageToken (str): _description_

        Returns:
            dict: _description_
        """
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

        if 'parentId' not in snippet:
            parentId = ''
        else:
            parentId = snippet['parentId']

        self.__cursor.execute(query, ( snippet['authorChannelId']['value'], 
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
                    print('{} csv loaded'.format(datetime.now()))

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
                            print('{} new video added'.format(datetime.now()))
                        else:
                            self.update_video(video)
                    self.update_channel_last_time_fetched(channel_id)
                    self.__connection.commit()
                

                # process videos
                video_ids = self.get_videos()
                for video_id in video_ids:
                    comments = self.fetch_comments(video_id)
                    if 'error' in comments:
                        print('no comments allowed')
                        comments = []
                        self.update_video_last_time_fetched(video_id)
                        self.__connection.commit()

                    for comment in comments:
                        
                        comment_id = self.get_comment_id_from_fetch(comment)
                        if self.is_comment_new(comment_id):
                            self.insert_comment(comment)
                        else:
                            self.update_comment(comment)

                        if 'replies' in comment:
                            for reply in comment['replies']['comments']:
                                reply_id = self.get_comment_id_from_fetch(comment)
                                if self.is_comment_new(reply_id):
                                    self.insert_comment(reply)
                                else:
                                    self.update_comment(reply)  

                    self.update_video_last_time_fetched(video_id)
                    self.__connection.commit()
                    if datetime.now() - last_time_load_csv > timedelta(minutes=15):
                        break

        except KeyboardInterrupt:
            self.__close_database()
            exit(0)

