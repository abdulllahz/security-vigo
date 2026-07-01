CREATE TABLE elb (
    `logstamp`                                DateTime64(3)                                            CODEC(DoubleDelta,  ZSTD(1)),
    `timestamp`                               DateTime64(3)                                            CODEC(ZSTD(3)),
    `trace_id`                                String                                                   CODEC(ZSTD(3)),
    `request_url`                             String                                                   CODEC(ZSTD(3)),
    `actions_executed`                        LowCardinality(String)                                   CODEC(ZSTD(3)),
    `chosen_cert_arn`                         LowCardinality(String)                                   CODEC(ZSTD(3)),
    `classification`                          LowCardinality(String)                                   CODEC(ZSTD(3)),
    `classification_reason`                   LowCardinality(String)                                   CODEC(ZSTD(3)),
    `client_ip_port`                          LowCardinality(String)                                   CODEC(ZSTD(3)),
    `domain_name`                             LowCardinality(String)                                   CODEC(ZSTD(3)),
    `elb_name`                                LowCardinality(String)                                   CODEC(ZSTD(3)),
    `elb_status_code`                         LowCardinality(String)                                   CODEC(ZSTD(3)),
    `lambda_error_reason`                     LowCardinality(String)                                   CODEC(ZSTD(3)),
    `matched_rule_priority`                   LowCardinality(String)                                   CODEC(ZSTD(3)),
    `redirect_url`                            LowCardinality(String)                                   CODEC(ZSTD(3)),
    `request_method`                          LowCardinality(String)                                   CODEC(ZSTD(3)),
    `ssl_cipher`                              LowCardinality(String)                                   CODEC(ZSTD(3)),
    `ssl_protocol`                            LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_group_arn`                        LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_ip_port`                          LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_port_list`                        LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_status_code`                      LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_status_code_list`                 LowCardinality(String)                                   CODEC(ZSTD(3)),
    `type`                                    LowCardinality(String)                                   CODEC(ZSTD(3)),
    `request_protocol`                        LowCardinality(String)                                   CODEC(ZSTD(3)),
    `target_processing_time`                  Float64		                          		                 CODEC(LZ4),
    `response_processing_time`                Float64		                          		                 CODEC(LZ4),
    `request_processing_time`                 Float64		                          		                 CODEC(LZ4),
    `received_bytes`                          Int64 DEFAULT -1                                         CODEC(T64,          ZSTD(1)),
    `sent_bytes`                              Int64 DEFAULT -1                                         CODEC(T64,          ZSTD(1)),
    `user_agent`                              String                                                   CODEC(ZSTD(3))
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp) 
ORDER BY (logstamp) 
TTL logstamp + INTERVAL 12 HOUR
SETTINGS index_granularity = 8192;