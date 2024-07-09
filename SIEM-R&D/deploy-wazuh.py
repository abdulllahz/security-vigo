import docker
import time
import os
client = docker.from_env()
project_prefix = 'wazuh'
#deluge_downloads='/home/anon/Misc/deluge/downloads:/downloads'
thisdir=os.getcwd()
api_configuration=      f'{thisdir}/wazuh_volume/api_config:/var/ossec/api/configuration'
etc=                    f'{thisdir}/wazuh_volume/etc:/var/ossec/etc'
logs=                   f'{thisdir}/wazuh_volume/logs:/var/ossec/logs'
queue=                  f'{thisdir}/wazuh_volume/queue:/var/ossec/queue'
var_multigroups=        f'{thisdir}/wazuh_volume/var_multigroups:/var/ossec/var/multigroups'
integrations=           f'{thisdir}/wazuh_volume/integrations:/var/ossec/integrations'
active_response=        f'{thisdir}/wazuh_volume/active_response:/var/ossec/active-response/bin'
agentless=              f'{thisdir}/wazuh_volume/agentless:/var/ossec/agentless'
wodles=                 f'{thisdir}/wazuh_volume/wodles:/var/ossec/wodles'
fb_etc=                 f'{thisdir}/wazuh_volume/filebeat_etc:/etc/filebeat'
fb_var=                 f'{thisdir}/wazuh_volume/filebeat_var:/var/lib/filebeat'
config_certs=           f'{thisdir}/wazuh_volume/ymls/certs.yml:/config/certs.yml'
config_wazuh=           f'{thisdir}/wazuh_volume/ymls/wazuh.yml:/wazuh-config-mount/data/wazuh/config/wazuh.yml'
indexer_data=           f'{thisdir}/wazuh_volume/wazuh-indexer-data:/var/lib/wazuh-indexer'
config_dashboard=       f'{thisdir}/wazuh_volume/dashboard_config:/usr/share/wazuh-dashboard/data/wazuh/config'
assets_dashboard=       f'{thisdir}/wazuh_volume/assets:/usr/share/wazuh-dashboard/plugins/wazuh/public/assets/custom'
config_manager=         f'{thisdir}/wazuh_volume/config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf'
certificates=           f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/:/certificates/'
indexer_root=           f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-indexer/certs/root-ca.pem'
manager_root=           f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/root-ca-manager.pem:/etc/ssl/root-ca.pem'
dashboard_root=         f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/root-ca.pem:/usr/share/wazuh-dashboard/certs/root-ca.pem'
certificates_manager=   f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.manager.pem:/etc/ssl/filebeat.pem'
certificates_indexer=   f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.indexer.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.pem'
certificates_dashboard= f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.dashboard.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard.pem'
certificates_admin=     f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/admin.pem:/usr/share/wazuh-indexer/certs/admin.pem'
key_indexer=            f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.indexer-key.pem:/usr/share/wazuh-indexer/certs/wazuh.indexer.key'
key_manager=            f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.manager-key.pem:/etc/ssl/filebeat.key'
key_dashboard=          f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/wazuh.dashboard-key.pem:/usr/share/wazuh-dashboard/certs/wazuh-dashboard-key.pem'
key_admin=              f'{thisdir}/wazuh_volume/config/wazuh_indexer_ssl_certs/admin-key.pem:/usr/share/wazuh-indexer/certs/admin-key.pem'
#volumes = [
#	"/home/anon/Misc/source:/root/source",
#	"/home/anon/Misc/keys:/root/.ssh"
#]
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
network_name=project_prefix+'_network'
network = client.networks.create(network_name, driver='bridge')
##################################################################
GenCert= client.containers.run(
        name= project_prefix+'.GenCert',
        image='wazuh/wazuh-certs-generator:0.0.2',
        command='./entrypoint.sh',
        detach=True,
        network=network_name,
        volumes=[certificates,config_certs]
    )
