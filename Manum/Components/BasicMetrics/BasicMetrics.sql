CREATE TABLE basic_metrics (
    `request.id`		        String	DEFAULT ''			        COMMENT 'Request identifier'								            CODEC(ZSTD(1)),
    `logstamp`		            DateTime64(3)						COMMENT 'Meta: Timestamp pipeline recieved the event'		CODEC(DoubleDelta,  ZSTD(1)),
    `timestamp`		            DateTime64(3)						COMMENT 'Meta: Timestamp event occured'						CODEC(DoubleDelta,  ZSTD(1)),
    `diffstamp`		            Int32          					    COMMENT 'Meta: Difference between the two'					CODEC(T64,          ZSTD(1)),
    `started_at`		        DateTime64(3)						COMMENT 'Meta: Timestamp event occured'						CODEC(DoubleDelta,  ZSTD(1)),
    `source`		            LowCardinality(String) DEFAULT '~'	COMMENT 'Meta: Request termination point'					CODEC(ZSTD(3)),
    `latencies.kong`	        Int32	DEFAULT 99999				COMMENT 'Meta: Kongs Internal latency'						CODEC(T64,          ZSTD(1)),
    `latencies.proxy`	        Int32	DEFAULT 99999				COMMENT 'Meta: End2End latency'								CODEC(T64,          ZSTD(1)),
    `latencies.receive`	        Int32	DEFAULT 99999				COMMENT 'Meta: Upstream service latency'					CODEC(T64,          ZSTD(1)),
    `latencies.request`	        Int32	DEFAULT 99999				COMMENT 'Meta: Kong to upstream transfer latency'			CODEC(T64,          ZSTD(1)),
    `client_ip`		            IPv4	DEFAULT '0.0.0.0'			COMMENT 'Request: Client IP'								CODEC(ZSTD(1)),
    `upstream_uri`		        String	DEFAULT ''					COMMENT 'Request: The path received by the service'			CODEC(ZSTD(3)),
    `request.method`	        LowCardinality(String)			    COMMENT 'Request: Method'									CODEC(ZSTD(1)),
    `request.size`		        Int32 DEFAULT 0					    COMMENT 'Request: Size'										CODEC(T64,          ZSTD(1)),
    `request.path`              LowCardinality(String) DEFAULT '~'  COMMENT 'Request: Generic Path'                             CODEC(ZSTD(3)),
    `request.uri`		        String DEFAULT ''					COMMENT 'Request: Specific Path'							CODEC(ZSTD(3)),
    `request.url`		        String DEFAULT ''					COMMENT 'Request: Full sanitzied url'						CODEC(ZSTD(3)),
    `request.headers`		    String DEFAULT ''					COMMENT 'Request: Headers stored as JSON string'			CODEC(ZSTD(5)),
    `request.querystring`	    String DEFAULT ''					COMMENT 'Request: Query params stored as JSON string'		CODEC(ZSTD(5)),
    `request.body`		        String DEFAULT ''					COMMENT 'Request: Body stored as JSON string'				CODEC(ZSTD(7)),
    `request.tls`               String DEFAULT '',
    `response.upstream`	        LowCardinality(String) DEFAULT '~'	COMMENT 'Request: The status code from the service'			CODEC(ZSTD(1)),
    `response.status`		    LowCardinality(String) DEFAULT '~'	COMMENT 'Response: Code served by Kong'						CODEC(ZSTD(1)),
    `response.size`		        Int32 DEFAULT 0					    COMMENT 'Response: Size in bytes'							CODEC(T64,          ZSTD(1)),
    `response.headers`		    String DEFAULT ''					COMMENT 'Response: Headers stored as JSON string'			CODEC(ZSTD(5)),
    `response.body`		        String DEFAULT ''					COMMENT 'Response: Body stored as JSON string'				CODEC(ZSTD(7)),
    `tries`		                String DEFAULT ''					COMMENT 'Meta: Loadbalancer stats stored as JSON string'	CODEC(ZSTD(5)),
    `err1`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3)),
    `err2`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3)),
    `err3`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3))
) ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp) 
ORDER BY (timestamp) 
TTL timestamp + INTERVAL 24 HOUR
SETTINGS index_granularity = 8192;