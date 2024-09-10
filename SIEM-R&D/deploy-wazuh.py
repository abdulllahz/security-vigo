import asyncio
import tarfile
import docker
import time
import os
import io
client = docker.from_env()
cur_dir = os.getcwd()
install = open('wazuh-install.sh', 'r')
#certgen = open('wazuh-certs-tool.sh', 'r')
install_str=install.read()
#certgen_str=certgen.read()
install.close()
#certgen.close()
project_prefix = 'wazuh'
script_version = '4.8.1-1'
username = 'admin'
password = 'admin'
path = '/home/wazuh_files/'
certpath = f'{path}/wazuh-certificates'
config=[
# Dashboards
"""
server.host: 0.0.0.0
server.port: 443
opensearch.hosts: https://wazuh.indexer:9200
opensearch.ssl.verificationMode: certificate
opensearch.username: admin
opensearch.password: admin
opensearch.requestHeadersAllowlist: ["securitytenant","authorization"]
opensearch_security.multitenancy.enabled: false
opensearch_security.readonly_mode.roles: ["kibana_read_only"]
server.ssl.enabled: true
server.ssl.key: "/etc/wazuh-dashboard/certs/dashboard-key.pem"
server.ssl.certificate: "/etc/wazuh-dashboard/certs/dashboard.pem"
opensearch.ssl.certificateAuthorities: ["/etc/wazuh-dashboard/certs/root-ca.pem"]
uiSettings.overrides.defaultRoute: /app/wz-home
""",
# Dashboards
"""
hosts:
  - default:
      url: https://wazuh.manager
      port: 55000
      username: wazuh-wui
      password: wazuh-wui
      run_as: false
""",
# Manager
f"""
output.elasticsearch:
  hosts: ["wazuh.indexer:9200"]
  protocol: https
  username: {username}
  password: {password}
  ssl.certificate_authorities:
    - /etc/filebeat/certs/root-ca.pem
  ssl.certificate: "/etc/filebeat/certs/filebeat.pem"
  ssl.key: "/etc/filebeat/certs/filebeat-key.pem"
setup.template.json.enabled: true
setup.template.json.path: '/etc/filebeat/wazuh-template.json'
setup.template.json.name: 'wazuh'
setup.ilm.overwrite: true
setup.ilm.enabled: false

filebeat.modules:
  - module: wazuh
    alerts:
      enabled: true
    archives:
      enabled: false

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

logging.metrics.enabled: false

seccomp:
  default_action: allow
  syscalls:
  - action: allow
    names:
    - rseq
""",
# Certgen
"""
nodes:
  # Wazuh indexer nodes
  indexer:
    - name: node-1
      ip: "wazuh.indexer"
    #- name: node-2
    #  ip: "<indexer-node-ip>"
    #- name: node-3
    #  ip: "<indexer-node-ip>"

  # Wazuh server nodes
  # If there is more than one Wazuh server
  # node, each one must have a node_type
  server:
    - name: wazuh-1
      ip: "wazuh.manager"
    #  node_type: master
    #- name: wazuh-2
    #  ip: "<wazuh-manager-ip>"
    #  node_type: worker
    #- name: wazuh-3
    #  ip: "<wazuh-manager-ip>"
    #  node_type: worker

  # Wazuh dashboard nodes
  dashboard:
    - name: dashboard
      ip: "wazuh.server"
"""
]
cmds=[
# Prepration
    f"apt update",
    f"apt install -y curl lsof gawk procps libcap2-bin lsb-release",
    f"mkdir -p /usr/share/filebeat/module",
    f"mkdir -p /usr/share/wazuh-dashboard/data/wazuh/config/",
    f"chmod 777 wazuh-install.sh",
    f"/wazuh-install.sh -dw deb",
    f"tar -xzf wazuh-offline.tar.gz",
    f"tar -xzf wazuh-offline/wazuh-files/wazuh-filebeat-0.4.tar.gz -C /usr/share/filebeat/module",
    f"dpkg -i /wazuh-offline/wazuh-packages/wazuh-indexer_{script_version}_amd64.deb",
    f"dpkg -i /wazuh-offline/wazuh-packages/wazuh-manager_{script_version}_amd64.deb",
    f"dpkg -i /wazuh-offline/wazuh-packages/wazuh-dashboard_{script_version}_amd64.deb",
    f"dpkg -i /wazuh-offline/wazuh-packages/filebeat-oss-7.10.2-amd64.deb",
    f"mkdir /etc/wazuh-indexer/certs",
    f"mkdir /etc/wazuh-dashboard/certs",
    f"mkdir /etc/filebeat/certs",
# Copy Certificates
    f"cp /wazuh-offline/wazuh-files/filebeat.yml            /etc/filebeat/",
    f"cp /wazuh-offline/wazuh-files/wazuh-template.json     /etc/filebeat/",
    f"cp {certpath}/root-ca.pem                             /etc/filebeat/certs/",
    f"cp {certpath}/wazuh-1.pem                             /etc/filebeat/certs/filebeat.pem",
    f"cp {certpath}/wazuh-1-key.pem                         /etc/filebeat/certs/filebeat-key.pem",
    f"cp {certpath}/node-1.pem                              /etc/wazuh-indexer/certs/indexer.pem",
    f"cp {certpath}/node-1-key.pem                          /etc/wazuh-indexer/certs/indexer-key.pem",
    f"cp {certpath}/admin-key.pem                           /etc/wazuh-indexer/certs/",
    f"cp {certpath}/admin.pem                               /etc/wazuh-indexer/certs/",
    f"cp {certpath}/root-ca.pem                             /etc/wazuh-indexer/certs/",
    f"cp {certpath}/wazuh-1.pem                             /etc/wazuh-dashboard/certs/dashboard.pem",
    f"cp {certpath}/wazuh-1-key.pem                         /etc/wazuh-dashboard/certs/dashboard-key.pem",
    f"cp {certpath}/root-ca.pem                             /etc/wazuh-dashboard/certs/",
# Permission control          
    f"chmod 500 -R                                          /etc/wazuh-indexer/certs",
    f"chown -R wazuh-indexer:wazuh-indexer                  /etc/wazuh-indexer/certs",
    f"chmod 500 -R                                          /etc/wazuh-dashboard/certs",
    f"chown -R wazuh-dashboard:wazuh-dashboard              /etc/wazuh-dashboard/certs",
    f"chmod 500 -R                                          /etc/filebeat/certs",
    f"chown -R root:root                                    /etc/filebeat/certs",
    f"chmod go+r                                            /etc/filebeat/wazuh-template.json",
# Save creds in manager
    f"/var/ossec/bin/wazuh-keystore -f indexer -k username -v {username}",
    f"/var/ossec/bin/wazuh-keystore -f indexer -k password -v {password}",
# Save creds in filebeat
    f"filebeat keystore create",
    f"echo admin | filebeat keystore add username --stdin --force",
    f"echo admin | filebeat keystore add password --stdin --force"
]
###################################################################
async def cmd_run(c,e):
    result=c.exec_run(cmd=e)
    if result.exit_code!=0:
        print("=================================")
    print(f"[{result.exit_code}] "+e)
    if result.exit_code!=0:
        print(result.output)
        print("=================================")
    return
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
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        # Create a file-like object from the string
        file_data = io.BytesIO(content.encode('utf-8'))
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(file_data.getvalue())
        tar.addfile(tarinfo, file_data)
    tar_stream.seek(0)
    #tar_stream = create_tarfile_from_string(file_name, content)
    container.put_archive(path=target_dir, data=tar_stream)
