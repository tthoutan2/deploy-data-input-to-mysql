import os
import json
import tempfile

import hvac
import jenkins
import getpass

from fabric.api import run, local, lcd, settings, execute, abort, hosts, shell_env, hide
from fabric.api import env as fabric_env

import slackweb

slack_url = os.environ.get('SLACK_URL')
slack = slackweb.Slack(slack_url)

MSA_ECR = "120387605022.dkr.ecr.{region}.amazonaws.com"
MSA_NEXUS = "nexus.mmt.local:8085"

def test_input_mysql(app):
    print("test")

def prepare_app_build_environment(app, tag=None):
    repo_name = "mmt-server-{}".format(app)
    if not os.path.isdir(app):
        organization = "MyMusicTaste"
        full_repo_name = "{0}/{1}".format(organization, repo_name)
        ssh_url = "git@github.com:{0}.git".format(full_repo_name)

        print("Cloning {0} ...".format(full_repo_name))
        local("git clone {0} {1}".format(ssh_url, app), capture=True)

    with lcd(app):
        local('git checkout master')
        if tag is None:
            local('git pull origin master')
        else:
            local('git fetch --all --tags --prune')
            local('git checkout tags/{}'.format(tag))
    ## legacy : It will be removed soon ##
    #with lcd(app), settings(warn_only=True):
    #    local('pyenv virtualenv 3.6.1 {}'.format(repo_name))
    #    local('pyenv local {}'.format(repo_name))
    #    local("pip install -r requirements.txt")


def build_and_push_service(region, service, dockerfile_path, build_args=None, version="latest"):
    service_name = "mmt-server-{}".format(service)
    login_command = '$(aws ecr get-login --no-include-email --region {0})'
    # TODO INSANIC REGION
    local(login_command.format('ap-northeast-1'))
    ecr_uri = MSA_ECR.format(region=region)
    ecr_repo = "{0}/{1}".format(ecr_uri, service_name)

    build_args_command = ""

    if build_args:
        for key, val in build_args.items():
            build_args_command += "--build-arg {0}={1} ".format(key, val)

    build_command = "docker build -f {0} -t {1}:{2} {3} ./{4}/."
    local(build_command.format(dockerfile_path, ecr_repo, version, build_args_command, service))
    login_command = '$(aws ecr get-login --no-include-email --region {0})'
    local(login_command.format(region))

    with settings(warn_only=True):
        create_ecr_command = "aws ecr create-repository --repository-name {0} --region {1}"
        local(create_ecr_command.format(service_name, region))

    push_command = "docker push {0}:{1}"
    local(push_command.format(ecr_repo, version))
    return "{0}:{1}".format(ecr_repo, version)


def build_app(app, region, env, additional_apk="", debug=0):
    prepare_app_build_environment(app)

    service_name = "mmt-server-{}".format(app)
    dockerfile_path = "./{}/Dockerfile".format(app)

    build_and_push_service(region, app, dockerfile_path)


def push_app_from_nexus(app, region, tag="latest"):
    service_name = "mmt-server-{}".format(app)
    full_path = "{0}/{1}:latest".format(MSA_NEXUS, service_name)

    ecr_uri = MSA_ECR.format(region=region)
    ecr_repo = "{0}/{1}".format(ecr_uri, service_name)

    nexus_user = os.getenv("NEXUS_USER")
    nexus_password = os.getenv("NEXUS_PASSWORD")

    with settings(warn_only=True):
        local("docker rmi {}".format(full_path))

    local("docker login -u {0} -p {1} {2}".format(nexus_user, nexus_password, MSA_NEXUS))
    local("docker pull {}".format(full_path))
    local("docker tag {0} {1}:{2}".format(full_path, ecr_repo, tag))
    login_command = '$(aws ecr get-login --no-include-email --region {0})'
    local(login_command.format(region))

    with settings(warn_only=True):
        create_ecr_command = "aws ecr create-repository --repository-name {0} --region {1}"
        local(create_ecr_command.format(service_name, region))

    full_image = "{0}:{1}".format(ecr_repo, tag)
    local("docker push {0}".format(full_image))
    return full_image


