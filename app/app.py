import os
import configparser
import sqlite3
from datetime import datetime, timedelta
import googleapiclient.discovery


class App:
    """A class representing the YouTube Comments Scraper application.

    This class provides methods to load channels and videos, process channel and video files,
    fetch videos from YouTube channels, and perform database operations.

    Attributes:
        scopes (list[str]): The scopes required for accessing the YouTube API.
        __config (configparser.ConfigParser): The configuration object for the application.
        __number_of_api_requests_left (int): The number of remaining API requests.
        __youtube (googleapiclient.discovery.Resource): The YouTube API client.
        __connection (sqlite3.Connection): The connection to the SQLite database.
        __cursor (sqlite3.Cursor): The cursor for executing SQL queries.
    """

    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self, config: configparser.ConfigParser) -> None:
        """Initialize the App object.

        Args:
            config (configparser.ConfigParser): The configuration object for the application.
        """
        self.__config = config

        try:
            self.__number_of_api_requests_left = int(
                self.__config["YOUTUBE"]["NUMBER_OF_TOKENS"]
            )
        except Exception:
            print("NUMBER_OF_TOKENS type problem! NUMBER_OF_TOKENS is set to 10_000")
            self.__number_of_api_requests_left = 10_000

        api_key = self.__config["YOUTUBE"]["API_SECRET"]
        api_service_name = "youtube"
        api_version = "v3"

        self.__youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=api_key
        )

        db_path = (
            self.__config["APP"]["DATABASE_PATH"]
            + self.__config["APP"]["DATABASE_FILE"]
        )
        try:
            self.__connection = sqlite3.connect(db_path)
            self.__cursor = self.__connection.cursor()
        except sqlite3.OperationalError:
            print("Connection to database: failed")

    def get_all_channel_files(self) -> list[str]:
        """Returns a list of channel files in the specified directory.

        Returns:
            list[str]: A list of channel files.
        """
        files_in_dir = os.listdir(self.__config["DATA"]["IMPORT_CHANNELS_PATH"])
        files = []
        for file in files_in_dir:
            if ".csv" in file:
                files.append(file)
        return files

    def load_channels(self) -> None:
        """Load channels from files and process them.

        This method reads channel files from the specified path and processes each file.
        After processing each file, the changes are committed to the database.

        Returns:
            None
        """
        files = self.get_all_channel_files()
        for file_name in files:
            file = open(
                self.__config["DATA"]["IMPORT_CHANNELS_PATH"] + file_name,
                "r",
                encoding="utf-8",
            )
            self.process_channel_files(file)
            self.__connection.commit()
            file.close()

    def process_channel_files(self, file: object) -> None:
        """Process the channel files.

        This method reads the contents of a file, skips the header line, 
            and processes each line of data.
        If the channel is new, it inserts the channel data.

        Args:
            file (object): The file object to be processed.

        Returns:
            None
        """
        file.readline()  # header
        for line in file.readlines():
            line = line.replace("\n", "")
            data = line.split(",")

            if data[0] == "":
                continue

            if self.is_channel_new(data[0]):
                self.insert_channel(data)

    def get_all_video_files(self) -> list[str]:
        """Returns a list of video files in the specified directory.

        Returns:
            list[str]: A list of video file names.
        """
        files_in_dir = os.listdir(self.__config["DATA"]["IMPORT_VIDEOS_PATH"])
        files = []
        for file in files_in_dir:
            if ".csv" in file:
                files.append(file)
        return files

    def load_videos(self) -> None:
        """Load videos from the specified directory and process them.

        This method retrieves all video files from the specified directory,
        processes each file, and commits the changes to the database.

        Returns:
            None
        """
        files: list = self.get_all_video_files()
        for file_name in files:
            file = open(
                self.__config["DATA"]["IMPORT_VIDEOS_PATH"] + file_name,
                "r",
                encoding="utf-8",
            )
            self.process_video_files(file)
            self.__connection.commit()
            file.close()

    def process_video_files(self, file: object) -> None:
        """Process video files and insert data into the database.

        Args:
            file (object): The file object containing video data.

        Returns:
            None
        """
        file.readline()  # Skip header
        for line in file.readlines():
            line = line.replace("\n", "")
            data = line.split(",")

            if data[0] == "":
                continue

            if self.is_video_new(data[0]):
                query = """INSERT INTO yt_video
                            (
                                id,
                                title,
                                publishedAt,
                                last_time_fetched,
                                description,
                                channel_id
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """
                self.__cursor.execute(query, data)

    def __close_database(self) -> None:
        """Close the cursor and the connection of the database.

        This method commits any pending changes to the database, closes the cursor,
        and then closes the connection to the database.

        Returns:
            None
        """
        self.__connection.commit()
        self.__cursor.close()
        self.__connection.close()

    def get_channels(self) -> list[str]:
        """Retrieve a list of channel IDs based on the last time videos were fetched.

        Returns:
            list[str]: A list of channel IDs.
        """
        if self.__config["CHANNEL"]["TIME_SINCE_LAST_VIDEO_FETCH"].isdigit():
            time_since_last_video_fetch = int(
                self.__config["CHANNEL"]["TIME_SINCE_LAST_VIDEO_FETCH"]
            )
        else:
            time_since_last_video_fetch = 900

        query = """SELECT channel_id
                    FROM yt_channel 
                    WHERE 
                        strftime('%s', ?) - strftime('%s', last_time_fetched) > ?
                    OR 
                        last_time_fetched = ""
                """
        result = self.__cursor.execute(
            query, (datetime.now(), time_since_last_video_fetch)
        )
        channels = []
        for channel in result.fetchall():
            channels.append(channel[0])
        return channels

    def is_channel_new(self, channel_id: str) -> bool:
        """Check if a channel is new.

        Args:
            channel_id (str): The ID of the channel to check.

        Returns:
            bool: True if the channel is new, False otherwise.
        """
        query = """SELECT channel_id 
                    FROM yt_channel 
                    WHERE channel_id = ?
                """

        result = self.__cursor.execute(query, (channel_id,))
        res = result.fetchone()
        if res is None or len(res) == 0:
            return True
        if len(res) == 0:
            return True
        return False

    def insert_channel(self, channel: dict | list) -> None:
        """Inserts a channel into the database.

        Args:
            channel (dict | list): The channel information to be inserted.
                If a dictionary is provided, it should contain the following keys:
                    - channel_id: The ID of the channel.
                    - person: The person associated with the channel.
                    - channelTitle: The title of the channel.
                    - last_time_fetched: The last time the channel was fetched.
                    - about: Information about the channel.
                If a list is provided, it should contain the values in the same order 
                    as mentioned above.
        """
        query = """INSERT INTO yt_channel
                    (
                        channel_id,
                        person,
                        channelTitle,
                        last_time_fetched,
                        about
                    )
                    VALUES (?, ?, ?, ?, ?);
                """
        self.__cursor.execute(query, channel)

    def update_channel(self, channel_id: str) -> None:
        """Update the last time fetched for a YouTube channel.

        Args:
            channel_id (str): The ID of the YouTube channel.
        """
        query = """UPDATE yt_channel 
                    SET last_time_fetched = ?
                    WHERE channel_id = ?
                """
        self.__cursor.execute(query, (channel_id, datetime.now()))

    def get_videos(self) -> set[str]:
        """Retrieve videos based on specified criteria.

        Returns:
            set[str]: A set of video IDs that meet the criteria.
        """
        # oldest newest diff(last_fetch)
        deltas = [
            [timedelta(days=3), timedelta(minutes=15), 30 * 60],
            [timedelta(days=7), timedelta(days=3), 1 * 24 * 60 * 60],
            [timedelta(days=30), timedelta(days=7), 7 * 24 * 60 * 60],
            [timedelta(days=10 * 365), timedelta(days=30), 30 * 24 * 60 * 60],
        ]

        query = """SELECT id
            FROM yt_video 
            WHERE 
                (
                    (publishedAt BETWEEN ? AND ?)
                    AND
                    strftime('%s', ?) - strftime('%s', last_time_fetched) > ?
                )	
                OR 
                    last_time_fetched = ""
        """
        videos = set()
        for delta in deltas:
            now = datetime.now()
            result = self.__cursor.execute(
                query, (now - delta[0], now - delta[1], now, delta[2])
            )

            for video in result.fetchall():
                videos.add(video[0])
        return videos

    def fetch_videos(self, channel_id: str) -> list:
        """Fetches videos from a YouTube channel.

        Args:
            channel_id (str): The ID of the YouTube channel.

        Returns:
            list: A list of videos from the channel.
        """
        videos = []
        self.check_api_requests_left()
        response = self.request_youtube_channel_videos(
            channel_id=channel_id, next_page_token=""
        )
        while True:
            if "items" in response:
                for video in response["items"]:
                    if not self.is_video_upload(video):
                        continue
                    videos.append(video)

                try:
                    next_page_token = response["nextPageToken"]
                    self.check_api_requests_left()
                    response = self.request_youtube_channel_videos(
                        channel_id=channel_id, next_page_token=next_page_token
                    )

                except KeyError:
                    break
            else:
                break

        return videos

    def request_youtube_channel_videos(
        self, channel_id: str, next_page_token: str
    ) -> dict:
        """Request YouTube channel videos.

        This method sends a request to the YouTube API to retrieve channel videos
        based on the provided channel ID and next page token.

        Args:
            channel_id (str): The ID of the YouTube channel.
            next_page_token (str): The token for the next page of results.

        Returns:
            dict: A dictionary containing the response from the YouTube API.

        """
        self.__number_of_api_requests_left -= 1
        request = self.__youtube.activities().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=500,
            pageToken=next_page_token,
        )
        try:
            return request.execute()
        except Exception:
            return {}

    def is_video_new(self, video_id: str) -> bool:
        """Check if a video is new.

        Args:
            video_id (str): The ID of the video.

        Returns:
            bool: True if the video is new, False otherwise.
        """
        query = """SELECT id
                    FROM yt_video
                    WHERE id = ?
                """

        result = self.__cursor.execute(query, (video_id,))
        res = result.fetchone()
        if res is None or len(res) == 0:
            return True
        if len(res) == 0:
            return True
        return False

    def is_video_upload(self, video: dict) -> bool:
        """
        Check if the given video is an upload.

        Args:
            video (dict): A dictionary representing the video.

        Returns:
            bool: True if the video is an upload, False otherwise.
        """
        if video["snippet"]["type"] == "upload":
            return True
        return False

    def insert_video(self, video: dict) -> None:
        """Inserts a video into the database.

        Args:
            video (dict): A dictionary containing the video information.

        Returns:
            None
        """
        video_id = self.get_video_id_from_fetch(video)
        snippet = video["snippet"]
        query = """INSERT INTO yt_video
                    (
                        id, 
                        title, 
                        publishedAt, 
                        last_time_fetched, 
                        description, 
                        channel_id
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?);
                """
        published_at = snippet["publishedAt"][:19] + ".000000"
        self.__cursor.execute(
            query,
            (
                video_id,
                snippet["title"],
                published_at,
                "",
                snippet["description"],
                snippet["channelId"],
            ),
        )

    def update_channel_last_time_fetched(self, channel_id: str) -> None:
        """Update the last time fetched for a specific channel.

        Args:
            channel_id (str): The ID of the channel to update.
        """
        query = """UPDATE yt_channel
                    SET last_time_fetched = ?
                    WHERE channel_id = ?
                """
        self.__cursor.execute(query, (datetime.now(), channel_id))

    def update_video_last_time_fetched(self, video_id: str) -> None:
        """Update the last time a video was fetched.

        Args:
            video_id (str): The ID of the video to update.
        """
        query = """UPDATE yt_video
                    SET last_time_fetched = ?
                    WHERE id = ?
                """
        self.__cursor.execute(query, (datetime.now(), video_id))

    def check_api_requests_left(self) -> None:
        """Check the number of API requests left and take appropriate actions.

        This method checks the value of `self.__number_of_api_requests_left` and
        performs the following actions:
        - If the number of requests left is 0, it prints a message, commits the
        connection, and exits the program.
        - If the number of requests left is a multiple of 100, it prints a message
        with the current timestamp and the number of requests left.

        Returns:
            None
        """
        if self.__number_of_api_requests_left >= 0:
            if self.__number_of_api_requests_left == 0:
                print(f"{datetime.now()} no token requests left")
                self.__connection.commit()
                print(f"Tokens left: {self.__number_of_api_requests_left}")
                os._exit(0)
            if self.__number_of_api_requests_left % 100 == 0:
                print(
                    f"{datetime.now()} token requests left {self.__number_of_api_requests_left}"
                )

    def fetch_comments(self, video_id: str) -> list:
        """
        Fetches comments for a given YouTube video.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            list: A list of comments for the video.
        """
        comments = []

        try:
            self.check_api_requests_left()
            response = self.request_youtube_video_comment(
                video_id=video_id, next_page_token=""
            )
        except googleapiclient.errors.HttpError:
            print(f"{datetime.now()} comments disabled @video_id {video_id}")
            return comments
        except Exception:
            # if e.g. comments are disabled
            print(
                f"{datetime.now()} error api_key: tried fetching @video_id {video_id}"
            )
            self.update_video_last_time_fetched(video_id)
            return comments

        while True:

            for comment in response["items"]:
                try:
                    comments.append(comment)
                except Exception:
                    continue

            try:
                next_page_token = response["nextPageToken"]
            except KeyError:
                break

            try:
                self.check_api_requests_left()
                response = self.request_youtube_video_comment(
                    video_id=video_id, next_page_token=next_page_token
                )
            except googleapiclient.errors.HttpError:
                print(f"{datetime.now()} comments disabled @video_id {video_id}")
                return comments
            except Exception:
                # if e.g. comments are disabled
                print(
                    f"{datetime.now()} error api_key: tried fetching @video_id {video_id}"
                )
                self.update_video_last_time_fetched(video_id)
                return comments

        return comments

    def request_youtube_video_comment(
        self, video_id: str, next_page_token: str
    ) -> dict:
        """Request YouTube video comments.

        This method sends a request to the YouTube API to retrieve comments for a specific video.

        Args:
            video_id (str): The ID of the YouTube video.
            nextPageToken (str): The token for the next page of comments.

        Returns:
            dict: A dictionary containing the response from the YouTube API.
        """
        self.__number_of_api_requests_left = self.__number_of_api_requests_left - 1
        request = self.__youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=500,
            pageToken=next_page_token,
        )
        return request.execute()

    def is_comment_new(self, comment_id: str) -> bool:
        """Check if a comment is new.

        Args:
            comment_id (str): The ID of the comment.

        Returns:
            bool: True if the comment is new, False otherwise.
        """
        query = """SELECT id 
                    FROM yt_comment
                    WHERE id = ?
                """

        result = self.__cursor.execute(query, (comment_id,))
        res = result.fetchone()
        if res is None or len(res) == 0:
            return True
        return False

    def update_video(self, video: dict) -> None:
        """Update video information in the database.

        Args:
            video (dict): A dictionary containing the video information.

        Returns:
            None
        """
        video_id = self.get_video_id_from_fetch(video)
        snippet = video["snippet"]
        query = """UPDATE yt_video
                    SET
                        title = ?,
                        publishedAt = ?,
                        description = ?,
                        channel_id = ?
                    WHERE id = ?
        """
        published_at = snippet["publishedAt"][:19] + ".000000"
        self.__cursor.execute(
            query,
            (
                snippet["title"],
                published_at,
                snippet["description"],
                snippet["channelId"],
                video_id,
            ),
        )

    def insert_comment(self, comment: dict) -> None:
        """Inserts a comment into the database.

        Args:
            comment (dict): The comment data to be inserted.

        Returns:
            None
        """
        if "youtube#commentThread" in comment["kind"]:
            snippet = comment["snippet"]["topLevelComment"]["snippet"]
            id = comment["snippet"]["topLevelComment"]["id"]
        else:
            snippet = comment["snippet"]
            id = comment["id"]

        published_at = snippet["publishedAt"][:19] + ".000000"
        updated_at = snippet["updatedAt"][:19] + ".000000"
        if "totalReplyCount" not in snippet:
            total_reply_count = 0
        else:
            total_reply_count = snippet["totalReplyCount"]

        if "parentId" not in snippet:
            parent_id = ""
        else:
            parent_id = snippet["parentId"]

        try:
            author_channel_id = snippet["authorChannelId"]["value"]
        except KeyError:
            author_channel_id = ""

        attributes = [
            id,
            author_channel_id,
            snippet["authorDisplayName"],
            parent_id,
            published_at,
            updated_at,
            snippet["textOriginal"],
            snippet["likeCount"],
            total_reply_count,
            datetime.now(),
            snippet["videoId"],
        ]

        query = """INSERT INTO yt_comment (
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
                """
        self.__cursor.execute(query, attributes)

    def get_video_id_from_fetch(self, video: dict) -> str:
        """Extracts the video ID from the given video dictionary.

        Args:
            video (dict): A dictionary containing video details.

        Returns:
            str: The video ID extracted from the video dictionary.
        """
        try:
            return video["contentDetails"]["upload"]["videoId"]
        except KeyError:
            pass

        try:
            return video["contentDetails"]["playlistItem"]["resourceId"]["videoId"]
        except KeyError:
            return ""

    def get_comment_id_from_fetch(self, comment: dict) -> str:
        """Get the comment ID from the fetched comment.

        This method retrieves the comment ID from the fetched comment dictionary.
        It first tries to extract the ID from the 'topLevelComment' key, and if that fails,
        it tries to extract the ID from the 'id' key. If both attempts fail, an empty string is returned.

        Args:
            comment (dict): The fetched comment dictionary.

        Returns:
            str: The comment ID, or an empty string if the ID cannot be found.
        """
        try:
            return comment["topLevelComment"]["id"]
        except KeyError:
            pass

        try:
            return comment["id"]
        except KeyError:
            return ""

    def update_comment(self, comment) -> None:
        """Updates the information of a comment in the database.

        Args:
            comment (dict): The comment object containing the updated information.
        """
        # comment_id = self.get_comment_id_from_fetch(comment)
        if "youtube#commentThread" in comment["kind"]:
            snippet = comment["snippet"]["topLevelComment"]["snippet"]
            id = comment["snippet"]["topLevelComment"]["id"]
        else:
            snippet = comment["snippet"]
            id = comment["id"]

        query = """UPDATE yt_comment
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
        """
        published_at = snippet["publishedAt"][:19] + ".000000"
        updated_at = snippet["updatedAt"][:19] + ".000000"
        if "totalReplyCount" not in snippet:
            total_reply_count = 0
        else:
            total_reply_count = snippet["totalReplyCount"]

        parent_id = ""
        if "parentId" in snippet:
            parent_id = snippet["parentId"]

        author_channel_id = ""
        if "authorChannelId" in snippet:
            author_channel_id = snippet["authorChannelId"]["value"]

        self.__cursor.execute(
            query,
            (
                author_channel_id,
                snippet["authorDisplayName"],
                parent_id,
                published_at,
                updated_at,
                snippet["textOriginal"],
                snippet["likeCount"],
                total_reply_count,
                datetime.now(),
                snippet["videoId"],
                id,
            ),
        )

    def main(self):
        """
        This method is the main entry point of the application.
        It loads channels and videos, and then continuously processes the channels 
            and videos.
        It fetches videos for each channel, checks if the video is new, and inserts 
            or updates it accordingly.
        It also fetches comments for each video, checks if the comment is new, and 
            inserts or updates it accordingly.
        The process continues until interrupted by the user.
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
                    print(f"{datetime.now()} csv loaded")

                # process channels
                channel_ids = self.get_channels()
                for channel_id in channel_ids:
                    print(f"{datetime.now()} process channel: {channel_id}")
                    videos = self.fetch_videos(channel_id)
                    for video in videos:
                        video_id = self.get_video_id_from_fetch(video)
                        # if not type(video_id) == type(str) and not len(video_id) > 0:
                        #    continue
                        if self.is_video_new(video_id):
                            self.insert_video(video)
                            print(f"{datetime.now()} new video added: {video_id}")
                        else:
                            self.update_video(video)
                    self.update_channel_last_time_fetched(channel_id)
                    self.__connection.commit()
                    if datetime.now() - last_time_load_csv > timedelta(minutes=5):
                        break

                # process videos
                video_ids = self.get_videos()
                for video_id in video_ids:
                    print(f"{datetime.now()} process video: {video_id}")
                    comments = self.fetch_comments(video_id)

                    for comment in comments:
                        if "error" in comments:
                            print("no comments allowed")
                            comments = []
                            self.update_video_last_time_fetched(video_id)
                            self.__connection.commit()
                            continue

                        if "snippet" in comment:
                            comment_id = comment["snippet"]["topLevelComment"]["id"]
                            if self.is_comment_new(comment_id):
                                self.insert_comment(comment)
                            else:
                                self.update_comment(comment)

                        if "replies" in comment:
                            for reply in comment["replies"]["comments"]:
                                reply_id = reply["id"]
                                if self.is_comment_new(reply_id):
                                    self.insert_comment(reply)
                                else:
                                    self.update_comment(reply)

                    self.update_video_last_time_fetched(video_id)
                    self.__connection.commit()
                    if datetime.now() - last_time_load_csv > timedelta(minutes=120):
                        break

        except KeyboardInterrupt:
            print(f"Tokens left: {self.__number_of_api_requests_left}")
            self.__close_database()
            exit(0)
