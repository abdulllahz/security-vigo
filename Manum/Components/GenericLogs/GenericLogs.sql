CREATE TABLE genericlog (
    `timestamp`                       DateTime64(3)                     COMMENT 'Event occurance time'                    CODEC(DoubleDelta,  ZSTD(1)),                                     
    `logstamp`                        DateTime64(3)                     COMMENT 'Event capture time'                      CODEC(DoubleDelta,  ZSTD(1)),
    `tag`                             LowCardinality(String)            COMMENT 'Service identifier (e.g., "Talos")'      CODEC(ZSTD(3)),
    `message`                         String                            COMMENT 'Body of the log'                         CODEC(ZSTD(3)) 
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp) 
ORDER BY (timestamp) 
TTL logstamp + INTERVAL 24 HOUR
SETTINGS index_granularity = 8192;