def build_kong(region, env):
    dockerfile_path = "./Dockerfile.kong"
    with lcd("./api_gateway/kong"):
        build_and_push_service(region, "kong", dockerfile_path)


def build_xray(region):
    dockerfile_path = "./monitoring/xray/Dockerfile.xray"
    build_and_push_service(region, "xray", dockerfile_path)


def _get_instances(instance_name, region):
    import boto3
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(
        Filters=[
            {'Name': 'tag-key', 'Values': ['Name']},
            {'Name': 'tag-value', "Values": [instance_name]}
        ]
    )
    return instances


def _get_vault_client_token(url, token, port=80):
    import json

    data = {"role_id": token}
    data = json.dumps(data)
    command = 'curl -s --request POST --header "Content-Type: application/json" --data \'{0}\' {1}/v1/auth/approle/login'.format(data, url)
    res = json.loads(run(command))
    client_token = res['auth']['client_token']
    return client_token


def _get_vault_approle_id(url, token, service, env, port=80):

    role_name = "msa-{0}-{1}".format(env, service)

    full_url = "{0}:{1}/v1/auth/approle/role/{2}/role-id".format(url, port, role_name)

    command = 'curl -s --header "Content-Type: application/json" --header "X-Vault-Token: {0}" {1}'.format(token, full_url)
    res = json.loads(run(command))
    data = res['data']
    return data['role_id']


def _get_vault_data(url, token, service, env, port=80):

    full_url = "{0}:{1}/v1/msa/{2}/{3}".format(url, port, env, service)

    command = 'curl -s --header "Content-Type: application/json" --header "X-Vault-Token: {0}" {1}'.format(token, full_url)

    res = json.loads(run(command))
    data = res['data']
    return data


def service_terraform_apply(
        service, env, url, token,
        image, region="us-east-1",
        resource_setting=None,
        desired_count=None):

    key = "mmt-{}-bastion.pem".format(env)
    pem_key_path = os.getenv("PEM_KEY_PATH", "~/.ssh/")
    fabric_env.region = region
    fabric_env.user = "ubuntu"
    fabric_env.key_filename = "{0}{1}".format(pem_key_path, key)

    instance_name = "mmt-{}-bastion".format(env)
    bastion =  list(_get_instances(instance_name ,region)).pop()
    hosts = []
    hosts.append(bastion.public_ip_address)
    token_dict = execute(_get_vault_client_token, url, token, hosts=hosts)
    client_token = list(token_dict.values()).pop()
    role_dict = execute(_get_vault_approle_id, url, client_token, service, env, hosts=hosts)
    role_id = list(role_dict.values()).pop()
    # datadog_api_key = os.getenv("DATADOG_API_KEY")
    with lcd('./terraform/service_infra/{0}/{1}_infra/'.format(env, service)):
        local("terraform init")
        terraform_apply_command = "terraform apply"
        terraform_refresh_command = "terraform refresh"
        terraform_variable_command = " -var 'vault_role_id={}'".format(role_id)
        terraform_variable_command += " -var 'image={}'".format(image)
        # terraform_variable_command += " -var 'datadog_api_key={}'".format(datadog_api_key)

        if resource_setting is not None:
            for key, val in resource_setting.items():
                if val:
                    terraform_variable_command += " -var '{0}={1}'".format(key, val)

        if desired_count is not None:
            terraform_variable_command += " -var 'app_desired_count={}'".format(desired_count)
        terraform_apply_command += terraform_variable_command
        terraform_refresh_command += terraform_variable_command
        terraform_apply_command += " -auto-approve"
        local(terraform_refresh_command)
        local(terraform_apply_command)


