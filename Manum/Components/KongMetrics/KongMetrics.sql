CREATE TABLE kong_metrics (
    `logstamp`                                                            DateTime64(3) CODEC(Delta, ZSTD),
    `database.reachable`                                                  Bool CODEC(T64, ZSTD),
    `memory.lua_shared_dicts.kong.allocated_slabs`                        Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong.capacity`                               Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_cluster_events.allocated_slabs`         Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_cluster_events.capacity`                Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_core_db_cache.allocated_slabs`          Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_core_db_cache.capacity`                 Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_core_db_cache_miss.allocated_slabs`     Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_core_db_cache_miss.capacity`            Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_db_cache.allocated_slabs`               Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_db_cache.capacity`                      Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_db_cache_miss.allocated_slabs`          Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_db_cache_miss.capacity`                 Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_healthchecks.allocated_slabs`           Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_healthchecks.capacity`                  Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_locks.allocated_slabs`                  Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_locks.capacity`                         Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_rate_limiting_counters.allocated_slabs` Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_rate_limiting_counters.capacity`        Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_secrets.allocated_slabs`                Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.kong_secrets.capacity`                       Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.prometheus_metrics.allocated_slabs`          Float64 CODEC(ZSTD),
    `memory.lua_shared_dicts.prometheus_metrics.capacity`                 Float64 CODEC(ZSTD),
    `server.connections_accepted`                                         UInt32 CODEC(T64, ZSTD),
    `server.connections_active`                                           UInt16 CODEC(T64, ZSTD),
    `server.connections_handled`                                          UInt32 CODEC(T64, ZSTD),
    `server.connections_reading`                                          UInt16 CODEC(T64, ZSTD),
    `server.connections_waiting`                                          UInt16 CODEC(T64, ZSTD),
    `server.connections_writing`                                          UInt16 CODEC(T64, ZSTD),
    `server.total_requests`                                               UInt32 CODEC(T64, ZSTD)
) ENGINE = MergeTree
PARTITION BY toYYYYMM(logstamp) 
ORDER BY (logstamp) 
TTL logstamp + INTERVAL 24 HOUR
SETTINGS index_granularity = 8192;