time.sleep(30)
Indexer= client.containers.run(
        name= project_prefix+'.Indexer',
        image='wazuh/wazuh-indexer:4.8.0',
        command='./entrypoint.sh',
        detach=True,
        ports={'9200':9200},
        environment={
            'OPENSEARCH_JAVA_OPTS': '-Xms1g -Xmx1g',
            'bootstrap.memory_lock': 'true',
            'NODE_NAME': 'wazuh.indexer',
            'CLUSTER_INITIAL_MASTER_NODES': 'wazuh.indexer',
            'CLUSTER_NAME': 'wazuh-cluster',
            'PATH_DATA': '/var/lib/wazuh-indexer',
            'PATH_LOGS': '/var/log/wazuh-indexer',
            'HTTP_PORT': '9200-9299',
            'TRANSPORT_TCP_PORT': '9300-9399',
            'COMPATIBILITY_OVERRIDE_MAIN_RESPONSE_VERSION': 'true',
            'PLUGINS_SECURITY_SSL_HTTP_PEMCERT_FILEPATH': '/usr/share/wazuh-indexer/certs/wazuh.indexer.pem',
            'PLUGINS_SECURITY_SSL_HTTP_PEMKEY_FILEPATH': '/usr/share/wazuh-indexer/certs/wazuh.indexer.key',
            'PLUGINS_SECURITY_SSL_HTTP_PEMTRUSTEDCAS_FILEPATH': '/usr/share/wazuh-indexer/certs/root-ca.pem',
            'PLUGINS_SECURITY_SSL_TRANSPORT_PEMCERT_FILEPATH': '/usr/share/wazuh-indexer/certs/wazuh.indexer.pem',
            'PLUGINS_SECURITY_SSL_TRANSPORT_PEMKEY_FILEPATH': '/usr/share/wazuh-indexer/certs/wazuh.indexer.key',
            'PLUGINS_SECURITY_SSL_TRANSPORT_PEMTRUSTEDCAS_FILEPATH': '/usr/share/wazuh-indexer/certs/root-ca.pem',
            'PLUGINS_SECURITY_SSL_HTTP_ENABLED': 'true',
            'PLUGINS_SECURITY_SSL_TRANSPORT_ENFORCE_HOSTNAME_VERIFICATION': 'false',
            'PLUGINS_SECURITY_SSL_TRANSPORT_RESOLVE_HOSTNAME': 'false',
            'PLUGINS_SECURITY_AUTHCZ_ADMIN_DN': 'CN=admin,OU=Wazuh,O=Wazuh,L=California,C=US',
            'PLUGINS_SECURITY_CHECK_SNAPSHOT_RESTORE_WRITE_PRIVILEGES': 'true',
            'PLUGINS_SECURITY_ENABLE_SNAPSHOT_RESTORE_PRIVILEGE': 'true',
            'PLUGINS_SECURITY_NODES_DN': 'CN=wazuh.indexer,OU=Wazuh,O=Wazuh,L=California,C=US',
            'PLUGINS_SECURITY_RESTAPI_ROLES_ENABLED': '[\'all_access\', \'security_rest_api_access\']',
            'PLUGINS_SECURITY_SYSTEM_INDICES_ENABLED': 'true',
            'PLUGINS_SECURITY_SYSTEM_INDICES_INDICES': '[\'.opendistro-alerting-config\', \'.opendistro-alerting-alert*\', \'.opendistro-anomaly-results*\', \'.opendistro-anomaly-detector*\', \'.opendistro-anomaly-checkpoints\', \'.opendistro-anomaly-detection-state\', \'.opendistro-reports-*\', \'.opendistro-notifications-*\', \'.opendistro-notebooks\', \'.opensearch-observability\', \'.opendistro-asynchronous-search-response*\', \'.replication-metadata-store\']',
            'PLUGINS_SECURITY_ALLOW_DEFAULT_INIT_SECURITYINDEX': 'true',
            'CLUSTER_ROUTING_ALLOCATION_DISK_THRESHOLD_ENABLED': 'false'
        },
        network=network_name,
        volumes=[indexer_data,indexer_root,key_indexer,certificates_indexer,certificates_admin,key_admin]
    )
Manager= client.containers.run(
        name= project_prefix+'.Manager',
        image='wazuh/wazuh-manager:4.8.0',
        command='tail -f /dev/null',
        detach=True,
        ports={
            '1514/tcp':1514,
            '1515/tcp':1515,
            '514/udp':514,
            '55000/tcp':55000
        },
        environment={
            'INDEXER_URL': f'https://{project_prefix+".Indexer"}:9200',
            'INDEXER_USERNAME': 'admin',
            'INDEXER_PASSWORD': 'admin',
            'FILEBEAT_SSL_VERIFICATION_MODE': 'full',
            'SSL_CERTIFICATE_AUTHORITIES': '/etc/ssl/root-ca.pem',
            'SSL_CERTIFICATE': '/etc/ssl/filebeat.pem',
            'SSL_KEY': '/etc/ssl/filebeat.key',
            'API_USERNAME': 'wazuh-wui',
            'API_PASSWORD': 'MyS3cr37P450r.*-'
        },
        network=network_name,
        volumes=[
            api_configuration,
            etc,
            logs,
            queue,
            var_multigroups,
            integrations,
            active_response,
            agentless,
            wodles,
            fb_etc,
            fb_var,
            manager_root,
            certificates_manager,
            key_manager,
            config_manager
        ]
    )
