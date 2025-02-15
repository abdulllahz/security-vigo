import threading
import requests
import tarfile
import docker
import time
import copy
import json
import sys
import os
import io

try:
######################################################################################################################################
# Usage
  #   sudo python3 deploy.py
  #    flags: 
  #     --db: self host DB
  #     --log: turn on logging
  #     --staging: prepare for staging environments
######################################################################################################################################
# Architecture
  #
  #  Service Discovery:
  #      |---------|   |-------------------------|   |------------------------------|   
  #  ===>| Ingress |===| /api/v1/common/services |===| Plugins (Request Terminator) |===||
  #      |---------|   |-------------------------|   |------------------------------|   || 
  #                                                                                     ||
  #                                                                               |------------|it oughta be having some if 
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
  # Request API Gateway Release:
  # Requester: ___________________
  # RFC: https://developer.mozilla.org/en-US/docs/Web/HTTP/Resources_and_specifications
  # Related PR: ___________________
  # Related Release:  ___________________
  # Method :: Host+Path :: RequestSchema :: ResponseSchema :: Auth? :: Redis? :: Resources (SMS,Voicecall) :: Expected Session QPS :: Expected Global QPS :: Usage Description :: Compliance
  # ______ :: _________ :: _____________ :: ______________ :: _____ :: ______ :: _________________________ :: ____________________ :: ___________________ :: _________________ :: __________
  # Gateway PR: ___________________
  # Interaction Diagram: ___________________
  # FE Dev Approval: Checkbox
  # BE Dev Approval: Checkbox
  # Sec Eng Approval: Checkbox
  # Data Eng Approval: Checkbox
  # Infra Eng Approval: Checkbox
######################################################################################################################################
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
        #tar_stream = create_tarfile_from_string(file_name, content)
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            file_data = io.BytesIO(content.encode('utf-8'))
            tarinfo = tarfile.TarInfo(name=file_name)
            tarinfo.size = len(file_data.getvalue())
            tar.addfile(tarinfo, file_data)
        tar_stream.seek(0)
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
    def run_cmd(container,command):
        results=container.exec_run(user="root", cmd=command)
        if(0!=results.exit_code):
            print(results.output)
    def animate():
        yellow=''
        red='\033[91m'
        dred='\033[31m'
        arr=[
            f'{red}0\033[94m---{dred}O\033[0m',
            f'{red}\u00200\033[34m={dred}o\033[0m',
            f'{red}\u0020\u00200\033[0m',
            f'{dred}\u0020o\033[34m={red}0\033[0m',
            f'{dred}O\033[94m---{red}0\033[0m',
            f'{dred}0\033[94m---{red}O\033[0m',
            f'{dred}\u00200\033[34m={red}o\033[0m',
            f'{dred}\u0020\u00200\033[0m',
            f'{red}\u0020o\33[34m={dred}0\033[0m',
            f'{red}O\033[94m---{dred}0\033[0m',
            f'{red}0\033[94m---{dred}O\033[0m',
            f'{red}\u00200\033[34m={dred}o\033[0m',
            f'{red}\u0020\u00200\033[0m',
            f'{dred}\u0020o\033[34m={red}0\033[0m',
            f'{dred}O\033[94m---{red}0\033[0m',
            f'{dred}0\033[94m---{red}O\033[0m',
            f'{dred}\u00200\033[34m={red}o\033[0m',
            f'{dred}\u0020\u00200\033[0m',
            f'{red}\u0020o\33[34m={dred}0\033[0m',
            f'{red}O\033[94m---{dred}0\033[0m',
            f'{red}0\033[94m---{dred}O\033[0m',
            f'{red}\u00200\033[34m={dred}o\033[0m'
            ]
        frame=len(arr)
        for i in range(0,10000):
            for j in range(0,frame):
                frame_buffer=arr[(j+i)%frame]
                if j < len(deployment_logs):
                    frame_buffer=frame_buffer + '\t' + deployment_logs[j]
                print(frame_buffer)
            if die:
                return 0
            time.sleep(0.2)
            os.system('clear')
######################################################################################################################################
# Config variables
# ELK
    elasticsearch_host=''
    elasticsearch_port='9200'
    logstash_user='logstash'
    logstash_pass='LoGstAsh_456'
    logstash_port='5775'
    logstash_host=''
    dash_user='Operations'
    dash_pass='Lol_Sometimes_4433'
    kibana_user='Kibana'
    kibana_pass='KibAna_456'
    kibana_port='5601'
# Postgres
    postgres_host='BykeaKongDB'
    postgres_port='5432'
    postgres_user='kong'
    postgres_pass='Kong_X1789'
# Redis
    redis_port='6379'
