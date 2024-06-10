import docker
import requests
import tarfile
import time
import copy
import json
import sys
import os
import io
from dotenv import load_dotenv # pip3 install python-dotenv

# Load environment variables from .env_staging file
load_dotenv('.env_staging')


######################################################################################################################################
# ASCII art
print('''\033[91m0\033[94m---\033[31mO
 \033[91m0\033[34m=\033[31mo
  \033[91m0
 \033[31mo\033[34m=\033[91m0
\033[31mO\033[94m---\033[91m0
\033[31m0\033[94m---\033[91mO
 \033[31m0\033[34m=\033[91mo
  \033[31m0
 \033[91mo\33[34m=\033[31m0
\033[91mO\033[94m---\033[31m0
\033[91m0\033[94m---\033[31mO
 \033[91m0\033[34m=\033[31mo
  \033[91m0
 \033[31mo\033[34m=\033[91m0
\033[31mO\033[94m---\033[91m0\033[0m''')
######################################################################################################################################
#
#  Service Discovery:
#      |---------|   |-------------------------|   |------------------------------|   
#  ===>| Ingress |===| /api/v1/common/services |===| Plugins (Request Terminator) |===||
#      |---------|   |-------------------------|   |------------------------------|   || 
#                                                                                     ||
#                                                                               |------------|
#  <============================================================================| ServiceMap |
#                                                                               |------------|
#  
#  Service Routing: 
#      |---------|   |--------|   |---------|   |----------|   |-----------|   |------- |   |--------|   |------|
#  ===>| Ingress |===| Routes |===| Plugins |===| Services |===| Upstreams |===| Target |===| Egress |===| Node |===||
#      |---------|   |--------|   |---------|   |----------|   |-----------|   |--------|   |--------|   |------|   ||
#                                                                                                                   ||
#                                                                                                              |----------|
#  <===========================================================================================================| Response |
#                                                                                                              |----------|
#
######################################################################################################################################

# Config variables
logstash_user = os.getenv('LOGSTASH_USER')
logstash_pass = os.getenv('LOGSTASH_PASS')
dash_user = os.getenv('DASH_USER')
dash_pass = os.getenv('DASH_PASS')
kibana_user = os.getenv('KIBANA_USER')
kibana_pass = os.getenv('KIBANA_PASS')
project_prefix = os.getenv('PROJECT_PREFIX')
path = os.getenv('PATH')
postgres_host = os.getenv('POSTGRES_HOST')
postgres_port = os.getenv('POSTGRES_PORT')
postgres_user = os.getenv('POSTGRES_USER')
postgres_pass = os.getenv('POSTGRES_PASS')
redis_port = os.getenv('REDIS_PORT')
elasticsearch_host = os.getenv('ELASTICSEARCH_HOST')
elasticsearch_port = os.getenv('ELASTICSEARCH_PORT')
logstash_port = os.getenv('LOGSTASH_PORT')
logstash_host = os.getenv('LOGSTASH_HOST')
kibana_port = os.getenv('KIBANA_PORT')
kong_gateway_port = os.getenv('KONG_GATEWAY_PORT')
kong_gateway_ssl_port = os.getenv('KONG_GATEWAY_SSL_PORT')
kong_admin_port = os.getenv('KONG_ADMIN_PORT')
kong_admin_ssl_port = os.getenv('KONG_ADMIN_SSL_PORT')
kong_admin_ui_port = os.getenv('KONG_ADMIN_UI_PORT')

# Load configs
toggle_devmode='--db' in sys.argv or '-d' in sys.argv
toggle_logging='--log' in sys.argv or '-l' in sys.argv
if toggle_devmode:
    elasticsearch_host=project_prefix+'ElasticSearch'
    postgres_host=project_prefix+'DB'
    logstash_host=project_prefix+'LogStash'