Dashboard= client.containers.run(
        name= project_prefix+'.Dashboard',
        image='wazuh/wazuh-dashboard:4.8.0',
        command='tail -f /dev/null',
        detach=True,
        ports={'443/tcp':5601},
        environment={
            'WAZUH_API_URL': f'https://{project_prefix+".Manager"}',
            'OPENSEARCH_HOSTS': f'https://{project_prefix+".Indexer"}:9200',
            'DASHBOARD_USERNAME': 'kibanaserver',
            'DASHBOARD_PASSWORD': 'kibanaserver',
            'API_USERNAME': 'wazuh-wui',
            'API_PASSWORD': 'MyS3cr37P450r.*-',
            'SERVER_HOST': '0.0.0.0',
            'SERVER_PORT': '5601',
            'OPENSEARCH_SSL_VERIFICATIONMODE': 'certificate',
            'OPENSEARCH_REQUESTHEADERSALLOWLIST': '["securitytenant","Authorization"]',
            'OPENSEARCH_SECURITY_MULTITENANCY_ENABLED': '"false"',
            'SERVER_SSL_ENABLED': '"true"',
            'OPENSEARCH_SECURITY_READONLY_MODE_ROLES': '["kibana_read_only"]',
            'SERVER_SSL_KEY': '"/usr/share/wazuh-dashboard/certs/wazuh-dashboard-key.pem"',
            'SERVER_SSL_CERTIFICATE': '"/usr/share/wazuh-dashboard/certs/wazuh-dashboard.pem"',
            'OPENSEARCH_SSL_CERTIFICATEAUTHORITIES': '["/usr/share/wazuh-dashboard/certs/root-ca.pem"]',
            'UISETTINGS_OVERRIDES_DEFAULTROUTE': '/app/wz-home'
        },
        network=network_name,
        volumes=[
            api_configuration,
            etc,
            logs,
            queue,
            var_multigroups,
            integrations,
            active_response,
            agentless,
            wodles,
            fb_etc,
            fb_var,
            manager_root,
            certificates_manager,
            key_manager,
            config_manager
        ]
    )
#result=workspace["indexer"].exec_run(cmd="curl -sO https://packages.wazuh.com/4.8/wazuh-certs-tool.sh")
#result=workspace["indexer"].exec_run(cmd="curl -sO https://packages.wazuh.com/4.8/config.yml")
#result=workspace["indexer"].exec_run(cmd=f"sed -i 's/<indexer-node-ip>/{project_prefix+'_indexer'}/g' config.yml")
#result=workspace["indexer"].exec_run(cmd=f"sed -i 's/<wazuh-manager-ip>/{project_prefix+'_manager'}/g' config.yml")
#result=workspace["indexer"].exec_run(cmd=f"sed -i 's/<dashboard-node-ip>/{project_prefix+'_manager'}/g' config.yml")
#result=workspace["indexer"].exec_run(cmd=f"bash ./wazuh-certs-tool.sh -A")
#result=workspace["indexer"].exec_run(cmd=f"tar -cvf ./wazuh-certificates.tar -C ./wazuh-certificates/ .")
#result=workspace["indexer"].exec_run(cmd=f"rm -rf ./wazuh-certificates")
#result=workspace["indexer"].exec_run(cmd=f"apt-get install debconf adduser procps gnupg apt-transport-https")
#result=workspace["indexer"].exec_run(cmd=f"""
#    curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | \\
#    gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import && \\
#    chmod 644 /usr/share/keyrings/wazuh.gpg""")
#result=workspace["indexer"].exec_run(cmd=f"""
#    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | \\
#    tee -a /etc/apt/sources.list.d/wazuh.list""")
#result=workspace["indexer"].exec_run(cmd="apt-get update")
#result=workspace["indexer"].exec_run(cmd="apt-get -y install wazuh-indexer")