import tarfile
import docker
import time
import sys
import os
import io
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
    return [file for file in os.listdir(f"{base_dir}/pipelines") if file.endswith('.toml') and file.startswith('enabled_')]
#try:
######################################################################################################################################
# Init
client = docker.from_env()
project_prefix = 'Bykea_Logging'
#vector --config /home/vector.toml --log-format=json --log-level=debug
buffer="""
# Enable Vector's internal metrics collection
[api]
  enabled = true
  address = "0.0.0.0:8686"
  playground = false
[sources.ingest]
  type = "socket"
  mode = "udp"
  address = "0.0.0.0:65001"
  max_length = 10485760
[transforms.parse]
  type = "remap"
  inputs = ["ingest"]
  source = '''
    . = parse_json!(string!(.message))
    del(route)
    del(service)
    time=now()
    .logstamp = format_timestamp!(time, "%Y-%m-%dT%H:%M:%S%.3f")
    .timestamp = format_timestamp!(from_unix_timestamp!(.started_at, unit: "milliseconds"), "%Y-%m-%dT%H:%M:%S%.3f")
    .diffstamp , err1 = to_unix_timestamp(time, unit: "milliseconds") - .started_at
    .err1 = err1
    temp , err2 = to_string(.request.headers."x-app-user-token")
    .err2 = err2
    .request.headers."x-app-user-token" = redact(temp, filters: [r'[a-z0-9]+'], redactor: {"type": "text", "replacement": "*[REDACTED]*"})
    .request.uri, err3 = replace(.request.uri, r'\\?.*', "")
    .err3 = err3
  '''
[sinks.clickhouse]
  type = "clickhouse"
  inputs = ["parse"]
  endpoint = "http://10.100.4.223:8123"
  database = "default"
  table = "kong_api_logs"
  skip_unknown_fields = true
  compression = "gzip"
  auth.strategy = "basic"
  auth.user = "default"
  auth.password = "default"
"""
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
vec = client.containers.run(
    name= project_prefix+'Vector',
    image='timberio/vector:nightly-debian',
    detach=True,
    network=network_name,
    entrypoint='/bin/tail',
    command='-f /dev/null',
    ports={**{f"{port}/udp": port for port in range(65000,65010)}}
)
push_string_to_container(vec,'vector.toml', buffer, '/home')
#vec.exec_run(cmd='vector --config /home/vector.toml', detach=True)
#ls.exec_run(cmd='mkdir /usr/share/logstash/certificates')
#push_string_to_container(ls,'http_ca.crt', certificate, '/usr/share/logstash/certificates')
#except Exception as e:
#    print('Exception!')
#    print(e)