def _get_max_build_number(tags):
    max_build_number = "0.0.0"

    for tag in tags:
        max_build_number_list = max_build_number.split('.')
        tag_build_number_list = tag.split('.')

        max_major_number = int(max_build_number_list[0])
        tag_major_number = int(tag_build_number_list[0])

        if max_major_number < tag_major_number:
            max_build_number = tag
            continue

        max_minor_number = int(max_build_number_list[1])
        tag_minor_number = int(tag_build_number_list[1])

        if max_minor_number < tag_minor_number:
            max_build_number = tag
            continue

        max_patch_number = int(max_build_number_list[2])
        tag_patch_number = int(tag_build_number_list[2])

        if max_patch_number < tag_patch_number:
            max_build_number = tag
            continue

    return max_build_number


def _get_latest_release_tag(service, github_id="mymusictasteadmin"):
    import requests as rq

    url = "https://api.github.com/repos/MyMusicTaste/mmt-server-{}/tags".format(service)
    github_password = os.getenv('GITHUB_TOKEN')
    res = rq.get(url=url, auth=(github_id, github_password)).json()
    tags = [x['name'] for x in list(filter(lambda x: 'rc0' in x['name'], res))]
    latest_tag = _get_max_build_number(tags)
    return latest_tag


def _get_latest_image_tag(service, region):
    command = "aws ecr describe-images --region {} ".format(region)
    command += "--repository-name mmt-server-{} ".format(service)
    command += "--query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' "
    command += "| awk '{print substr($0, 2, length($0) - 2)}'"
    latest_image_tag = local(command, capture=True)
    return latest_image_tag


def _notify_version_number_by_slack(bn, service, env):
    text = "deploying {0}:{1} now.....".format(service, bn)
    slack.notify(text=text, channel="#dev-deploy-{}".format(env))
    return


def deploy_app(service, env, worker_count=None, log_level=None, fargate_cpu=256, fargate_memory=512, app_cpu=250, app_memory=500, desired_count=2,
        release_type="patch", region="us-east-1", additional_apk="", image_tag="latest", ecs_autoscale_min_instances=2):
    prepare_app_build_environment(service)
    if env == "beta":
        release_command = "fullrelease"
        if release_type == "minor":
            release_command += " --feature"
        elif release_type == "major":
            release_command += " --breaking"

        with lcd('./{}'.format(service)):
            local(release_command)

        latest_tag = _get_latest_release_tag(service)
        prepare_app_build_environment(service, latest_tag)

        build_args = {}
        build_args.update({"APP_PORT": 8000})
        build_args.update({"SERVICE": service})
        if additional_apk:
            build_args.update({"ADDITIONAL_APK": "'{}'".format(" ".join(list(filter(None, additional_apk.split(';')))))})

        # full_image = push_app_from_nexus(service, region, tag=latest_tag)
        full_image = build_and_push_service(
            region, service,
            './{}/Dockerfile'.format(service),
            build_args=build_args,
            version=latest_tag)
        _notify_version_number_by_slack(latest_tag, service, env)

    elif env == "prod":
        repo = MSA_ECR.format(region=region)

        if image_tag == "latest":
            image_tag = _get_latest_image_tag(service, region)

        full_image = "{0}/mmt-server-{1}:{2}".format(repo, service, image_tag)
        _notify_version_number_by_slack(image_tag, service, env)

    else:
        print("Please set right env. beta|prod")
        return

    resource_setting = {
        "fargate_cpu": int(fargate_cpu),
        "fargate_memory": int(fargate_memory),
        "container_cpu": int(app_cpu),
        "container_memory": int(app_memory),
        "log_level": log_level,
        "worker_count": worker_count,
        "ecs_autoscale_min_instances": ecs_autoscale_min_instances,
    }

    vault_url = os.getenv('VAULT_{}_URL'.format(env.upper()))
    role_id = os.getenv('VAULT_{}_DEPLOY_ROLE_ID'.format(env.upper()))
    service_terraform_apply(service, env, vault_url, role_id, full_image,
        resource_setting=resource_setting, desired_count=desired_count)

