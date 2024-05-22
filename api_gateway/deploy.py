import docker
import requests
import time
import copy
import json
import os
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
#      |---------|   |--------|   |---------|   |----------|   |-----------|   |---------------|   |--------|   |------|
#  ===>| Ingress |===| Routes |===| Plugins |===| Services |===| Upstreams |===| Loadbalancing |===| Egress |===| Node |===||
#      |---------|   |--------|   |---------|   |----------|   |-----------|   |---------------|   |--------|   |------|   ||
#                                                                                                                          ||
#                                                                                                                     |----------|
#  <==================================================================================================================| Response |
#                                                                                                                     |----------|
#
######################################################################################################################################
# Load configs
client = docker.from_env()
project_prefix = 'BykeaAPIGateway'
sandbox = '/home/anon/Misc/sandbox:/root/sandbox'
path='./config/'
configs=[]
for file in [file for file in os.listdir('./config/') if file.endswith('.json') and file.startswith('enabled_')]:
    f=open(path+file,'r')
    configs.append(json.load(f))
    f.close()
f=open(path+'common.json','r')
common=json.load(f)
f.close()
f=open(path+'Kong.json','r')
service_map=json.load(f)
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
db = client.containers.run(
    name= project_prefix+'_KongDB',
    image='postgres:9.6.24-alpine',
    #command='tail -f /dev/null',
    detach=True,
    network=network_name,
    environment={
        'POSTGRES_USER':'kong',
        'POSTGRES_DB':'kong',
        'POSTGRES_PASSWORD':'kong'
    }
)
time.sleep(10)
gw = client.containers.run(
    name= project_prefix+'_Gateway',
    image='kong:3.6.1',
    command='tail -f /dev/null',
    detach=True,
    network=network_name,
    environment={
        'KONG_DATABASE': 'postgres',
        'KONG_PG_HOST': project_prefix+'_KongDB',
        'KONG_PG_PASSWORD': 'kong',
        'KONG_CASSANDRA_CONTACT_POINTS': 'kong-database',
        'KONG_PROXY_ACCESS_LOG': '/dev/stdout',
        'KONG_ADMIN_ACCESS_LOG': '/dev/stdout',
        'KONG_PROXY_ERROR_LOG': '/dev/stderr',
        'KONG_ADMIN_ERROR_LOG': '/dev/stderr',
        'KONG_ADMIN_LISTEN': '0.0.0.0:8001,0.0.0.0:8444 ssl'
    },
    ports={
        '8000': '8000',
        '8443': '8443',
        '8001': '8001',
        '8444': '8444',
        '8002': '8002'
    }
)
gw.exec_run(cmd='kong migrations bootstrap')
gw.exec_run(cmd='kong start')
gw.exec_run(cmd='''curl -Ls https://get.konghq.com/quickstart | \\
                bash -s -- -i kong -t latest''')
print('Gateway: '+gw.id)
header={
        'Content-Type': 'application/json',
        'accept': 'application/json'
}
######################################################################################################################################
# Populate upstreams
for config in configs:
    payload={}
    payload.update(common['upstream'])
    payload.update(config['upstream'])
    payload.update({'name':f'{config["name"]}.kong.internal'})
    response = requests.post(f'http://127.0.0.1:8001/upstreams', json=payload, headers=header)
    upstream=response.json()['id']
######################################################################################################################################
# Populate targets
    for target in config['targets']:
        payload={}
        payload.update(common['targets'])
        payload.update(target)
        payload.update({'upstream':{'id':upstream}})
        response = requests.post(f'http://127.0.0.1:8001/upstreams/{upstream}/targets', json=payload, headers=header)
######################################################################################################################################
# Populate services
    payload={}
    payload.update(common['service'])
    payload.update(config['service'])
    payload.update({'name':config['name']})
    payload.update({'host':f'{config["name"]}.kong.internal'})
    response = requests.post(f'http://127.0.0.1:8001/services', json=payload, headers=header)
    service_id=response.json()['id']
######################################################################################################################################
# Populate routes
    for route in config['routes']:
        payload={}
        payload.update(common['routes'])
        payload.update(route)
        payload.update({'service': {'id': service_id}})
        payload.pop('original_path')
        response = requests.post(f'http://127.0.0.1:8001/routes', json=payload, headers=header)
        print('=======================================================')
        print(response.content)
        print(payload)
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
        response = requests.post(f'http://127.0.0.1:8001/routes/{route_id}/plugins', json=payload, headers=header)
######################################################################################################################################
# Populate ServiceMap
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
response = requests.post(f'http://127.0.0.1:8001/routes/{route_id}/plugins', json=payload, headers=header)