pipeline=f'''
input {{
  udp {{
    port => {logstash_port}
    codec => json
  }}
}}
output {{
  elasticsearch {{
    hosts => ["{elasticsearch_host}:{elasticsearch_port}"]
    ssl => true
    ssl_certificate_verification => false
    cacert => "/usr/share/logstash/certificates/http_ca.crt"
    index => "http-%{{+YYYY.MM.dd}}"
    user => "{logstash_user}"
    password => "{logstash_pass}"
  }}
}}
'''
redis_port_mapped={redis_port:redis_port}
postgres_port_mapped={postgres_port:postgres_port}
elasticsearch_port_mapped={elasticsearch_port:elasticsearch_port,'9300':'9300'}
logstash_port_mapped={f'{logstash_port}/udp':logstash_port}
kibana_port_mapped={kibana_port:kibana_port}
kong_port_mapped={
        kong_gateway_port:kong_gateway_port,
        kong_gateway_ssl_port:kong_gateway_ssl_port,
        kong_admin_port:kong_admin_port,
        kong_admin_ssl_port:kong_admin_ssl_port,
        kong_admin_ui_port:kong_admin_ui_port
}
header={'Content-Type': 'application/json','accept': 'application/json'}

# Helpers
def create_tarfile_from_string(file_name, content):
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        # Create a file-like object from the string
        file_data = io.BytesIO(content.encode('utf-8'))
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(file_data.getvalue())
        tar.addfile(tarinfo, file_data)
    tar_stream.seek(0)
    return tar_stream

def push_string_to_container(container, file_name, content, target_dir):
    tar_stream = create_tarfile_from_string(file_name, content)
    container.put_archive(path=target_dir, data=tar_stream)

def parse_json_config(fpath):
    f=open(fpath,'r')
    string=json.load(f)
    f.close()
    return string

def predicate_filelist(internal):
    if internal:
        return [file for file in os.listdir('./config/') if file.endswith('.json') and 'Kong' in file and file.startswith('enabled_')]
    else:
        return [file for file in os.listdir('./config/') if file.endswith('.json') and 'Kong' not in file and file.startswith('enabled_')]

client = docker.from_env()
configs=[parse_json_config(path + file) for file in predicate_filelist(False)]
service_maps=[parse_json_config(path + file) for file in predicate_filelist(True)]
f=open(path+'internal_common.json','r')
common=json.load(f)
f.close()
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
if toggle_devmode:
    db = client.containers.run(
        name= project_prefix+'DB',
        image='postgres:9.6.24-alpine',
        detach=True,
        network=network_name,
        ports=postgres_port_mapped,
        environment={
            'POSTGRES_DB':'kong',
            'POSTGRES_USER':postgres_user,
            'POSTGRES_PASSWORD':postgres_pass
        }
    )
    rs = client.containers.run(
        name= project_prefix+'Cache',
        image='redis:7.0.15-alpine',
        detach=True,
        network=network_name,
        ports=redis_port_mapped
    )
gw = client.containers.run(
    name= project_prefix+'Gateway',
    image='kong:3.6.1',
    command='tail -f /dev/null',
    detach=True,
    network=network_name,
    environment={
        'KONG_DATABASE': 'postgres',
        'KONG_PG_HOST': postgres_host,
        'KONG_PG_PASSWORD': postgres_pass,
        'KONG_CASSANDRA_CONTACT_POINTS': 'kong-database',
        'KONG_PROXY_ACCESS_LOG': '/dev/stdout',
        'KONG_ADMIN_ACCESS_LOG': '/dev/stdout',
        'KONG_PROXY_ERROR_LOG': '/dev/stderr',
        'KONG_ADMIN_ERROR_LOG': '/dev/stderr',
        'KONG_ADMIN_LISTEN': f'0.0.0.0:{kong_admin_port},0.0.0.0:{kong_admin_ssl_port} ssl'
    },
    ports=kong_port_mapped
)

gw.exec_run(cmd='kong migrations bootstrap')
gw.exec_run(cmd='kong start')
gw.exec_run(cmd='''curl -Ls https://get.konghq.com/quickstart | \\
                bash -s -- -i kong -t latest''')