async def cleanup(client):
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
async def main():
    client = docker.from_env()
# Remove residual
    await cleanup(client)
##################################################################
# Create networks
    network_name=project_prefix+'_network'
    network = client.networks.create(network_name, driver='bridge')
##################################################################
    Indexer= client.containers.run(
            name= project_prefix+'.indexer',
            image='debian:sid-slim',
            command='tail -f /dev/null',
            detach=True,
            ports={"9200/tcp": 9200,**{f"{port}/tcp": port for port in range(9300, 9400)}},
            network=network_name,
            volumes=[f"{cur_dir}/wazuh_volume/:{path}"]
            #environment={'OPENSEARCH_JAVA_OPTS': '-Xms750m -Xmx750m'}
    )
    Manager= client.containers.run(
            name= project_prefix+'.manager',
            image='debian:sid-slim',
            command='tail -f /dev/null',
            detach=True,
            ports={
                # Server RESTful API
                '55000':55000,
                # Agent connection service
                '1514/tcp':1514,
                # Agent enrollment service
                '1515/tcp':1515,
                # Agent cluster daemon
                '1516/tcp':1516,
                # Syslog collection
                '514/tcp':514,
                # Agent connection service
                '1514/udp':1514,
                # Syslog collection
                '514/udp':514
            },
            network=network_name,
            volumes=[f"{cur_dir}/wazuh_volume/:{path}"]
            #environment={'OPENSEARCH_JAVA_OPTS': '-Xms750m -Xmx750m'}
    )
    Server= client.containers.run(
            name= project_prefix+'.server',
            image='debian:sid-slim',
            command='tail -f /dev/null',
            detach=True,
            ports={
                '443':443
            },
            network=network_name,
            volumes=[f"{cur_dir}/wazuh_volume/:{path}"]
            #environment={'OPENSEARCH_JAVA_OPTS': '-Xms750m -Xmx750m'}
    )

    push_string_to_container(Server,"wazuh-install.sh",          install_str,"/")
