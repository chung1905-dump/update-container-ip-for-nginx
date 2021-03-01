from typing import Iterator, NamedTuple, List

import docker
from docker import DockerClient
from docker.models.containers import Container


class ContainerIp(NamedTuple):
    name: str
    ip: str


def _map_container() -> List[ContainerIp]:
    ret: List[ContainerIp] = []
    ip: str
    for container in docker_containers:
        networks: dict = container.attrs.get('NetworkSettings', {}).get('Networks', {})
        for network_name in networks:
            ip = networks.get(network_name, {}).get('IPAddress', None)
            if ip is None:
                continue
            ret.append(ContainerIp(container.name, ip))
    return ret


if __name__ == '__main__':
    client: DockerClient = docker.from_env()
    docker_containers: Iterator[Container] = client.containers.list(filters={'status': 'running'})
    docker_containers = filter(lambda c: '80/tcp' in c.ports, docker_containers)
    containers = _map_container()
    print(containers)
