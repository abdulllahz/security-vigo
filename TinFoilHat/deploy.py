import re
import docker
import time
client = docker.from_env()

project_prefix='TinFoilHat'
kibana_user='mitm_kib'
kibana_pass='mitm_kib'
es_user='elastic_kib'
es_pass='elastic_kib'
mitm_user='Security_Team'
mitm_pass='LolSometimes'

###################################################################
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
##################################################################
# Create networks
network_name=project_prefix+'_network'
network = client.networks.create(network_name, driver='bridge')
##################################################################
# elasticsearch
ES = client.containers.run(
    image= 'elasticsearch:8.12.1',
    network=network_name,
    detach= True,
	name= project_prefix+'_ES',
    hostname= project_prefix+'_ES',
    ports= {'9200': '9200', '9300': '9300'},
    mem_limit= '2g',
    environment= {
    	'discovery.type': 'single-node',
    	'ES_JAVA_OPTS': '-Xms750m -Xmx750m'
    }
)
time.sleep(30)
result=ES.exec_run(cmd=f'bin/elasticsearch-users useradd {kibana_user} -p {kibana_pass} -r kibana_system')
result=ES.exec_run(cmd=f'bin/elasticsearch-users useradd {mitm_user} -p {mitm_pass} -r superuser')
result=ES.exec_run(cmd=f'bin/elasticsearch-users useradd {es_user} -p {es_pass} -r superuser')
print('[✓] ElasticSearch credentials')
result=ES.exec_run(cmd="elasticsearch-create-enrollment-token -s kibana")
token=result.output.decode('utf-8')
##################################################################
# kibana
KIB = client.containers.run(
    image='kibana:8.12.1',
    network=network_name,
    detach=True,
    name= project_prefix+'_KIB',
    hostname= project_prefix+'_KIB',
    ports={'5601': '5601'}
)
time.sleep(30)
log=KIB.logs().decode('utf-8')
index=log.find('code=')+5
##################################################################
# core
PRX = client.containers.run(
    image='ubuntu:latest',
    network=network_name,
    detach=True,
    name= project_prefix+'_CORE',
    hostname= project_prefix+'_CORE',
    ports={'8080': '8080'},
    working_dir='/mitmproxy/plugins/',
    volumes=[
        '/home/anon/Misc/source/tengu/plugins:/mitmproxy/plugins/',
        '/home/anon/Misc/source/tengu/certificate:/root/.mitmproxy'
    ],
    environment={
        'MITMPROXY_ADDONS': '/mitmproxy/plugins/core.py',
        'ES_HOST': token,
        'ES_PORT': '9200',
        'ES_USER': es_user,
        'ES_PASS': es_pass
    },
    command='tail -f /dev/null'
)
result=PRX.exec_run(cmd='apt update')
print('[✓] Proxy update')
result=PRX.exec_run(cmd='apt install -y curl')
print('[✓] Proxy curl')
result=PRX.exec_run(cmd='apt install -y libyara-dev python3-yara')
print('[✓] Proxy yara')
result=PRX.exec_run(cmd='apt install -y python3-elasticsearch')
print('[✓] Proxy elasticsearch-client')
result=PRX.exec_run(cmd="apt install -y mitmproxy")
print('[✓] Proxy mitmproxy')
##################################################################
# setup
print(f"ElasticSearch   ID: {ES.id}")
print(f"Kibana          ID: {KIB.id}")
print(f"Proxy           ID: {PRX.id}")
print("Enrollment token: "+token)
print("Kibana Code: "+log[index:index+6])