def deploy_yata(host_url=None, is_server=False, version_update="patch", region='us-east-1', env="beta", cpu=250,
                memory=250, desired_count=1, static_host="betateam.mymusictaste.com", gtm_value="GTM-KRCXKJK", rollback_version=None):
    import requests
    from urllib.parse import urlparse

    service = 'yata-client'
    github_name = f'mmt-yata-client'

    if is_server:
        service = 'yata-server'
        github_name = f'mmt-yata-server'

    repo_name = f'120387605022.dkr.ecr.us-east-1.amazonaws.com/{github_name}'

    if not os.path.isdir(github_name):
        if service == 'yata-client' and env == 'beta':
            local(f"git clone -b development git@github.com:MyMusicTaste/{github_name}.git", capture=True)
        else:
            local(f"git clone git@github.com:MyMusicTaste/{github_name}.git", capture=True)

    with lcd(github_name):
        local('git pull')

        if env == "prod":
            if rollback_version:
                image_path = f'{repo_name}:{rollback_version}'
            else:
                token = os.getenv("GITHUB_TOKEN")
                github_api_url = f'https://api.github.com/repos/MyMusicTaste/{github_name}/releases'
                headers = {
                    'Authorization': f'token {token}'
                }
                r = requests.get(url=f'{github_api_url}/latest', headers=headers)
                latest_version = r.json()['tag_name']
                version_list = [int(s) for s in latest_version[1:].split('.')]

                if version_update == 'patch':
                    version_list[2] += 1
                elif version_update == 'minor':
                    version_list[1] += 1
                elif version_update == 'major':
                    version_list[0] += 1

                new_version = 'v' + (".").join([str(v) for v in version_list])
                print(f'release version : {new_version}')

                payload = {
                    'tag_name': new_version,
                    'target_commitish': 'master',
                    'name': new_version
                }

                r = requests.post(github_api_url, json=payload, headers=headers)
                if r.status_code is not 201:
                    raise Exception('It was failed to release on Github by API')

                image_path = f'{repo_name}:{new_version}'
                local(f'docker build -t {image_path} --build-arg HOST=https://{static_host} --build-arg GTM={gtm_value} .')
                local('$(aws ecr get-login --no-include-email --region us-east-1)')
                local(f'docker push {image_path}')
        else:
            image_path = f'{repo_name}:beta'
            local(f'docker build -t {image_path} --build-arg HOST=https://{static_host} --build-arg GTM={gtm_value} .')
            local('$(aws ecr get-login --no-include-email --region us-east-1)')
            local(f'docker push {image_path}')

            local(f'aws ecs update-service --service beta-{service.split("-")[1]} --force-new-deployment --cluster yata-beta --region us-east-1')
            return

    resource_setting = {
        "image": image_path,
        "cpu": cpu,
        "memory": memory,
        "desired_count": desired_count,
        "host": host_url
    }

    if service is 'yata-server':
        key = "mmt-{}-bastion.pem".format(env)
        pem_key_path = os.getenv("PEM_KEY_PATH", "~/.ssh/")
        fabric_env.region = region
        fabric_env.user = "ubuntu"
        fabric_env.key_filename = "{0}{1}".format(pem_key_path, key)
        vault_url = os.getenv(f'VAULT_{env.upper()}_URL')
        parsed_uri = urlparse(vault_url)
        deploy_role_id = os.getenv(f'VAULT_{env.upper()}_DEPLOY_ROLE_ID')
        instance_name = "mmt-{}-bastion".format(env)
        bastion = list(_get_instances(instance_name, region)).pop()
        hosts = []
        hosts.append(bastion.public_ip_address)
        token_dict = execute(_get_vault_client_token, vault_url, deploy_role_id, hosts=hosts)
        client_token = list(token_dict.values()).pop()
        role_dict = execute(_get_vault_approle_id, vault_url, client_token, 'yata', env, hosts=hosts)
        role_id = list(role_dict.values()).pop()
        resource_setting.update({
            "vault_scheme": parsed_uri.scheme,
            "vault_host": parsed_uri.netloc,
            "vault_port": 80,
            "vault_role_id": role_id,
        })

    with lcd(f'./terraform/yata_infra/{env}/{service}'):
        local("terraform init")
        terraform_apply_command = "terraform apply"
        terraform_refresh_command = "terraform refresh"
        terraform_variable_command = ""

        if resource_setting is not None:
            for key, val in resource_setting.items():
                if val:
                    terraform_variable_command += " -var '{0}={1}'".format(key, val)

        terraform_apply_command += terraform_variable_command
        terraform_refresh_command += terraform_variable_command
        terraform_apply_command += " -auto-approve"
        local(terraform_refresh_command)
        local(terraform_apply_command)


