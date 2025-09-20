import docker
import requests
client = docker.from_env()
project_prefix = 'Dimensionality_Benchmarks'
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
db0 = client.containers.run(
    name= project_prefix+'_db0',
    image='postgres:13.14-alpine3.19',
    detach=True,
    network=network_name,
    environment={
        'POSTGRES_USER':'root',
        'POSTGRES_DB':'ggwp',
        'POSTGRES_PASSWORD':'toor'
    }
)

toy=open('filename.txt', 'r').read().replace('#:TYPES',).replace('#:KCOLUMNS',).replace()
gw.exec_run(cmd='kong migrations bootstrap')