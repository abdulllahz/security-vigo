import docker
import requests
import time
import copy
import json
client = docker.from_env()
project_prefix = 'BykeaAPIGateway'
sandbox = '/home/anon/Misc/sandbox:/root/sandbox'
path='./config/'
###################################################################
files=['Kronos.json']
f=open(path+'common.json','r')
common=json.load(f)
configs=[]
for file in files:
    f=open(path+file,'r')
    configs.append(json.load(f))
###################################################################
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
###################################################################
# Create networks
network_name=project_prefix+'_network'
network = client.networks.create(network_name, driver='bridge')
###################################################################
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
for config in configs:
    payload={}
    payload.update(config['service'])
    payload.update(common['service'])
    response = requests.post('http://127.0.0.1:8001/services', json=payload, headers=header)
    service_id=response.json()['id']
    for route in config['routes']:
        payload={}
        payload.update(common['routes'])
        payload.update(route)
        payload.update({'service': {'id': service_id}})
        payload.pop('original_path')
        response = requests.post('http://127.0.0.1:8001/routes', json=payload, headers=header)
        print(response.content)
        print(payload)
        route_id=response.json()['id']
        payload={}
        payload.update(common['rewriter'])
        payload['tags']=[route['paths'][0].replace('/','\\')]
        payload['instance_name']='ReWrite_'+route['name']
        payload['config']['replace']['uri']=route['original_path']
        payload.update({'service': {'id': service_id}})
        payload.update({'route': {'id': route_id}})
        response = requests.post(f'http://127.0.0.1:8001/routes/{route_id}/plugins', json=payload, headers=header)
        print(response.content)
        
"""{
    'services':{
        'core':'talos_url',
        'auth':'raptor_url',
        'profile':'mis_url',
        'invoice':'kronos_url',
        'bidding':'bolee_url',
        'pickdrop':'belaz_url'
    }
}"""