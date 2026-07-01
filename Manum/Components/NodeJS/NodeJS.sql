CREATE TABLE node_metrics (
    `timestamp`               DateTime64(3)              COMMENT 'Event occurance time'                    CODEC(DoubleDelta,  ZSTD(1)),                                     
    `logstamp`                DateTime64(3)              COMMENT 'Event capture time'                      CODEC(DoubleDelta,  ZSTD(1)),
    `service_name`            LowCardinality(String)     COMMENT 'Service identifier (e.g., "Talos")'      CODEC(ZSTD(3)),
    `instance_id`             LowCardinality(String)     COMMENT 'Unique server/instance ID'               CODEC(ZSTD(3)),
    `host_name`               LowCardinality(String)     COMMENT 'Host machine name'                       CODEC(ZSTD(3)),
    `environment`             LowCardinality(String)     COMMENT 'Environment ("prod", "local", etc.)'     CODEC(ZSTD(3)),
    `method`                  LowCardinality(String)     COMMENT 'HTTP method'                             CODEC(ZSTD(3)),
    `path`                    String                     COMMENT 'HTTP resource path'                      CODEC(ZSTD(3)),
    `status_code`             UInt16                     COMMENT 'HTTP response code'                      CODEC(T64,          ZSTD(1)),
    `request_duration_ms`     Float32                    COMMENT 'Contoller call to res.send'              CODEC(FPC),
    `cpu_percent`             Float32                    COMMENT 'Average CPU usage all cores'             CODEC(FPC),
    `load_avg_1m`             Float32                    COMMENT 'Avg number of processes waiting for CPU' CODEC(FPC),
    `uptime_sec`              Float32                    COMMENT 'Process uptime'                          CODEC(FPC),
    `event_loop_lag_ms`       Float32                    COMMENT 'Average waiting time for event loop'     CODEC(FPC),
    `event_loop_lag_max_ms`   Float32                    COMMENT 'Max waiting time for event loop'         CODEC(FPC),
    `event_loop_utilization`  Float32                    COMMENT 'Event loop idle vs executing time'       CODEC(FPC),
    `memory_rss_mb`           Float32                    COMMENT 'Total memory used by process'            CODEC(FPC),
    `heap_used_mb`            Float32                    COMMENT 'JS heap used'                            CODEC(FPC),
    `heap_total_mb`           Float32                    COMMENT 'JS heap allocated'                       CODEC(FPC),
    `old_space_used_mb`       Float32                    COMMENT 'Long lived objects memoryusage'          CODEC(FPC),
    `heap_limit_mb`           Float32                    COMMENT 'Max allowed to be allocated by V8'       CODEC(FPC),
    `heap_usage_percent`      Float32                    COMMENT '% of heap used'                          CODEC(FPC),
    `external_mb`             Float32                    COMMENT 'Memory in use by external resources'     CODEC(FPC),
    `array_buffers_mb`        Float32                    COMMENT 'Memory for buffer like objects'          CODEC(FPC) 
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp) 
ORDER BY (timestamp) 
TTL logstamp + INTERVAL 24 HOUR
SETTINGS index_granularity = 8192;