import asyncio
import tarfile
import docker
import time
import os
import io
#<130>1 2024-10-28 10:31:07 aaaaaaaa KongHTTP PID a1bf4b20-adf8-4a35-a282-b953cd6c998e body={"__SId":"aaaaaaaa"}

### Variables
client = docker.from_env()
cur_dir = os.getcwd()
project_prefix = 'wazuh'
script_version = '4.8.1-1'
agent_url = f'https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_{script_version}_amd64.deb'
path = '/home/wazuh_files/'
certpath = f'{path}/wazuh-certificates'
### Credentials
username =            "admin"
password =            "admin"
indexerKib_username = ""
indexerKib_password = ""
indexerAdm_username = "admin"
indexerAdm_password = "admin"
managerApi_username = ""
managerApi_password = ""
managerWUI_username = "wazuh-wui"
managerWUI_password = "wazuh-wui"
### Host/Ports
indexer_host =      "wazuh.indexer"
manager_host =      "wazuh.manager"
dashboard_host =    "wazuh.dashboard"
dashboard_port =    "443"
indexer_port =      "9200"
manager_port =      "55000"
manager_agent_port= "1514"
manager_syslog_port= "514"
forwarder_port =    "7799"

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
        result_tmp=c['m'].exec_run(user="root",cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'i:':
        result_tmp=c['i'].exec_run(user="root",cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'd:':
        result_tmp=c['d'].exec_run(user="root",cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    if e[0:2] == 'f:':
        result_tmp=c['f'].exec_run(user="root",cmd=e[2:])
        result["exit_code"]=result["exit_code"]|result_tmp.exit_code
        result["output"]=str(result["output"])+str(result_tmp.output)
        return result
    return
def push_file_to_container(container, content, target_dir, file_name, params):
    temp = open(content,'r')
    filestr = temp.read()
    temp.close()
    if {}!=params:
        filestr=filestr.format(**params)
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        file_data = io.BytesIO(filestr.encode('utf-8'))
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(file_data.getvalue())
        tar.addfile(tarinfo, file_data)
    tar_stream.seek(0)
    #tar_stream = create_tarfile_from_string(file_name, content)
    container.put_archive(path=target_dir, data=tar_stream)
def push_folder(container,directory,target):
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            temp=open(path,'r')
            push_file_to_container(container,path,target,filename,{})
    return True
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
##################################################################
async def main():
    cmds=[
# Prepration
        f"a:apt update",
        f"a:apt install -y curl lsof gawk procps libcap2-bin lsb-release wget",
        f"f:curl {agent_url} -o /wazuh-agent_{script_version}_amd64.deb",
        f"f:/usr/share/logstash/bin/logstash-plugin install logstash-output-syslog"
        f"m:mkdir -p /usr/share/filebeat/module",
        f"d:mkdir -p /usr/share/wazuh-dashboard/data/wazuh/config/",
        f"a:chmod 777 /wazuh-install.sh",
        f"a:/wazuh-install.sh -dw deb",
        f"a:tar -xzf wazuh-offline.tar.gz",
        f"m:tar -xzf wazuh-offline/wazuh-files/wazuh-filebeat-0.4.tar.gz -C /usr/share/filebeat/module",
        f"f:dpkg -i /wazuh-agent_{script_version}_amd64.deb",
        f"i:dpkg -i /wazuh-offline/wazuh-packages/wazuh-indexer_{script_version}_amd64.deb",
        f"d:dpkg -i /wazuh-offline/wazuh-packages/wazuh-dashboard_{script_version}_amd64.deb",
        f"m:dpkg -i /wazuh-offline/wazuh-packages/wazuh-manager_{script_version}_amd64.deb",
        f"m:dpkg -i /wazuh-offline/wazuh-packages/filebeat-oss-7.10.2-amd64.deb",
        f"m:mkdir /etc/filebeat/certs",
        f"i:mkdir /etc/wazuh-indexer/certs",
        f"d:mkdir /etc/wazuh-dashboard/certs",
#        f"f:mkdir /var/ossec",
#        f"f:mkdir /var/ossec/etc",
###################################################################
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
###################################################################
# Permission control          
        f"i:chmod 500 -R                                          /etc/wazuh-indexer/certs",
        f"i:chown -R wazuh-indexer:wazuh-indexer                  /etc/wazuh-indexer/certs",
        f"d:chmod 500 -R                                          /etc/wazuh-dashboard/certs",
        f"d:chown -R wazuh-dashboard:wazuh-dashboard              /etc/wazuh-dashboard/certs",
        f"m:chmod 500 -R                                          /etc/filebeat/certs",
        f"m:chown -R root:root                                    /etc/filebeat/certs",
        f"m:chmod go+r                                            /etc/filebeat/wazuh-template.json",
        f"m:chmod 777 -R                                          /var/ossec/ruleset/decoders/",
        f"m:chmod 777 -R                                          /var/ossec/ruleset/rules/",
        f"m:chmod 777 -R                                          /var/ossec/ruleset/sca/",
###################################################################
# Save creds in manager
        f"m:/var/ossec/bin/wazuh-keystore -f indexer -k username -v {indexerAdm_username}",
        f"m:/var/ossec/bin/wazuh-keystore -f indexer -k password -v {indexerAdm_password}",
###################################################################
# Save creds in filebeat
        f"m:filebeat keystore create",
        f"m:echo {indexerAdm_username} | filebeat keystore add username --stdin --force",
        f"m:echo {indexerAdm_password} | filebeat keystore add password --stdin --force"]
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
                # '514/udp':514
            },
            network=network_name,
            volumes=[
                f"{cur_dir}/wazuh_volume/:{path}"
            ]
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
            volumes=[f"{cur_dir}/wazuh_volume/:{path}"],
            environment={
                'WAZUH_MANAGER':f'{manager_host}',
                'WAZUH_AGENT_GROUP':'default',
                'WAZUH_AGENT_NAME':'ForwarderAgent'
            }
    )
    containers_set={"i":Indexer,"m":Manager,"d":Server,"f":Forwarder}
###################################################################
# Files!
    push_file_to_container(Server,"wazuh-install.sh","/","wazuh-install.sh",{})
    push_file_to_container(Manager,"wazuh-install.sh","/","wazuh-install.sh",{})
    push_file_to_container(Indexer,"wazuh-install.sh","/","wazuh-install.sh",{})
    push_file_to_container(Forwarder,"wazuh-install.sh","/","wazuh-install.sh",{})
###################################################################
# Command Runners
    for cmd in cmds:
        result=cmd_run(containers_set,cmd)
        if result["exit_code"]!=0:
            print("=================================")
        print(f"[{result['exit_code']}] "+cmd)
        if result["exit_code"]!=0:
            print(result["output"])
            print("=================================")
###################################################################            
# More FILES
    push_file_to_container(Server,
        "dashboard_indexer.conf",
        "/etc/wazuh-dashboard/","opensearch_dashboards.yml", {
            "username":         indexerAdm_username,
            "password":         indexerAdm_password,
            "indexer_host":     indexer_host,
            "indexer_port":     indexer_port,
            "dashboard_port":   dashboard_port
    })
    push_file_to_container(Server, 
        "dashboard_manager.conf",
        "/usr/share/wazuh-dashboard/data/wazuh/config/","wazuh.yml", {
            "username":         managerWUI_username,
            "password":         managerWUI_password,
            "manager_host":     manager_host,
            "manager_port":     manager_port
    })
    push_file_to_container(Manager,
        "manager_indexer.conf", 
        "/etc/filebeat/", "filebeat.yml", {
            "username":         indexerAdm_username,
            "password":         indexerAdm_password,
            "indexer_host":     indexer_host,
            "indexer_port":     indexer_port
    })
    push_file_to_container(Forwarder, 
        "forwarder_manager.conf", 
        "/usr/share/logstash/pipeline/", "logstash.conf", {
            "forwarder_port":     forwarder_port,
            "manager_host":       manager_host,
            "manager_syslog_port": manager_syslog_port
    })
    push_file_to_container(Forwarder, 
        "manager_config.conf", 
        "/var/ossec/etc/", "ossec.conf", {
    })
    push_file_to_container(Forwarder, 
        "forwarder_agent.conf",
        "/var/ossec/etc/", "ossec.conf", {
            "manager_host":       manager_host,
            "manager_agent_port": manager_agent_port
    })
    push_folder(Manager,f"{cur_dir}/decoders",                      "/var/ossec/ruleset/decoders/")
    push_folder(Manager,f"{cur_dir}/rules",                         "/var/ossec/ruleset/rules/")
    push_folder(Manager,f"{cur_dir}/sca",                           "/var/ossec/ruleset/sca/")

###################################################################

#Post install commands
#result=Indexer.exec_run(user="wazuh-indexer",detach=True,cmd=f"/usr/share/wazuh-indexer/bin/systemd-entrypoint")
#print(result.output)
#print(result.exit_code)
#time.sleep(30)
#result=Indexer.exec_run(user="root",cmd=f"./usr/share/wazuh-indexer/bin/indexer-security-init.sh")
#print(result.output)
#print(result.exit_code)
#result=Manager.exec_run(user="root",cmd=f"./etc/init.d/wazuh-manager start")
#print(result.output)
#print(result.exit_code)
#result=Manager.exec_run(user="root",cmd=f"./etc/init.d/filebeat start")
#print(result.output)
#print(result.exit_code)
#result=Server.exec_run(user="wazuh-dashboard",detach=True,cmd=f"/usr/share/wazuh-dashboard/bin/opensearch-dashboards --allow-root -p 443 -H 0.0.0.0")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(user="logstash",cmd=f"logstash")
#print(result.output)
#print(result.exit_code)
#result=Indexer.exec_run(user="root",cmd=f"/var/ossec/bin/wazuh-control")
#print(result.output)
#print(result.exit_code)

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
