import fileinput
import re
from enum import Enum, auto
from os import getenv
from os.path import isfile
from typing import Iterator, NamedTuple, List, Optional

import docker
from docker import DockerClient
from docker.models.containers import Container


class ContainerIp(NamedTuple):
    name: str
    ip: str


class ReplaceStatus(Enum):
    NOT_MATCH = auto()
    SKIPPED = auto()
    REPLACED = auto()


def _map_container(docker_containers: Iterator[Container]) -> List[ContainerIp]:
    ret: List[ContainerIp] = []
    ip: str
    for c in docker_containers:
        networks: dict = c.attrs.get('NetworkSettings', {}).get('Networks', {})
        for network_name in networks:
            ip = networks.get(network_name, {}).get('IPAddress')
            if not ip:
                continue
            ret.append(ContainerIp(c.name, ip))
    return ret


def _get_containers() -> List[ContainerIp]:
    client: DockerClient = docker.from_env()
    docker_containers: Iterator[Container] = client.containers.list(filters={'status': 'running'})
    docker_containers = filter(lambda c: '80/tcp' in c.ports, docker_containers)
    return _map_container(docker_containers)


def _replace_item(obj: dict, key: str, replace_value: str):
    for k, v in obj.items():
        if isinstance(v, dict):
            obj[k] = _replace_item(v, key, replace_value)
    if key in obj:
        obj[key] = replace_value
    return obj


def _replace_nginx_conf(containers: List[ContainerIp]) -> (list, list):
    success: List[ContainerIp] = []
    skip: List[ContainerIp] = []
    regex_search = re.compile(r'(proxy_pass[\s+]http://)([^;]+);')
    for c in containers:
        nginx_conf_file = nginx_dir + c.name + '.conf'
        if not isfile(nginx_conf_file):
            print("{} doesn't existed".format(nginx_conf_file))
            continue
        line: str
        for line in fileinput.input(nginx_conf_file, inplace=True):
            line, status = _replace_line(c, line, regex_search)
            if status == ReplaceStatus.SKIPPED:
                skip.append(c)
            elif status == ReplaceStatus.REPLACED:
                success.append(c)
            print(line, end='')
    return success, skip


def _replace_line(c: ContainerIp, line: str, regex_search: re.Pattern) -> (str, ReplaceStatus):
    match = re.search(regex_search, line)
    status = ReplaceStatus.NOT_MATCH
    if match:
        old_ip = match.group(2)
        if old_ip:
            if old_ip == c.ip:
                status = ReplaceStatus.SKIPPED
            else:
                line = re.sub(regex_search, r'\g<1>{};'.format(c.ip), line)
                status = ReplaceStatus.REPLACED
    return line, status


if __name__ == '__main__':
    nginx_dir: Optional[str] = getenv('DONIK_NGINX_DIR')
    if not nginx_dir:
        exit("Please set DONIK_NGINX_DIR")
    nginx_dir = nginx_dir.rstrip('/') + '/'
    containers = _get_containers()
    success, skip = _replace_nginx_conf(containers)
    for s in success:
        print("Set '{}': '{}'".format(s.name, s.ip))
    for s in skip:
        print("Skip '{}': '{}'".format(s.name, s.ip))
