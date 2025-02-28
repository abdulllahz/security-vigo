import tarfile
import docker
import time
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
    return [file for file in os.listdir(f"{base_dir}/pipelines") if file.endswith('.conf') and file.startswith('enabled_')]
#try:
######################################################################################################################################
# Init
client = docker.from_env()
project_prefix = 'Bykea_Logging'
base_dir=os.getcwd()
pipelines=predicate_filelist(base_dir)
buffer=''
for pipeline in pipelines:
    f=open(f"{base_dir}/pipelines/{pipeline}")
    temp=f.read()
    f.close()
    start=temp.find("#=================================")+len("#=================================")+1
    end=temp[start:].find("#=================================")+len("#=================================")
    buffer=buffer+"- pipeline.id: %s\n  path.config: \"/usr/share/logstash/pipeline/%s\"\n%s\n"%(pipeline,pipeline,temp[start:end].replace('#',''))
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
ls = client.containers.run(
    name= project_prefix+'LogStash',
    image='logstash:8.13.4',
    detach=True,
    network=network_name,
    command='tail -f /dev/null',
    ports={**{f"{port}/tcp": port for port in range(65000,65535)}},
    volumes=[f"{base_dir}/pipelines:/usr/share/logstash/pipeline/"]
)
ls.exec_run(cmd='mkdir /usr/share/logstash/certificates')
#push_string_to_container(ls,'http_ca.crt', certificate, '/usr/share/logstash/certificates')
push_string_to_container(ls,'logstash.conf', buffer, '/usr/share/logstash/pipeline')
ls.exec_run(cmd='logstash --path.settings /usr/share/logstash/pipeline/logstash.conf', detach=False)       
#except Exception as e:
#    print('Exception!')
#    print(e)