# Kong
    project_prefix = 'BykeaKong'
    path='./config/'
    kong_gateway_port='8000'
    kong_gateway_ssl_port='8443'
    kong_admin_port='8001'
    kong_admin_ssl_port='8444'
    kong_admin_ui_port='8002'
    forward_https='443'
    forward_http='80'
######################################################################################################################################
# Init!
    deployment_logs=[]
    thread1 = threading.Thread(target=animate)
    die=False
    thread1.start()
    toggle_aiomode='--db' in sys.argv or '-d' in sys.argv
    toggle_logging='--log' in sys.argv or '-l' in sys.argv
    toggle_staging='--staging' in sys.argv or '-s' in sys.argv
    if toggle_aiomode:
        elasticsearch_host=project_prefix+'ElasticSearch'
        postgres_host=project_prefix+'DB'
        logstash_host=project_prefix+'LogStash'
    if toggle_logging:
        pipeline_f=open("pipeline/logstash.conf",'r')
        pipeline_str=pipeline_f.read()
        pipeline_f.close()
        pipeline=pipeline_str.format(**{
            "logstash_port": logstash_port,
            "elasticsearch_host": elasticsearch_host,
            "elasticsearch_port": elasticsearch_port,
            "logstash_user": logstash_user,
            "logstash_pass": logstash_pass
        })
        deployment_logs.append("Logstash pipeline loaded")
    
    redis_port_mapped={redis_port:redis_port}
    postgres_port_mapped={postgres_port:postgres_port}
    elasticsearch_port_mapped={elasticsearch_port:elasticsearch_port,'9300':'9300'}
    logstash_port_mapped={f'{logstash_port}/udp':logstash_port}
    kibana_port_mapped={kibana_port:kibana_port}
    kong_port_mapped={
            kong_gateway_port:forward_http,
            kong_gateway_ssl_port:forward_https,
            kong_admin_port:kong_admin_port,
            kong_admin_ssl_port:kong_admin_ssl_port,
            kong_admin_ui_port:kong_admin_ui_port
    }
    header={'Content-Type': 'application/json','accept': 'application/json'}
    client = docker.from_env()
    deployment_logs.append("Connected to container engine")
    configs=[parse_json_config(path + file) for file in predicate_filelist(False)]
    deployment_logs.append("Loaded external configs")
    service_maps=[parse_json_config(path + file) for file in predicate_filelist(True)]
    deployment_logs.append("Loaded internal configs")
    f=open(path+'internal_common.json','r')
    common=json.load(f)
    f.close()
    deployment_logs.append("Loaded common parameters")
    base_dir=os.getcwd()
    deployment_logs.append("Init section done")
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
    deployment_logs.append("Killed old residual containers")
######################################################################################################################################
# Create networks
    network_name=project_prefix+'_network'
    network = client.networks.create(network_name, driver='bridge')
    deployment_logs.append("Network created")
######################################################################################################################################
# Run containers
    if toggle_aiomode:
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
        deployment_logs.append("Spun up postgres")
        rs = client.containers.run(
            name= project_prefix+'Cache',
            image='redis:7.0.15-alpine',
            detach=True,
            network=network_name,
            ports=redis_port_mapped
        )
        deployment_logs.append("Spun up redis")
    time.sleep(10)
    gw = client.containers.run(
        name= project_prefix+'Gateway',
        image='kong:3.9.0',
        command='tail -f /dev/null',
        detach=True,
        network=network_name,
        environment={
            'KONG_PG_SSL': 'on',
            'KONG_PG_USER': postgres_user,
            'KONG_PG_DATABASE': 'postgres',
            'KONG_PG_HOST': postgres_host,
            'KONG_PG_PASSWORD': postgres_pass,
            'KONG_CASSANDRA_CONTACT_POINTS': 'kong-database',
            'KONG_PROXY_ACCESS_LOG': '{base_dir}/logs/internal',
            'KONG_ADMIN_ACCESS_LOG': '{base_dir}/logs/internal',
            'KONG_PROXY_ERROR_LOG': '{base_dir}/logs/internal',
            'KONG_ADMIN_ERROR_LOG': '{base_dir}/logs/internal',
            'KONG_ADMIN_LISTEN': f'0.0.0.0:{kong_admin_port},0.0.0.0:{kong_admin_ssl_port} ssl'
        },
        volumes=[f"{base_dir}/logs:/tmp/kong"],
        ports=kong_port_mapped
    )
    deployment_logs.append("Spun up kong")
    run_cmd(gw,'kong migrations bootstrap -v')
    deployment_logs.append("Running migrations")
    run_cmd(gw,'kong start')
    deployment_logs.append("Started kong")
    run_cmd(gw,'apt update')
    run_cmd(gw,'apt install -y curl')
    run_cmd(gw,'''curl -Ls https://get.konghq.com/quickstart | \\
            bash -s -- -i kong -t latest''')
    deployment_logs.append("Added UI")
