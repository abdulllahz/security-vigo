import time
import copy
import json
import sys
import os
# Load configs
# Example:
# sudo python3 environment.py envX-#service.bykea.dev
path='./config/'
base='./base/'
configs=[]
for file in [file for file in os.listdir(base) if file.endswith('.json') and file.startswith('base_')]:
    f=open(base+file,'r')
    configs.append(json.load(f))
    f.close()
for config in configs:
    for environment in sys.argv[1:]:
        stuff=copy.deepcopy(config)
        config_name=f'{environment}'
        config_name=config_name.replace('#service',config['name'])
        stuff['targets'][0]['target']=config_name
        stuff['name']=config_name
        for route in stuff['routes']:
            temp=route['name']
            route.update({
                'name':f'{temp}_{config["name"]}'
                #'hosts':[f'{config_name}']
            })
        f=open(path+f'enabled_{config_name}.json','w')
        f.write(json.dumps(stuff))
        f.close()
f=open(base+'internal_Kong.json','r')
kong=json.load(f)
f.close()
for environment in sys.argv[1:]:
    stuff={}
    stuff.update(kong)
    temp=environment.replace('#service','api')
    stuff['routes'][0]['name']=f'{temp}_ServiceMap'
    stuff['ServiceMap']['data']['base_url']=f'{temp}/'
    f=open(path+f'enabled_{temp}_Kong.json','w')
    f.write(json.dumps(stuff))
    f.close()