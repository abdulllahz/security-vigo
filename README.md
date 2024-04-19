# Security Repo

Brief description of the project.

## API Gateway

![Workflow Diagram](figures/APIGatewayDiagram.png)

- [Installation](#installation)

Install python3-docker and then just run deploy.py!

It will take care of setting up containers, running migrations and performing nessecary configuration.

- [Upsteam](#upsteam)

The first thing that must be configured. You must provide a virtual hostname, used by a service. The hostname will only be used internally.

This hostname must be used in the all the services for that upsteam. Targets are actual hosts that will be used as destinations for a request.

In a way all egress goes through upstream and is loadbalanced to targets. 

- [Diagrams](#diagrams)


- [Contributing](#contributing)
- [License](#license)