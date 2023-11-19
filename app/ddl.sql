/*
    DATA DEFINITION LANGUAGE
*/



CREATE TABLE IF NOT EXISTS yt_channel (
    channel_id TEXT,
    person TEXT,
    channelTitle TEXT,
    last_time_fetched TEXT,
    about TEXT,
    PRIMARY KEY(channel_id)
);


CREATE TABLE IF NOT EXISTS yt_video (
    id TEXT,
    title TEXT,
    publishedAt TEXT,
    last_time_fetched TEXT,
    desciption TEXT,
    channel_id TEXT,
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
    video_id TEXT,
    PRIMARY KEY(id)
);


