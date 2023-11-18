


CREATE TABLE IF NOT EXISTS content_creator (
    id INTEGER,
    person TEXT,
    about TEXT,
    PRIMARY KEY(id)
);


CREATE TABLE IF NOT EXISTS yt_channel (
    channel_id TEXT,
    channelTitle TEXT,
    last_time_fetched TEXT,
    about TEXT,
    content_creator_id INTEGER,
    PRIMARY KEY(channel_id)
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


