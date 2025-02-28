import re
import docker
import time
client = docker.from_env()
project_prefix='YouWannaLog'
pipeline_f=open("pipeline/logstash.conf",'r')
pipeline_str=pipeline_f.read()
pipeline_f.close()
pipeline=pipeline_str.format(**{
    "logstash_port": logstash_port,
    "logstash_user": logstash_user,
    "logstash_pass": logstash_pass
})
logstash_port_mapped={f'{logstash_port}/udp':logstash_port}
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
# Spin up containers
ls = client.containers.run(
    name= project_prefix+'LogStash',
    image='logstash:8.13.4',
    detach=True,
    network=network_name,
    command='tail -f /dev/null',
    ports=logstash_port_mapped
)
push_string_to_container(ls,'http_ca.crt', certificate, '/usr/share/logstash/certificates')
push_string_to_container(ls,'logstash.conf', pipeline, '/usr/share/logstash/pipeline')
ls.exec_run(cmd='logstash -f pipeline/logstash.conf', detach=True)