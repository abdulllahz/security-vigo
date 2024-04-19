# Security Repo

Brief description of the project.

## API Gateway

![Workflow Diagram](figures/APIGatewayDiagram.png)

### Installation

Install python3-docker and then just run deploy.py!
It will take care of setting up containers, running migrations and performing necessary configuration.

### Components

#### Routes
This is the path that will match in the request itself.
You can use various filters to narrow down matches.
Like Protocol, Method, Url path and Headers.
Before configuring this you must configure services.
Routes belong to a service.

#### Plugins
This stage can consist of various different plugins.
One plugin is mandatory and that is the request transformation.
The reason for this is because we are using path based routing
and it is necessary to remove the service path prefix.
You may configure plugins on global, service or route levels.

#### Services
This is the service denomination denotes a set of routes.
Ideally irrelevant of where it resides a service ought to be a process.

#### Upsteams
The first thing that must be configured. 
You must provide a virtual hostname, used by a service.
The hostname will only be used internally.
This hostname must be used in the all the services for that upsteam.  

#### Targets
Targets are actual hosts that will be used as destinations for a request.
Targets belong to an upstream.
In a way all egress goes through upstream and is loadbalanced to targets.

### Project Layout

#### config
##### common.json
Contains all the settings that will be common across all services/routes/plugins.
##### service.json
Contains a set of routes belonging to a service.

#### deploy.py
The deployment script
- Loads all the jsons in the configuration
- cleans up residual containers
- create containers
- performs configuration based on definitions from config folder.