/*
    DATA DEFINITION LANGUAGE
*/



CREATE TABLE IF NOT EXISTS yt_channel (
    id INTEGER,
    yt_channel_id TEXT,
    person TEXT,
    channelTitle TEXT,
    last_time_fetched TEXT,
    about TEXT,
    PRIMARY KEY(id)
);


CREATE TABLE IF NOT EXISTS yt_video (
    id TEXT,
    title TEXT,
    publishedAt TEXT,
    last_time_fetched TEXT,
    desciption TEXT,
    yt_channel_channel_id TEXT,
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS yt_comment (
    id TEXT,
    authorChannelId TEXT,
    authorDisplayName TEXT,
    parentId TEXT,
    publishedAt TEXT,
    updatedAt TEXT,
    textOriginal INTEGER,
    likecount INTEGER,
    totalReplyCpunt TEXT,
    last_time_fetched TEXT,
    yt_video_video_id TEXT,
    PRIMARY KEY(id)
);


