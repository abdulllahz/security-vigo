import asyncio
import tarfile
import docker
import time
import os
import io
client = docker.from_env()
cur_dir = os.getcwd()
install =               open("wazuh-install.sh", 'r')
dashboard_indexer =     open("dashboard_indexer.conf", 'r')
dashboard_manager =     open("dashboard_manager.conf", 'r')
manager_indexer =       open("manager_indexer.conf",'r')
preinstall_certgen =    open("preinstall_certgen.conf", 'r')
forwarder_manager =     open("forwarder_manager.conf", 'r')
kong_decoder =          open('rules/0171-KongHTTP_decoders.xml','r')
kong_rules =            open('rules/0261-KongHTTP_rules.xml','r')
#certgen = open('wazuh-certs-tool.sh', 'r')
install_str=            install.read()
dashboard_indexer_str=  dashboard_indexer.read()
dashboard_manager_str=  dashboard_manager.read()
manager_indexer_str=    manager_indexer.read()
preinstall_certgen_str= preinstall_certgen.read()
forwarder_manager_str=  forwarder_manager.read()
kong_decoder_str=       kong_decoder.read()
kong_rules_str=         kong_rules.read()
#certgen_str=certgen.read()
install                 .close()
dashboard_indexer       .close()
dashboard_manager       .close()
manager_indexer         .close()
preinstall_certgen      .close()
forwarder_manager       .close()
kong_decoder            .close()
kong_rules              .close()
#certgen.close()
project_prefix = 'wazuh'
script_version = '4.8.1-1'
path = '/home/wazuh_files/'
certpath = f'{path}/wazuh-certificates'
ui_username =       "admin"
ui_password =       "admin"
username =          "wazuh-wui"
password =          "wazuh-wui"
indexer_host =      "wazuh.indexer"
manager_host =      "wazuh.manager"
dashboard_host =    "wazuh.dashboard"
dashboard_port =    "443"
indexer_port =      "9200"
manager_port =      "55000"
forwarder_port =    "7799"

