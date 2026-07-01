CREATE TABLE trace (
    `timestamp`     DateTime64(3)                       COMMENT 'Meta: Timestamp event generated'              CODEC(DoubleDelta,  ZSTD(1)),
    `logstamp`      DateTime64(3)                       COMMENT 'Meta: Timestamp pipeline recieved the event'  CODEC(DoubleDelta,  ZSTD(1)),
    `SessionId`     String	DEFAULT ''                  COMMENT ''                                             CODEC(ZSTD(3)),
    `TName`         LowCardinality(String) DEFAULT '~'  COMMENT 'Thread name'                                  CODEC(ZSTD(3)),
    `CName`         LowCardinality(String) DEFAULT '~'  COMMENT 'Class name'                                   CODEC(ZSTD(3)),
    `Fid`           String	DEFAULT ''			        COMMENT 'Function id'					               CODEC(ZSTD(1)),
    `FName`         LowCardinality(String) DEFAULT '~'  COMMENT 'Function name'                                CODEC(ZSTD(3)),
    `Pid`           String	DEFAULT ''			        COMMENT 'Parent function id'					       CODEC(ZSTD(1)),
    `PName`         LowCardinality(String) DEFAULT '~'  COMMENT 'Parent function name'                         CODEC(ZSTD(3)),
    `args`          DEFAULT ''                          COMMENT 'Supplied arguments'                           CODEC(ZSTD(3)),
    `retval`        DEFAULT ''                          COMMENT 'Return value'                                 CODEC(ZSTD(3)),
    `delta`         Int64 DEFAULT -1                    COMMENT 'Time lapse'                                   CODEC(T64,          ZSTD(1)),
    `Mb`            Int32                               COMMENT 'Memory before'                                CODEC(T64,          ZSTD(1)),
    `Ma`            Int32                               COMMENT 'Memory after'                                 CODEC(T64,          ZSTD(1)),
    `exception`     String DEFAULT ''                   COMMENT 'Exception'                                    CODEC(ZSTD(3))
) ENGINE = MergeTree 
PARTITION BY toYYYYMM(logstamp) 
ORDER BY (logstamp) 
TTL logstamp + INTERVAL 24 HOUR
SETTINGS index_granularity = 8192;