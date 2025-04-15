from typer import Typer
import httpx
import re
import base64
from os import environ as env
from urllib.parse import urlencode
from prettytable import PrettyTable
import yaml
import logging
import subprocess

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = Typer()

def get_image_tags():
    url = f"https://{env['ALIYUN_REGISTRY']}/v2/{env['ALIYUN_NAME_SPACE']}/tags/list"
    response = httpx.get(url)

    if response.status_code == 401:
        # 解析 Www-Authenticate 字段
        auth_header = response.headers.get('Www-Authenticate')
        match = re.search(r'realm="([^"]+)",service="([^"]+)",scope="([^"]+)"', auth_header)
        if match:
            realm, service, scope = match.groups()
            # 对用户名和密码进行 Base64 编码
            credentials = f"{env['ALIYUN_REGISTRY_USER']}:{env['ALIYUN_REGISTRY_PASSWORD']}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            # 设置请求头
            headers = {
                "Authorization": f"Basic {encoded_credentials}"
            }
            #scope = 'repository:{repository}:pull'
            # 向认证服务请求 Token
            token_url = f"{realm}?"+urlencode({'service': service, 'scope': scope})
            logger.debug(f"Token 请求 URL: {token_url}")
            token_response = httpx.get(token_url, headers=headers)
            if token_response.status_code == 200:
                logger.debug(f"Token 请求成功: {token_response.json()}")
                token = token_response.json().get('token')
                logger.debug(f"获取到的 Token: {token}")
                # 使用 Token 发起请求
                headers = {
                    "Content-Type": "application/json; charset=utf-8",
                    "Docker-Distribution-Api-Version": "registry/2.0",
                    "Authorization": f"Bearer {token}"
                }
                response = httpx.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data["tags"]
                else:
                    logger.error(f"请求失败，状态码: {response.status_code}")
            else:
                logger.error(f"获取 Token 失败，状态码: {token_response.status_code}")
    else:
        logger.error(f"请求失败，状态码: {response.status_code}")

def parse_image(image_name):
    if ':' in image_name:
        prefix, tag = image_name.rsplit(':', 1)
    else:
        prefix = image_name
        tag = None
    parts = prefix.split('/')
    if len(parts) == 1:
        registry = 'docker.io'
        namespace = 'library'
        name = parts[0]
    elif len(parts) == 2:
        registry = 'docker.io'
        namespace = parts[0]
        name = parts[1]
    elif len(parts) == 3:
        registry = parts[0]
        namespace = parts[1]
        name = parts[2]
    return {
        'name': image_name,
        'registry': registry,
        'namespace': namespace,
        'repository': name,
        'tag': tag if ':' in image_name else None
    }

def get_image_tag(image):
    if image['tag']:
        name = f"{image['repository']}-{image['tag']}"
    else:
        name = image['repository']
    if image['namespace'] == 'bitnami':
        name = f"{image['namespace']}-{name}"
    return [
        name,
        image.get('alias'),
        f"{image['namespace']}-{name}", 
        f"{image['registry']}-{image['namespace']}-{name}"
    ]

def push_image(image, tag, dry_run):
    logger.info(f"push image {image['name']} with tag {tag}")
    if dry_run:
        return
    full_name = f"{env['ALIYUN_REGISTRY']}/{env['ALIYUN_NAME_SPACE']}:{tag}"
    # TODO: 支持 platform 参数
    commands = f"""
    docker pull {image['name']}
    docker tag {image['name']} {full_name}
    docker push {full_name}
    docker rmi {image['name']}
    docker rmi {full_name}
    """

    # 执行命令，将输出直接输出到当前的 stdout 和 stderr
    try:
        subprocess.run(['bash', '-c', commands], check=True)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败，返回码: {e.returncode}")

@app.command()
def list():
    tags = get_image_tags()
    for tag in tags:
        print(f"{env['ALIYUN_REGISTRY']}/{env['ALIYUN_NAME_SPACE']}:{tag}")

@app.command()
def push(dry_run: bool = False):
    table = PrettyTable()
    table.align = "l"
    table.field_names = ["image_name", "tag"]
    tags = get_image_tags()
    seen = {}

    with open('images.yaml', 'r') as file:
        images = yaml.safe_load(file)
        for image in images:
            image.update(parse_image(image['name']))
            for tag in get_image_tag(image):
                if not tag:
                    continue
                if tag in tags:
                    if tag not in seen:
                        seen[tag] = image['name']
                        break
                    else:
                        continue
                else:
                    tags.append(tag)
                    seen[tag] = image['name']
                    push_image(image, tag, dry_run)
                    break
            if image['name'] not in seen.values():
                logger.error(f"image {image['name']} not pushed")
        for tag, name in seen.items():
            table.add_row([name, tag])
        print(table)
        
if __name__ == "__main__":
    app()