def deploy_serverless_app(service, env, region='us-east-1', log_level='DEBUG'):
    from shutil import copyfile

    prepare_app_build_environment(service)

    with lcd(service):
        local('./get_zip_file.sh')

    copyfile(f"./{service}/deploy.zip", f'./terraform/service_infra/{env}/{service}_infra/deploy.zip')

    key = "mmt-{}-bastion.pem".format(env)
    pem_key_path = os.getenv("PEM_KEY_PATH", "~/.ssh/")

    fabric_env.region = region
    fabric_env.user = "ubuntu"
    fabric_env.key_filename = "{0}{1}".format(pem_key_path, key)

    instance_name = "mmt-{}-bastion".format(env)
    bastion =  list(_get_instances(instance_name ,region)).pop()
    hosts = []
    hosts.append(bastion.public_ip_address)
    vault_url = os.getenv('VAULT_{}_URL'.format(env.upper()))
    role_id = os.getenv('VAULT_{}_DEPLOY_ROLE_ID'.format(env.upper()))
    token_dict = execute(_get_vault_client_token, vault_url, role_id, hosts=hosts)
    client_token = list(token_dict.values()).pop()
    role_dict = execute(_get_vault_approle_id, vault_url, client_token, service, env, hosts=hosts)
    role_id = list(role_dict.values()).pop()
    token_dict = execute(_get_vault_client_token, vault_url, role_id, hosts=hosts)
    client_token = list(token_dict.values()).pop()
    data_dict = execute(_get_vault_data, vault_url, client_token, service, env, hosts=hosts)
    data_dict = list(data_dict.values()).pop()

    terraform_var_args = ""

    for key, val in data_dict.items():
        terraform_var_args += " -var '{0}={1}'".format(key, val)

    with lcd('./terraform/service_infra/{0}/{1}_infra/'.format(env, service)):
        local("terraform init")
        terraform_apply_command = "terraform apply"
        terraform_apply_command += terraform_var_args
        terraform_apply_command += f' -var LOG_LEVEL={log_level}'
        terraform_apply_command += " -auto-approve"
        local(terraform_apply_command)