try:
    ######################################################################################################################################
    # Populate upstreams
    for config in configs:
        payload={}
        payload.update(common['upstream'])
        payload.update(config['upstream'])
        payload.update({'name':f'{config["name"]}.kong.internal'})
        response = requests.post(f'http://127.0.0.1:{kong_admin_port}/upstreams', json=payload, headers=header)
        upstream=response.json()['id']
    ######################################################################################################################################
    # Populate targets
        for target in config['targets']:
            payload={}
            payload.update(common['targets'])
            payload.update(target)
            payload.update({'upstream':{'id':upstream}})
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/upstreams/{upstream}/targets', json=payload, headers=header)
    ######################################################################################################################################
    # Populate services
        payload={}
        payload.update(common['service'])
        payload.update(config['service'])
        payload.update({'name':config['name']})
        payload.update({'host':f'{config["name"]}.kong.internal'})
        response = requests.post(f'http://127.0.0.1:{kong_admin_port}/services', json=payload, headers=header)
        service_id=response.json()['id']
    ######################################################################################################################################
    # Populate routes
        for route in config['routes']:
            payload={}
            payload.update(common['routes'])
            payload.update(route)
            payload.update({'service': {'id': service_id}})
            payload.pop('original_path')
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes', json=payload, headers=header)
            route_id=response.json()['id']
    ######################################################################################################################################
    # Populate mandatory plugin
            payload={}
            payload.update(common['rewriter'])
            payload['tags']=[route['paths'][0].replace('/','\\')]
            payload['instance_name']='ReWrite_'+route['name']
            payload['config']['replace']['uri']=route['original_path']
            payload.update({'service': {'id': service_id}})
            payload.update({'route': {'id': route_id}})
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes/{route_id}/plugins', json=payload, headers=header)
    ######################################################################################################################################
    # Populate ServiceMap
    for service_map in service_maps:
        payload={}
        payload.update(common['routes'])
        payload.update(service_map['routes'][0])
        payload.pop('original_path')
        response = requests.post(f'http://127.0.0.1:8001/routes', json=payload, headers=header)
        route_id=response.json()['id']
        payload={}
        payload.update(service_map['plugins'])
        payload['instance_name']='Responder_'+service_map['routes'][0]['name']
        payload.update({'route': {'id': route_id}})
        payload['config'].update({'body':json.dumps(service_map['ServiceMap'])})
        response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes/{route_id}/plugins', json=payload, headers=header)
    ######################################################################################################################################
    # Populate Logger
    if toggle_logging:
        if toggle_devmode:
            es = client.containers.run(
                name= project_prefix+'ElasticSearch',
                image='elasticsearch:8.13.4',
                detach=True,
                network=network_name,
                ports=elasticsearch_port_mapped,
                mem_limit= '2g',
                environment= {
    	            'discovery.type': 'single-node',
    	            'ES_JAVA_OPTS': '-Xms768m -Xmx768m'
                }
            )
            ls = client.containers.run(
                name= project_prefix+'LogStash',
                image='logstash:8.13.4',
                detach=True,
                network=network_name,
                command='tail -f /dev/null',
                ports=logstash_port_mapped
            )
            kb = client.containers.run(
                name= project_prefix+'Kibana',
                image='kibana:8.13.4',
                detach=True,
                network=network_name,
                ports=kibana_port_mapped
            )
            time.sleep(60)
            es.logs().decode('utf-8') #empty the stream first!
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {kibana_user} -p {kibana_pass} -r kibana_system')
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {dash_user} -p {dash_pass} -r superuser')
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {logstash_user} -p {logstash_pass} -r superuser')
            result=es.exec_run(cmd=f'bin/elasticsearch-create-enrollment-token -s kibana')
            token=result.output.decode('utf-8')
            log=kb.logs().decode('utf-8')
            index=log.find('code=')+5
            ls.exec_run(cmd='mkdir /usr/share/logstash/certificates')
            certificate=es.exec_run(cmd='cat /usr/share/elasticsearch/config/certs/http_ca.crt').output.decode('utf-8')
            push_string_to_container(ls,'http_ca.crt', certificate, '/usr/share/logstash/certificates')
            push_string_to_container(ls,'logstash.conf', pipeline, '/usr/share/logstash/pipeline')
            ls.exec_run(cmd='logstash -f pipeline/logstash.conf', detach=True)
            print('Enrollment token: '+token)
            print('Kibana Code: '+log[index:index+6])
        response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes', json={
            'enabled':True,
            'name':'udp-log',
            'instance_name':'Logger',
            'protocols':['grpc','grpcs','http','https'],
            'config':{
                'custom_fields_by_lua':{},
                'host':logstash_host,
                'port':logstash_port,
                'timeout':10000
            }
        }, headers=header)
except Exception as e:
    print('Exception!')
    print(e)
    print(config)
    print(payload)
    print(response.json())