###################################################################
# Populate configuration
config=[
    # Dashboards
        dashboard_indexer_str.format(**{
            "username":         username,
            "password":         password,
            "indexer_host":     indexer_host,
            "indexer_port":     indexer_port,
            "dashboard_port":   dashboard_port
        }),
    # Indexer
        dashboard_indexer_str.format(**{
            "username":         ui_username,
            "password":         ui_password,
            "dashboard_port":   dashboard_port,
            "indexer_host":     indexer_host,
            "indexer_port":     indexer_port
        }),
    # Manager
        manager_indexer_str.format(**{
            "username":         username,
            "password":         password,
            "indexer_host":     indexer_host,
            "indexer_port":     indexer_port
        }),
    # Certgen
        preinstall_certgen_str.format(**{
            "indexer_host":     indexer_host,
            "manager_host":     manager_host,
            "dashboard_host":   dashboard_host,
        }),
    # Forwarder
        forwarder_manager_str.format(**{
            "forwarder_port":   forwarder_port
        })
]
cmds=[
    # Prepration
        f"a:apt update",
        f"a:apt install -y curl lsof gawk procps libcap2-bin lsb-release",
        f"m:mkdir -p /usr/share/filebeat/module",
        f"d:mkdir -p /usr/share/wazuh-dashboard/data/wazuh/config/",
        f"a:chmod 777 /wazuh-install.sh",
        f"a:/wazuh-install.sh -dw deb",
        f"a:tar -xzf wazuh-offline.tar.gz",
        f"m:tar -xzf wazuh-offline/wazuh-files/wazuh-filebeat-0.4.tar.gz -C /usr/share/filebeat/module",
        f"m:dpkg -i /wazuh-offline/wazuh-packages/wazuh-manager_{script_version}_amd64.deb",
        f"m:dpkg -i /wazuh-offline/wazuh-packages/filebeat-oss-7.10.2-amd64.deb",
        f"i:dpkg -i /wazuh-offline/wazuh-packages/wazuh-indexer_{script_version}_amd64.deb",
        f"d:dpkg -i /wazuh-offline/wazuh-packages/wazuh-dashboard_{script_version}_amd64.deb",
        f"m:mkdir /etc/filebeat/certs",
        f"i:mkdir /etc/wazuh-indexer/certs",
        f"d:mkdir /etc/wazuh-dashboard/certs",
    # Copy Certificates
        f"m:cp /wazuh-offline/wazuh-files/filebeat.yml            /etc/filebeat/",
        f"m:cp /wazuh-offline/wazuh-files/wazuh-template.json     /etc/filebeat/",
        f"m:cp {certpath}/root-ca.pem                             /etc/filebeat/certs/",
        f"m:cp {certpath}/wazuh-1.pem                             /etc/filebeat/certs/filebeat.pem",
        f"m:cp {certpath}/wazuh-1-key.pem                         /etc/filebeat/certs/filebeat-key.pem",
        f"i:cp {certpath}/node-1.pem                              /etc/wazuh-indexer/certs/indexer.pem",
        f"i:cp {certpath}/node-1-key.pem                          /etc/wazuh-indexer/certs/indexer-key.pem",
        f"i:cp {certpath}/admin-key.pem                           /etc/wazuh-indexer/certs/",
        f"i:cp {certpath}/admin.pem                               /etc/wazuh-indexer/certs/",
        f"i:cp {certpath}/root-ca.pem                             /etc/wazuh-indexer/certs/",
        f"d:cp {certpath}/wazuh-1.pem                             /etc/wazuh-dashboard/certs/dashboard.pem",
        f"d:cp {certpath}/wazuh-1-key.pem                         /etc/wazuh-dashboard/certs/dashboard-key.pem",
        f"d:cp {certpath}/root-ca.pem                             /etc/wazuh-dashboard/certs/",
    # Permission control          
        f"i:chmod 500 -R                                          /etc/wazuh-indexer/certs",
        f"i:chown -R wazuh-indexer:wazuh-indexer                  /etc/wazuh-indexer/certs",
        f"d:chmod 500 -R                                          /etc/wazuh-dashboard/certs",
        f"d:chown -R wazuh-dashboard:wazuh-dashboard              /etc/wazuh-dashboard/certs",
        f"m:chmod 500 -R                                          /etc/filebeat/certs",
        f"m:chown -R root:root                                    /etc/filebeat/certs",
        f"m:chmod go+r                                            /etc/filebeat/wazuh-template.json",
    # Save creds in manager
        f"m:/var/ossec/bin/wazuh-keystore -f indexer -k username -v {username}",
        f"m:/var/ossec/bin/wazuh-keystore -f indexer -k password -v {password}",
    # Save creds in filebeat
        f"m:filebeat keystore create",
        f"m:echo admin | filebeat keystore add username --stdin --force",
        f"m:echo admin | filebeat keystore add password --stdin --force"
]
###################################################################
# Helpers
def cmd_run(c,e):
    result={"exit_code":0,"output":""}
    if e[0:2] == 'a:':
        for l in c:
            result_tmp=c[l].exec_run(user="root",cmd=e[2:])
            result["exit_code"]=result["exit_code"]|result_tmp.exit_code
            result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'm:':
        result_tmp=c['m'].exec_run(cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'i:':
        result_tmp=c['i'].exec_run(cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'd:':
        result_tmp=c['d'].exec_run(cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'f:':
        result_tmp=c['f'].exec_run(cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
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
##################################################################
# Remove residual
    await cleanup(client)
##################################################################
# Create networks
    network_name=project_prefix+'_network'
    network = client.networks.create(network_name, driver='bridge')
##################################################################
# Run Containers
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
    Forwarder= client.containers.run(
            name= project_prefix+'.forwarder',
            image='logstash:7.17.24',
            command='tail -f /dev/null',
            detach=True,
            ports={
                '7799':7799
            },
            network=network_name,
            volumes=[f"{cur_dir}/wazuh_volume/:{path}"]
            #environment={'OPENSEARCH_JAVA_OPTS': '-Xms750m -Xmx750m'}
    )
    containers_set={"i":Indexer,"m":Manager,"d":Server,"f":Forwarder}
###################################################################
# Files!
    push_string_to_container(Server,"wazuh-install.sh",          install_str,"/")
    push_string_to_container(Manager,"wazuh-install.sh",         install_str,"/")
    push_string_to_container(Indexer,"wazuh-install.sh",         install_str,"/")
    push_string_to_container(Forwarder,"wazuh-install.sh",       install_str,"/")
# Command Runners
    for cmd in cmds:
        result=cmd_run(containers_set,cmd)
        #print(result)
        if result["exit_code"]!=0:
            print("=================================")
        print(f"[{result["exit_code"]}] "+cmd)
        if result["exit_code"]!=0:
            print(result["output"])
            print("=================================")
    
# More FILES
    push_string_to_container(Server,"opensearch_dashboards.yml",    config[0],"/etc/wazuh-dashboard/")
    push_string_to_container(Server,"wazuh.yml",                    config[1],"/usr/share/wazuh-dashboard/data/wazuh/config/")
    push_string_to_container(Manager,"filebeat.yml",                config[2],"/etc/filebeat/")
    push_string_to_container(Forwarder,"logstash.conf",             config[4],"/usr/share/logstash/pipeline/")
    push_string_to_container(Forwarder,"0171-KongHTTP_decoders.xml",kong_decoder_str,"/usr/share/logstash/pipeline/")
###################################################################

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

# TODOS:
# HTTP Logs
# DB Logs
# AWS Logs
# Git logs

