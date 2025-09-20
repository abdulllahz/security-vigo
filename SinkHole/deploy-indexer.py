import tarfile
import docker
import time
import sys
import os
import io
######################################################################################################################################
# Usage:
#     sudo python3 deploy-indexer.py --password=PASSWORD --migrate
######################################################################################################################################
# Helpers
def push_string_to_container(container, file_name, content, target_dir):
    #tar_stream = create_tarfile_from_string(file_name, content)
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        file_data = io.BytesIO(content.encode('utf-8'))
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(file_data.getvalue())
        tar.addfile(tarinfo, file_data)
    tar_stream.seek(0)
    container.put_archive(path=target_dir, data=tar_stream)
def predicate_filelist(base_dir):
    return [file for file in os.listdir(f"{base_dir}/pipelines") if file.endswith('.conf') and file.startswith('enabled_')]
#try:
######################################################################################################################################
# Init
client = docker.from_env()
project_prefix = 'Bykea_Logging'
base_dir=os.getcwd()
migrate=False
for i in sys.argv[1:]:
    if('--password' in i):
        password=i.replace('--password','')
    else:
        password='default'
    if(i == '--migrate'):
        migrate=True
buffer='''
CREATE TABLE kong_api_logs (
    `request.id`		        String	DEFAULT ''					COMMENT 'Request identifier'								CODEC(ZSTD(1)),
    `logstamp`		            DateTime64(3)						COMMENT 'Meta: Timestamp pipeline recieved the event'		CODEC(DoubleDelta,  ZSTD(1)),
    `timestamp`		            DateTime64(3)						COMMENT 'Meta: Timestamp event occured'						CODEC(DoubleDelta,  ZSTD(1)),
    `diffstamp`		            UInt32          					COMMENT 'Meta: Difference between the two'					CODEC(T64,          ZSTD(1)),
    `started_at`		        DateTime64(3)						COMMENT 'Meta: Timestamp event occured'						CODEC(DoubleDelta,  ZSTD(1)),
    `source`		            LowCardinality(String)	DEFAULT '~'	COMMENT 'Meta: Request termination point'					CODEC(ZSTD(3)),
    `latencies.kong`	        UInt32	DEFAULT 99999				COMMENT 'Meta: Kongs Internal latency'						CODEC(T64,          ZSTD(1)),
    `latencies.proxy`	        UInt32	DEFAULT 99999				COMMENT 'Meta: End2End latency'								CODEC(T64,          ZSTD(1)),
    `latencies.receive`	        UInt32	DEFAULT 99999				COMMENT 'Meta: Upstream service latency'					CODEC(T64,          ZSTD(1)),
    `latencies.request`	        UInt32	DEFAULT 99999				COMMENT 'Meta: Kong to upstream transfer latency'			CODEC(T64,          ZSTD(1)),
    `client_ip`		            IPv4	DEFAULT '0.0.0.0'			COMMENT 'Request: Client IP'								CODEC(ZSTD(1)),
    `upstream_status`	        LowCardinality(String) DEFAULT '~'	COMMENT 'Request: The status code from the service'			CODEC(ZSTD(1)),
    `upstream_uri`		        String	DEFAULT ''					COMMENT 'Request: The path received by the service'			CODEC(ZSTD(3)),
    `request.method`	        LowCardinality(String)				COMMENT 'Request: Method'									CODEC(ZSTD(1)),
    `request.size`		        UInt32 DEFAULT 0					COMMENT 'Request: Size'										CODEC(T64,          ZSTD(1)),
    `request.uri`		        String DEFAULT ''					COMMENT 'Request: Path'										CODEC(ZSTD(3)),
    `request.url`		        String DEFAULT ''					COMMENT 'Request: Full santizied url'						CODEC(ZSTD(3)),
    `request.headers`		    String DEFAULT ''					COMMENT 'Request: Headers stored as JSON string'			CODEC(ZSTD(5)),
    `request.querystring`	    String DEFAULT ''					COMMENT 'Request: Query params stored as JSON string'		CODEC(ZSTD(5)),
    `request.body`		        String DEFAULT ''					COMMENT 'Request: Body stored as JSON string'				CODEC(ZSTD(7)),
    `request.tls.cipher`		String DEFAULT ''					COMMENT 'TODO'												CODEC(ZSTD(1)),
    `request.tls.client_verify`	String DEFAULT ''					COMMENT 'TODO'												CODEC(ZSTD(1)),
    `request.tls.version`		String DEFAULT ''					COMMENT 'TODO'												CODEC(ZSTD(1)),
    `response.status`		    LowCardinality(String) DEFAULT '~'	COMMENT 'Response: Code served by Kong'						CODEC(ZSTD(1)),
    `response.size`		        UInt32 DEFAULT 0					COMMENT 'Response: Size in bytes'							CODEC(T64, ZSTD(1)),
    `response.headers`		    String DEFAULT ''					COMMENT 'Response: Headers stored as JSON string'			CODEC(ZSTD(5)),
    `response.body`		        String DEFAULT ''					COMMENT 'Response: Body stored as JSON string'				CODEC(ZSTD(7)),
    `tries`		                String DEFAULT ''					COMMENT 'Meta: Loadbalancer stats stored as JSON string'	CODEC(ZSTD(5)),
    `err1`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3)),
    `err2`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3)),
    `err3`		                String DEFAULT ''					COMMENT 'Meta: pipeline errors'								CODEC(ZSTD(3)),
    `raw_json`		            String DEFAULT ''					COMMENT 'Meta: TOREMOVE'									CODEC(ZSTD(7)),
    `workspace`		            UUID 								COMMENT 'Meta: TOREMOVE'									CODEC(ZSTD(1)),
    `workspace_name`		    String DEFAULT ''					COMMENT 'Meta: TOREMOVE'									CODEC(ZSTD(1))
) ENGINE = MergeTree 
PARTITION BY toYYYYMM(timestamp) 
ORDER BY (timestamp) 
TTL timestamp + INTERVAL 18 HOUR
SETTINGS index_granularity = 8192;
'''
######################################################################################################################################
# Remove residual
containers = client.containers.list()
for container in containers:
    if project_prefix in container.name:
        container.kill()
containers = client.containers.list(all=True)
for container in containers:
    if project_prefix in container.name:
        container.remove()
networks = client.networks.list()
for network in networks:
    if project_prefix in network.name:
        network.remove()
######################################################################################################################################
# Create networks
network_name=project_prefix+'_network'
network = client.networks.create(network_name, driver='bridge')
######################################################################################################################################
# Run containers
idx = client.containers.run(
    name= project_prefix+'Indexer',
    image='clickhouse:25.7.1.3997-jammy',
    detach=True,
    network=network_name,
    #command='tail -f /dev/null',
    ports={'8123':8123,'9000':9000},
    #volumes=[f"/mnt/data/:/var/lib/clickhouse/store/"],
    environment= {'CLICKHOUSE_PASSWORD': password}
)
if(migrate):
    push_string_to_container(idx,'migrate.sql',buffer, '/docker-entrypoint-initdb.d/')
    idx.exec_run(cmd='clickhouse-client --multiquery < /docker-entrypoint-initdb.d/migrate.sql', detach=True)