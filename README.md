# YouTube Video Information and Comments Fetcher

This program fetches YouTube video information and comments.

## Installation

1. Install the required libraries:

    You can install them individually:

    ```shell
    pip install sqlite3
    pip install google-api-python-client
    ```

    Or you can install them all at once using the requirements file:

    ```shell
    pip install -r requirements.txt
    ```

    To check the versions of the installed libraries, run:

    ```shell
    python version.py
    ```

    The required versions of the libraries are:

    | Library                  | Version | Notes    |
    | ------------------------ | ------- | -------- |
    | python                   | 3.12.2  | or newer |
    | google-api-python-client | 2.121.0 | or newer |
    | sqlite3                  | 3.43.1  | or newer |

2. Run the installation script:

    ```shell
    python install.py
    ```

    When prompted in the terminal, confirm with `y` and press enter.

3. Create a YouTube API Key:

    - Go to the [Google Developers Console](https://console.cloud.google.com/projectselector2/apis/dashboard?hl=de&supportedpurview=project)
    - Activate the YouTube API:
        - Go to the dashboard of the created project
        - Click on "Go to API overview" under "APIs"
        - Click on "+ Activate APIs and services" next to the "APIs and services" heading
        - Search for "YouTube Data API v3", select the corresponding API and click on "Activate API"

    - Request an API key:
        - Click on the YouTube API on the "APIs and services" page
        - Click on "Credentials"
        - Click on "+ Create credentials" and select "API key"

4. Configure the application:

    - Put your YouTube API token in `config.ini` as `API_SECRET`:

        ```ini
        API_SECRET=your_youtube_secret
        ```

    - Set the `NUMBER_OF_TOKENS` value according to your API key's quota:

        - If your API key has a default quota, set `NUMBER_OF_TOKENS=10000`
        - If your API key has an unlimited quota, set `NUMBER_OF_TOKENS=-1`
        - If your API key has a different quota, set `NUMBER_OF_TOKENS=` to that value

        Note: Spaces can cause problems.

    - Fill the `/data/channels.csv` file. You can have multiple `.csv` files, all will be used.

5. Run the application:

    ```shell
    python run.py
    ```

## FAQ

1. **Question:** Where can I get the YouTube Channel ID?
   **Answer:** Google is your friend.

2. **Question:** Where can I get the video id?
   **Answer:** From the Video URL. Example: www.youtube.com/watch?v=`0e3GPea1Tyg`

3. **Question:** What will the program fetch?
   **Answer:** If you use the channels.csv, it will fetch all columns in the yt_video and yt_comment tables (except the last_time_fetched)

4. **Question:** How does it work?
   **Answer:** If you fill the channel.csv file. It will first fetch all videos from the channels (for max. couple minutes). After all videos are fetched, it will fetch the public comments (for max. ~30 minutes). All couple minutes all channels will be refetched. Depending on the publication date, the video is fetched accordingly (new video more often). It also loads all csv files into the database every few minutes.

5. **Question:** Will it fetch all comments?
   **Answer:** For all public comments, it should work. If you have a limited API Key (10,000 Token/day) then maybe not. The program will terminate after the 10,000 token are exhausted. If I don't make a mistake, then a maximum of 1,000,000 comments should be received. It is maybe possible if the video has more than 1,000,000 comments, the program will not write the comments into the database.

6. **Question:** Can I also use several CSV files at the same time?
   **Answer:** Yes, you can use several `.csv`-files. It loads all csv files into the database every few minutes.

7. **Question:** What happens with the collected data, if the tokens are empty or I interrupt the program?
   **Answer:** If the program is cancelled or the tokens are used, the program may not write the already collected data into the database. The program will write data into the database if a channel/video is fetched till it finished. If otherwise: lucky for you.

8. **Question:** How long (time) can I use an API key till it is exhausted?
   **Answer:** Hard to say, it depends on how many comments per video and how many videos per channel.

9. **Question:** How many tokens are left?
   **Answer:** After every 100 used tokens, the remaining will be printed on the terminal/console.

## Note

An SQLite database is used. Which can reach its limit (really slow) at +8GB. If you want to use it for data science/analytics or other fun stuff.

## Disclaimer

Information provided without guarantee.