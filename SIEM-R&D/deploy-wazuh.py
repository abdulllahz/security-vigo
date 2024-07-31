import docker
import time
import os
client = docker.from_env()
project_prefix = 'wazuh'
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
#/usr/share/wazuh-indexer/entrypoint.sh:
network_name=project_prefix+'_network'
network = client.networks.create(network_name, driver='bridge')
##################################################################
Indexer= client.containers.run(
        name= project_prefix+'.Indexer',
        image='debian:sid-slim',
        command='tail -f /dev/null',
        detach=True,
        ports={
            '9200':9200,
            '55001':55001
        },
        network=network_name,
        #environment={'OPENSEARCH_JAVA_OPTS': '-Xms750m -Xmx750m'}
        #volumes=volumes
)

cmds=["apt update",
"apt install -y curl",
"apt install -y lsof",
"apt install -y gawk",
"apt install -y procps",
"apt install -y libcap2-bin",
"apt install -y lsb-release",
"curl -sO https://packages.wazuh.com/4.8/wazuh-install.sh",
"curl -sO https://packages.wazuh.com/4.8/wazuh-certs-tool.sh",
"curl -sO https://packages.wazuh.com/4.8/config.yml",
"chmod 744 wazuh-install.sh",
"chmod 744 wazuh-certs-tool.sh",
"mkdir -p /usr/share/filebeat/module",
f"sed -i 's/<indexer-node-ip>/{'siem.bykea.dev'}/g' config.yml",
f"sed -i 's/<wazuh-manager-ip>/{'siem.bykea.dev'}/g' config.yml",
f"sed -i 's/<dashboard-node-ip>/{'siem.bykea.dev'}/g' config.yml",
"./wazuh-install.sh -dw deb",
"./wazuh-certs-tool.sh --all",
"tar -xzf wazuh-offline.tar.gz",
"tar -xzf wazuh-offline/wazuh-files/wazuh-filebeat-0.4.tar.gz -C /usr/share/filebeat/module",
"dpkg -i /wazuh-offline/wazuh-packages/wazuh-indexer_4.8.1-1_amd64.deb",
"dpkg -i /wazuh-offline/wazuh-packages/wazuh-manager_4.8.1-1_amd64.deb",
"dpkg -i /wazuh-offline/wazuh-packages/wazuh-dashboard_4.8.1-1_amd64.deb",
"dpkg -i /wazuh-offline/wazuh-packages/filebeat-oss-7.10.2-amd64.deb",
"mkdir /etc/wazuh-indexer/certs",
"mkdir /etc/wazuh-dashboard/certs",
"mkdir /etc/filebeat/certs",
"/var/ossec/bin/wazuh-keystore -f indexer -k username -v admin",
"/var/ossec/bin/wazuh-keystore -f indexer -k password -v admin",
"cp wazuh-offline/wazuh-files/filebeat.yml /etc/filebeat/",
"cp wazuh-offline/wazuh-files/wazuh-template.json /etc/filebeat/",
"cp wazuh-certificates/node-1.pem /etc/wazuh-indexer/certs/indexer.pem",
"cp wazuh-certificates/node-1-key.pem /etc/wazuh-indexer/certs/indexer-key.pem",
"cp wazuh-certificates/admin-key.pem /etc/wazuh-indexer/certs/",
"cp wazuh-certificates/admin.pem /etc/wazuh-indexer/certs/",
"cp wazuh-certificates/wazuh-1.pem /etc/filebeat/certs/filebeat.pem",
"cp wazuh-certificates/wazuh-1-key.pem /etc/filebeat/certs/filebeat-key.pem",
"cp wazuh-certificates/wazuh-1.pem /etc/wazuh-dashboard/certs/dashboard.pem",
"cp wazuh-certificates/wazuh-1-key.pem /etc/wazuh-dashboard/certs/dashboard-key.pem",
"cp wazuh-certificates/root-ca.pem /etc/wazuh-indexer/certs/",
"cp wazuh-certificates/root-ca.pem /etc/filebeat/certs/",
"cp wazuh-certificates/root-ca.pem /etc/wazuh-dashboard/certs/",
"chmod 500 -R /etc/wazuh-indexer/certs",
"chmod 500 -R /etc/wazuh-dashboard/certs",
"chmod 500 -R /etc/filebeat/certs",
"chmod go+r /etc/filebeat/wazuh-template.json",
"filebeat keystore create",
"echo admin | filebeat keystore add username --stdin --force",
"echo admin | filebeat keystore add password --stdin --force",
"chown -R wazuh-indexer:wazuh-indexer /etc/wazuh-indexer/certs",
"chown -R root:root /etc/filebeat/certs",
"chown -R wazuh-dashboard:wazuh-dashboard /etc/wazuh-dashboard/certs",
"sed -i 's/${username}/admin/g' /etc/filebeat/filebeat.yml",
"sed -i 's/${password}/admin/g' /etc/filebeat/filebeat.yml",
"sed -i 's/#opensearch\.username:/opensearch\.username: admin/g' /etc/wazuh-dashboard/opensearch_dashboards.yml",
"sed -i 's/#opensearch\.password:/opensearch\.password: admin/g' /etc/wazuh-dashboard/opensearch_dashboards.yml",
"sed -i 's/127\.0\.0\.1:9200/siem\.bykea\.dev:9200/g' etc/filebeat/filebeat.yml"
]

for cmd in cmds:
    result=Indexer.exec_run(cmd=cmd)
    print(f"[{result.exit_code}] "+cmd)
    print(result.output)

#result=Indexer.exec_run(user="wazuh-indexer",detach=True,cmd=f"/usr/share/wazuh-indexer/bin/systemd-entrypoint")
#print(result.output)
#print(result.exit_code)
#time.sleep(30)
#result=Indexer.exec_run(cmd=f"./usr/share/wazuh-indexer/bin/indexer-security-init.sh")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(cmd=f"./etc/init.d/wazuh-manager start")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(cmd=f"./etc/init.d/filebeat start")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(user="wazuh-dashboard",detach=True,cmd=f"/usr/share/wazuh-dashboard/bin/opensearch-dashboards -e https://127.0.0.1:9200 -p 55001 -H 0.0.0.0")
#print(result.output)
#print(result.exit_code)