######################################################################################################################################
# Populate upstreams
    for config in configs:
        if('upstream' in config):
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
# Populate mandatory plugin
        if('rewriter' in config['meta']):
            payload={}
            payload.update(common['rewriter'])
            payload['tags']=['path_correction']
            payload['instance_name']='ReWrite_'+config['name']
            payload['config']['replace']['uri']=config['original_path']
            payload['config']['replace']['headers']=[f'Host: {config["original_host"]}']
            payload.update({'service': {'id': service_id}})
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/plugins', json=payload, headers=header)
        if('redirector' in config['meta']):
            payload={}
            payload.update(common['redirector'])
            payload['tags']=['redirection']
            payload['instance_name']='Redirect_'+config['name']
            payload['config']['location']=config['original_host']
            payload.update({'service': {'id': service_id}})
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/plugins', json=payload, headers=header)
######################################################################################################################################
# Populate routes
        for route in config['routes']:
            payload={}
            payload.update(common['routes'])
            payload.update(route)
            payload.update({'service': {'id': service_id}})
            if toggle_staging:
                payload.update({'service': {'hosts': common['environment']}})
            #payload.pop('original_path')
            response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes', json=payload, headers=header)
            route_id=response.json()['id']
######################################################################################################################################
# Populate ServiceMap
    deployment_logs.append("Gateway populated")
    for service_map in service_maps:
        payload={}
        payload.update(common['routes'])
        payload.update(service_map['routes'][0])
        response = requests.post(f'http://127.0.0.1:8001/routes', json=payload, headers=header)
        route_id=response.json()['id']
        payload={}
        payload.update(service_map['plugins'])
        payload['instance_name']='Responder_'+service_map['routes'][0]['name']
        payload.update({'route': {'id': route_id}})
        payload['config'].update({'body':json.dumps(service_map['ServiceMap'])})
        response = requests.post(f'http://127.0.0.1:{kong_admin_port}/routes/{route_id}/plugins', json=payload, headers=header)
    deployment_logs.append("Service discovery is ready")
######################################################################################################################################
# Populate Logger
    if toggle_logging:
        fb = client.containers.run(
            name= project_prefix+'FileBeat',
            image='docker.elastic.co/beats/filebeat:8.17.0',
            detach=True,
            command='tail -f /dev/null',
            network=network_name,
            environment={
                "ELASTICSEARCH_HOSTS": "https://Operation:Lol_Sometimes_4433@BykeaKongElasticSearch:9200"  # If required
            },
            volumes=[f"{base_dir}/logs:/tmp/kong"]
        )
        deployment_logs.append("Spun up filebeat")
        if toggle_aiomode:
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
            deployment_logs.append("Spun up elasticsearch")
            ls = client.containers.run(
                name= project_prefix+'LogStash',
                image='logstash:8.13.4',
                detach=True,
                network=network_name,
                command='tail -f /dev/null',
                ports=logstash_port_mapped
            )
            deployment_logs.append("Spun up logstash")
            kb = client.containers.run(
                name= project_prefix+'Kibana',
                image='kibana:8.13.4',
                detach=True,
                network=network_name,
                ports=kibana_port_mapped
            )
            deployment_logs.append("Spun up kibana")
            time.sleep(60)
            es.logs().decode('utf-8')
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {kibana_user} -p {kibana_pass} -r kibana_system')
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {dash_user} -p {dash_pass} -r superuser')
            result=es.exec_run(cmd=f'bin/elasticsearch-users useradd {logstash_user} -p {logstash_pass} -r superuser')
            deployment_logs.append("Users added")
            result=es.exec_run(cmd=f'bin/elasticsearch-create-enrollment-token -s kibana')
            token=result.output.decode('utf-8')
            log=kb.logs().decode('utf-8')
            index=log.find('code=')+5
            ls.exec_run(cmd='mkdir /usr/share/logstash/certificates')
            fb.exec_run(cmd='mkdir /usr/share/filebeat/certificates')
            certificate=es.exec_run(cmd='cat /usr/share/elasticsearch/config/certs/http_ca.crt').output.decode('utf-8')
            push_string_to_container(ls,'http_ca.crt', certificate, '/usr/share/logstash/certificates')
            push_string_to_container(ls,'logstash.conf', pipeline, '/usr/share/logstash/pipeline')
            ls.exec_run(cmd='logstash -f pipeline/logstash.conf', detach=True)
            deployment_logs.append("ELK configured")
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
    die=True
    thread1.join()
    deployment_logs.append("Done")
    if toggle_logging:
        print('enrollment token: '+token)
        print('kibana Code: '+log[index:index+6])
except Exception as e:
    die=True
    thread1.join()
    print(deployment_logs)
    print('Exception!')
    print(e)
    print('Config!')
    print(config)
    print('Payload!')
    print(payload)
    print('Response!')
    print(response.json())