#    push_string_to_container(Server,"wazuh-certs-tool.sh",       certgen_str,"/")
    push_string_to_container(Manager,"wazuh-install.sh",         install_str,"/")
#    push_string_to_container(Manager,"wazuh-certs-tool.sh",      certgen_str,"/")
    push_string_to_container(Indexer,"wazuh-install.sh",         install_str,"/")
#    push_string_to_container(Indexer,"wazuh-certs-tool.sh",      certgen_str,"/")
    for cmd in cmds:
        await asyncio.gather(
            cmd_run(Indexer,cmd),
            cmd_run(Server,cmd),
            cmd_run(Manager,cmd)
        )
    push_string_to_container(Manager,"filebeat.yml",            config[2],"/etc/filebeat/")
    push_string_to_container(Server,"opensearch_dashboards.yml",config[0],"/etc/wazuh-dashboard/")
    push_string_to_container(Server,"wazuh.yml",                config[1],"/usr/share/wazuh-dashboard/data/wazuh/config/")
    
#result=Indexer.exec_run(user="wazuh-indexer",detach=True,cmd=f"/usr/share/wazuh-indexer/bin/systemd-entrypoint")
#print(result.output)
#print(result.exit_code)
#time.sleep(30)
#result=Indexer.exec_run(cmd=f"./usr/share/wazuh-indexer/bin/indexer-security-init.sh")
#print(result.output)
#print(result.exit_code)
#result=Manager.exec_run(cmd=f"./etc/init.d/wazuh-manager start")
#print(result.output)
#print(result.exit_code)
#result=Manager.exec_run(cmd=f"./etc/init.d/filebeat start")
#print(result.output)
#print(result.exit_code)
#result=Server.exec_run(user="wazuh-dashboard",detach=True,cmd=f"/usr/share/wazuh-dashboard/bin/opensearch-dashboards --allow-root -p 443 -H 0.0.0.0")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(cmd=f"wazuh-offline/wazuh-files/wazuh-template.json")
#print(result.output)
#print(result.exit_code)
# Do this after a startup.
# 

# Notes!
# Overview: Meaningless
# Disover: Query
# Dashboards: Dataview
# Visualization: Dataview
# Reports: Automated reporting
# Alerting: Anomaly detction
# Notifications: Chat & Email notifcations
# Endpoint: Dashboard, Inventory, Events
# File integrity: Dashboard, Inventory, Events
# Malware: Dashboard, Events

# Wazuh agent Ports: (1514, 1515, 514) public to org
# Wazuh Manager Ports: (1516) only to Wazuh manager ASG
# Wazuh Manager Rest: (55000) only to Wazuh cluster
# Wazuh Indexer Rest: (9200) only to Wazuh cluster
# Wazuh Indexer Cluster: (9300-9400) only to Wazuh Indexer ASG
# Wazuh Dashboad: (443) public to org
asyncio.run(main())