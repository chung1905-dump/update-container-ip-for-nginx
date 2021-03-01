from typing import Iterator

import docker
from docker import DockerClient
from docker.models.containers import Container

if __name__ == '__main__':
    client: DockerClient = docker.from_env()
    containers: Iterator[Container] = client.containers.list(filters={'status': 'running'})
    containers = filter(lambda c: '80/tcp' in c.ports, containers)
    for container in containers:
        networks: dict = container.attrs.get('NetworkSettings', {}).get('Networks', {})
        for network_name in networks:
            print(network_name)
            print(networks.get(network_name, {}).get('IPAddress', {}))
