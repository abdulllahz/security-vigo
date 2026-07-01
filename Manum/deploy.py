import tarfile
import docker
import time
import json
import sys
import os
import io
######################################################################################################################################
# PROJECT MANUM
#   M -> Metrics
#   A -> Analytics
#   N -> Notifications and
#   U -> Unified
#   M -> Monitoring
# Usage:
#     sudo python3 deploy.py --migrate --indexer --dashboard --forwarder --test
#     sudo python3 deploy.py --migrate --indexer --dashboard
#     sudo python3 deploy.py --forwarder
#     sudo python3 deploy.py --agent
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
def get_ports(data,behalf):
    open_ports={}
    for source in data[behalf]:
      if('port' in data[behalf][source] and 'type' in data[behalf][source]):
        open_ports[data[behalf][source]['port']+'/'+data[behalf][source]['type']]=int(data[behalf][source]['port'])
      else:
        continue
    return open_ports
try:
######################################################################################################################################
# Init
    client = docker.from_env()
    base_dir=os.getcwd()
    agent=False
    migrate=False
    indexer=False
    dashboard=False
    forwarder=False
    test=False
    volumes = []
    sql=''
    collector=f"""
    [api]
      enabled = true
      address = "0.0.0.0:8686"
    """
    pipeline=f"""
    [api]
      enabled = true
      address = "0.0.0.0:8686"
    """
    for i in sys.argv[1:]:
        if(i == '--migrate'):
            migrate=True
        if(i == '--agent'):
            agent=True
        if(i == '--indexer'):
            indexer=True
        if(i == '--dashboard'):
            dashboard=True
        if(i == '--forwarder'):
            forwarder=True
        if(i == '--test'):
            test=True
    file=open('settings.json', 'r')
    data=json.load(file)
    file.close()
    network_name=data["name"]+'_network'
    if(not test):
      volumes = [data["indexer"]["storage"]+":/var/lib/clickhouse/store/","/tmp/logs:/var/log/clickhouse-server/"]
    indexer_config={
        "name":data["name"]+'_ClickHouse',
        "image":data["indexer"]["image"],
        "detach":True,
        "network":network_name,
        "ports":{'8123':data["indexer"]["http-port"],'9000':data["indexer"]["db-port"]},
        "environment":{'CLICKHOUSE_PASSWORD':data["indexer"]["password"]},
        "volumes":volumes
    }
    forwarder_config={
        "name":data["name"]+'_Vector',
        "image":data["forwarder"]["image"],
        "detach":True,
        "network":network_name,
        "entrypoint":'/bin/tail',
        "command":'-f /dev/null',
        "ports":get_ports(data,"forwarder"),
        "volumes":[
          base_dir+data["forwarder"]["cert_directory"]+":/home"+data["forwarder"]["cert_directory"],
          base_dir+data["forwarder"]["log_directory"]+":/tmp"+data["forwarder"]["log_directory"]
        ]
    }
    agent_config={
        "name":data["name"]+'_Agent',
        "image":data["forwarder"]["image"],
        "detach":True,
        "network":network_name,
        "entrypoint":'/bin/tail',
        "command":'-f /dev/null',
        "ports":get_ports(data,"agent")
    }
    dashboard_config={
        "name":data["name"]+'_Grafana',
        "image":data["dashboard"]["image"],
        "detach":True,
        "network":network_name,
        #"command":'tail -f /dev/null',1
        "ports":{'3000':data["dashboard"]["http-port"]},
        "volumes":[f"{base_dir}/backup.db:/var/lib/grafana/grafana.db"]
        #"environment":{'GF_SECURITY_ADMIN_USER': 'admin','GF_SECURITY_ADMIN_PASSWORD':data["dashboard"]["password"]}
    }
######################################################################################################################################
# Populate logging Features
    for entry in os.scandir(base_dir+'/Components'):
        print(entry.name)
        file=open(f"{base_dir}/Components/{entry.name}/{entry.name}.sql", 'r')
        temp=file.read()
        file.close()
        sql=sql+temp
        file=open(f"{base_dir}/Components/{entry.name}/{entry.name}.toml", 'r')
        temp=file.read()
        file.close()
        pipeline=pipeline+eval(temp)
        if os.path.exists(f"{base_dir}/Components/{entry.name}/Agent.toml"):
          file=open(f"{base_dir}/Components/{entry.name}/Agent.toml", 'r')
          temp=file.read()
          file.close()
          collector=collector+eval(temp)
######################################################################################################################################
# Remove residual
    containers = client.containers.list()
    for container in containers:
        if data["name"] in container.name:
            container.kill()
    containers = client.containers.list(all=True)
    for container in containers:
        if data["name"] in container.name:
            container.remove()
    networks = client.networks.list()
    for network in networks:
        if data["name"] in network.name:
            network.remove()
######################################################################################################################################
# Create networks
    network = client.networks.create(network_name, driver='bridge')
######################################################################################################################################
# Run containers
    if(indexer):
        idx = client.containers.run(**indexer_config)
        if(migrate):
            push_string_to_container(idx,'migrate.sql',sql, '/docker-entrypoint-initdb.d/')
            idx.exec_run(cmd='clickhouse-client --multiquery < /docker-entrypoint-initdb.d/migrate.sql', detach=True)
    if(agent):
        vec = client.containers.run(**agent_config)
        push_string_to_container(vec,'vector.toml', collector, '/home')
        vec.exec_run(cmd='apt update', detach=False)
        vec.exec_run(cmd='apt install -y redis-tools', detach=True)
        if(not test):
          vec.exec_run(cmd='vector --config /home/vector.toml', detach=True)
    if(forwarder):
        vec = client.containers.run(**forwarder_config)
        push_string_to_container(vec,'vector.toml', pipeline, '/home')
        vec.exec_run(cmd='apt update', detach=False)
        vec.exec_run(cmd='apt install -y redis-tools', detach=True)
        if(not test):
          vec.exec_run(cmd='vector --config /home/vector.toml', detach=True)
    if(dashboard):
        grf = client.containers.run(**dashboard_config)
        #push_string_to_container(grf,'grafana.ini', settings, '/etc/grafana/')
        #push_string_to_container(grf,'grafana.db', backup, '/var/lib/grafana/')
        #grf.exec_run(cmd='chown grafana /var/lib/grafana/grafana.db', detach=False)
        #grf.exec_run(cmd='chmod 0640 /var/lib/grafana/grafana.db', detach=False)
        #grf.exec_run(cmd='grafana server --homepath="/usr/share/grafana" --config="/etc/grafana/grafana.ini" --packaging=docker "$@" cfg:default.log.mode="console" cfg:default.paths.data="/var/lib/grafana" cfg:default.paths.logs="/var/log/grafana" cfg:default.paths.plugins="/var/lib/grafana/plugins" cfg:default.paths.provisioning="/etc/grafana/provisioning"', detach=True)
except Exception as e:
    print(f"An unexpected error occurred: {e}")