import tarfile
import docker
import time
import sys
import os
import io
######################################################################################################################################
# Usage:
#     sudo python3 deploy-dashboard.py --password=PASSWORD
######################################################################################################################################
# Helpers
def push_string_to_container(container, file_name, content, target_dir):
    #tar_stream = create_tarfile_from_string(file_name, content)
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        file_data = io.BytesIO(content.encode('utf-8'))
        tarinfo = t
        arfile.TarInfo(name=file_name)
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
for(i in argv[1:]):
    if('--password' in i):
        password=i.replace('--password','')
    else:
        password='default'
buffer=''
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
grf = client.containers.run(
    name= project_prefix+'Grafana',
    image='grafana/grafana:12.2.0-16791878397',
    detach=True,
    network=network_name,
    #command='tail -f /dev/null',
    ports={'3000':3000},
    #volumes=[f"{base_dir}/pipelines:/usr/share/logstash/pipeline/"],
    environment= {'GF_SECURITY_ADMIN_USER': 'admin','GF_SECURITY_ADMIN_USER': password}
)