import os
import pymysql


def deploy_info_beta_prod(service, env, worker_count=None, log_level=None, fargate_cpu=256, fargate_memory=512, app_cpu=250,
                     app_memory=500, desired_count=2, release_type="patch", region="us-east-1", additional_apk="",
                     image_tag="latest", ecs_autoscale_min_instances=2):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_beta_prod (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            env VARCHAR(8) NULL,
                            fargate_cpu INT NULL,
                            fargate_memory INT NULL,
                            app_cpu INT NULL,
                            app_memory INT NULL,
                            desired_count INT NULL,
                            log_level VARCHAR(16) NULL,
                            worker_count INT NULL,
                            release_type VARCHAR(16) NULL,
                            region VARCHAR(20) NULL,
                            additional_apk VARCHAR(32) NULL,
                            image_tag VARCHAR(16) NULL,
                            ecs_autoscale_min_instances INT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            ) DEFAULT CHARACTER SET utf8mb4
            """

            cursor.execute(sql)
        with connection.cursor() as cursor:
            sql = """INSERT INTO info_beta_prod (started_at, finished_at, service, env, fargate_cpu,
                                              fargate_memory, app_cpu, app_memory, desired_count,
                                              log_level, worker_count, release_type, region,
                                              additional_apk, image_tag, ecs_autoscale_min_instances, build_number)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                              %s, %s, %s, %s)"""
            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), service, env,
                                 os.getenv('fargate_cpu', fargate_cpu), os.getenv('fargate_memory', fargate_memory),
                                 os.getenv('app_cpu', app_cpu), os.getenv('app_memory', app_memory),
                                 os.getenv('desired_count', desired_count), os.getenv('log_level', log_level),
                                 os.getenv('worker_count', worker_count), os.getenv('release_type', release_type),
                                 os.getenv('region', region), os.getenv('additional_apk', additional_apk),
                                 os.getenv('image_tag', image_tag),
                                 os.getenv('ecs_autoscale_min_instances', ecs_autoscale_min_instances),
                                 os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_etc(service, env, description=""):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_etc (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            env VARCHAR(8) NULL,
                            description TEXT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_etc (started_at, finished_at, service, env, description, build_number)
                                    VALUES(%s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), service, env,
                                 os.getenv('description', description), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_datalake(env):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_datalake (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            env VARCHAR(8) NULL,
                            github_branch VARCHAR(16) NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_datalake (started_at, finished_at, service, env, github_branch, build_number)
                                        VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), 'datalake',
                                 env, os.getenv('GITHUB_BRANCH'), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_yata(host_url=None, is_server=False, version_update="patch", region='us-east-1', env='beta', cpu=250,
                     memory=250, desired_count=1, static_host='betateam.mymusictaste.com', gtm_value='GTM_KRCXKJK',
                     rollback_version=None):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_yata (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            host_url VARCHAR(256) NULL,
                            is_server BOOLEAN NULL,
                            version_update VARCHAR(16) NULL,
                            region VARCHAR(20) NULL,
                            env VARCHAR(8) NULL,
                            app_cpu INT NULL,
                            app_memory INT NULL,
                            desired_count INT NULL,
                            static_host VARCHAR(256) NULL,
                            gtm_value VARCHAR(32) NULL,
                            rollback_version VARCHAR(8),
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)
        with connection.cursor() as cursor:
            sql = """INSERT INTO info_yata (started_at, finished_at, host_url, is_server, version_update, region, 
                                            env, app_cpu, app_memory, desired_count, static_host, gtm_value,
                                            rollback_version, build_number)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), os.getenv('host_url', host_url),
                                 os.getenv('is_server', is_server), os.getenv('version_update', version_update),
                                 os.getenv('region', region), env, os.getenv('cpu', cpu),
                                 os.getenv('memory', memory), os.getenv('desired_count', desired_count),
                                 os.getenv('static_host', static_host), os.getenv('gtm_value', gtm_value),
                                 os.getenv('rollback_version', rollback_version), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_test(service):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_test (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            vault_role_id VARCHAR(64) NULL,
                            service VARCHAR(64) NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_test (started_at, finished_at, vault_role_id, service, build_number)
                                    VALUES (%s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), os.getenv('VAULT_ROLE_ID'),
                                 service, os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_local(service, additional_apk="", debug=0, environment='development', stack_name='mmt-server',
                      replica_num=2, memory_limit='500M', cpu_limit='0.15', git_branch='master'):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:

            sql = """CREATE TABLE IF NOT EXISTS info_local (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            additional_apk VARCHAR(32) NULL,
                            debug INT NULL,
                            environment VARCHAR(16) NULL,
                            stack_name VARCHAR(16) NULL,
                            replica_num INT NULL,
                            memory_limit VARCHAR(16) NULL,
                            cpu_limit VARCHAR(8) NULL,
                            git_branch VARCHAR(16) NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_local (started_at, finished_at, service, additional_apk, debug, environment,
                                             stack_name, replica_num, memory_limit, cpu_limit, git_branch, build_number)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), service,
                                 os.getenv('additional_apk', additional_apk), os.getenv('debug', debug),
                                 os.getenv('environment', environment), os.getenv('stack_name', stack_name),
                                 os.getenv('replica_num', replica_num), os.getenv('memory_limit', memory_limit),
                                 os.getenv('cpu_limit', cpu_limit), os.getenv('git_branch_env', git_branch),
                                 os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_push_builder(service):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:

            sql = """CREATE TABLE IF NOT EXISTS info_push_builder (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:

            sql = """INSERT INTO info_push_builder (started_at, finished_at, service, build_number)
                                            VALUES (%s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), service, os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_local_yata(is_server=False, host="development.msa.swarm", port=3000):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_local_yata (
                            id INT NOT NULL AUTO_INCREMENT,
                            started_at TIMESTAMP NULL,
                            finished_at TIMESTAMP NULL,
                            is_server BOOLEAN NULL,
                            host VARCHAR(256) NULL,
                            port INT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_local_yata (started_at, finished_at, is_server, host, port, build_number)
                                          VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), os.getenv('is_server', is_server),
                                 os.getenv('host', host), os.getenv('port', port), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def build_info_bastion(purpose):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql  = """CREATE TABLE IF NOT EXISTS info_bastion (
                                id INT NOT NULL AUTO_INCREMENT,
                                started_at TIMESTAMP NULL,
                                finished_at TIMESTAMP NULL,
                                purpose VARCHAR(16) NULL,
                                action_name VARCHAR(8) NULL,
                                environment VARCHAR(8) NULL,
                                service_name VARCHAR(64) NULL,
                                request_user VARCHAR(64) NULL,
                                build_number INT NULL,
                                PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_beta_bastion (started_at, finished_at, purpose, action_name, environment, 
                                                    service_name, request_user, build_number)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), purpose, os.getenv('action'),
                                 os.getenv('environment', 'beta'), os.getenv('service_name', ""),
                                 os.getenv('BUILD_USER_ID'), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def create_info_repo(repo_type):

    connection = pymysql.connect(host=os.environ['MYSQL_HOST'],
                                 user=os.environ['MYSQL_USER'],
                                 password=os.environ['MYSQL_PASS'],
                                 db='deploy_information',
                                 charset='utf8mb4',
                                 port=3306,
                                 autocommit=True
                                 )

    try:
        with connection.cursor() as cursor:
            sql = """CREATE TABLE IF NOT EXISTS info_repo (
                               id INT NOT NULL AUTO_INCREMENT,
                               started_at TIMESTAMP NULL,
                               finished_at TIMESTAMP NULL,
                               repo_name VARCHAR(64) NULL,
                               team_id VARCHAR(64) NULL,
                               user_name VARCHAR(64) NULL,
                               repo_type VARCHAR(12) NULL,
                               build_number INT NULL,
                               PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_repo (started_at, finished_at, repo_name, team_id, user_name, repo_type, 
                                            build_number)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('started_at'), os.getenv('finished_at'), os.getenv('repo_name'),
                                 os.getenv('team_id', ""), os.getenv('user_name', ""), repo_type,
                                 os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()