def deploy_rabbitmq(env, region='us-east-1'):
    instance_name = "mmt-{}-bastion".format(env)
    bastion = list(_get_instances(instance_name, region)).pop()
    service = "rabbitmq"
    key = "mmt-{}-bastion.pem".format(env)
    pem_key_path = os.getenv("PEM_KEY_PATH", "~/.ssh/")

    fabric_env.region = region
    fabric_env.user = "ubuntu"
    fabric_env.key_filename = "{0}{1}".format(pem_key_path, key)

    hosts = []
    hosts.append(bastion.public_ip_address)

    vault_url = os.getenv('VAULT_{}_URL'.format(env.upper()))
    role_id = os.getenv('VAULT_{}_DEPLOY_ROLE_ID'.format(env.upper()))
    token_dict = execute(_get_vault_client_token, vault_url, role_id, hosts=hosts)
    client_token = list(token_dict.values()).pop()
    role_dict = execute(_get_vault_approle_id, vault_url, client_token, service, env, hosts=hosts)
    role_id = list(role_dict.values()).pop()
    token_dict = execute(_get_vault_client_token, vault_url, role_id, hosts=hosts)
    client_token = list(token_dict.values()).pop()

    data_dict = execute(_get_vault_data, vault_url, client_token, service, env, hosts=hosts)
    data_dict = list(data_dict.values()).pop()
    data_dict.update({"region": region})

    terraform_var_args = ""

    for key, val in data_dict.items():
        terraform_var_args += " -var '{0}={1}'".format(key, val)

    with lcd('./terraform/{0}_infra/{1}/'.format(service, env)):
        local("terraform init")
        terraform_apply_command = "terraform apply"
        terraform_apply_command += terraform_var_args
        terraform_apply_command += " -auto-approve"
        local(terraform_apply_command)


def _make_service_jenkins_job(server, env, service, slack_token):
    from jinja2 import Environment, FileSystemLoader

    template_fn = "deploy_{}_job_template.xml".format(env)

    context = {
        "service": service,
        "env": env,
        "slack_token": slack_token,
    }

    path = os.path.dirname(os.path.abspath(__file__))
    template_env = Environment(
        autoescape=False,
        loader=FileSystemLoader(os.path.join(path, 'command/jenkins_templates')),
        trim_blocks=False
    )

    xml = template_env.get_template(template_fn).render(context)
    server.create_job('deploy-{0}-{1}'.format(env, service), xml)


def make_service_jenkins_jobs(env, local_vault_url, local_vault_token):
    client = hvac.Client(url=local_vault_url, token=local_vault_token)
    res = client.list('msa-services/')
    service_list = res.get('data').get('keys')
    slack_token = client.read('secret/common')['data']['JENKINS_SLACK_TOKEN']

    jenkins_url = "http://jenkins.mmt.local:9082/"
    jenkins_un = "user"
    jenkins_pw = os.getenv("GITHUB_TOKEN")
    server = jenkins.Jenkins(jenkins_url, username=jenkins_un, password=jenkins_pw)

    for service in service_list:
        _make_service_jenkins_job(server, env, service, slack_token)


def make_service_terraform_templates(env, local_vault_url, local_vault_token):
    client = hvac.Client(url=local_vault_url, token=local_vault_token)
    res = client.list('msa-services/')
    service_list = res.get('data').get('keys')
    dir_path = "./terraform/service_infra/{0}/{1}_infra"
    for service in service_list:
        if not os.path.isdir(dir_path.format(env, service)):
            local('mkdir {}'.format(dir_path.format(env, service)))
            local('cp ./terraform/service_infra/service_template/*.tf {}/'.format(dir_path.format(env, service)))


def force_update_all_service(cluster, region="us-east-1"):
    command = "aws ecs list-services --cluster {0} --region {1}"
    res = json.loads(local(command.format(cluster, region), capture=True))
    service_list = res.get("serviceArns")
    command = "aws ecs update-service --cluster {0} --service {1} --force-new-deployment --region {2}"

    for service in service_list:
        local(command.format(cluster, service, region))


def force_delete_all_service(cluster, region="us-east-1"):
    command = "aws ecs list-services --cluster {0} --region {1}"
    res = json.loads(local(command.format(cluster, region), capture=True))
    service_list = res.get("serviceArns")
    command = "aws ecs delete-service --cluster {0} --service {1} --region {2}"
    command_2 = "aws ecs update-service --cluster {0} --service {1} --force-new-deployment --desired-count 0 --region {2}"

    for service in service_list:
        local(command_2.format(cluster, service, region))
        local(command.format(cluster, service, region))
