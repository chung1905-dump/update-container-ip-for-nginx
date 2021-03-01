import docker
from docker import DockerClient
from docker.models.containers import Container
from typing import Optional, Iterator


def filter_http_container(c: Container) -> bool:
    for i in c.ports:
        ports: Optional[list] = c.ports.get(i)
        if ports is None:
            continue
        if int(ports.pop().get('HostPort')) == 80:
            return True
    return False


if __name__ == '__main__':
    client: DockerClient = docker.from_env()
    containers: Iterator[Container] = client.containers.list()
    containers = filter(filter_http_container, containers)
    for container in containers:
        networks: dict = container.attrs.get('NetworkSettings').get('Networks')
        for network_name in networks:
            print(network_name)
            print(networks.get(network_name).get('IPAddress'))
