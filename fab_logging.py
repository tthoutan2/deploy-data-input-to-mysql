import os
import pymysql
from fabric.api import local


def deploy_info_beta_prod(service, env):

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
                            built_at TIMESTAMP NULL,
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
                            img_tag_version VARCHAR(16) NULL,
                            ecs_autoscale_min_instances INT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            ) DEFAULT CHARACTER SET utf8mb4
            """

            cursor.execute(sql)
        with connection.cursor() as cursor:
            sql = """INSERT INTO info_beta_prod (built_at, service, env, fargate_cpu,
                                              fargate_memory, app_cpu, app_memory, desired_count,
                                              log_level, worker_count, release_type, region,
                                              additional_apk, img_tag_version, ecs_autoscale_min_instances, build_number)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                              %s, %s, %s)"""

            latest_img_tag = _get_latest_image_tag(service, 'us-east-1')
            cursor.execute(sql, (os.getenv('built_at'), service, env,
                                 os.getenv('fargate_cpu'), os.getenv('fargate_memory'),
                                 os.getenv('app_cpu'), os.getenv('app_memory'),
                                 os.getenv('desired_count'), os.getenv('log_level'),
                                 os.getenv('worker_count'), os.getenv('release_type'),
                                 os.getenv('region'), os.getenv('additional_apk'),
                                 latest_img_tag,
                                 os.getenv('ecs_autoscale_min_instances'),
                                 os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_etc(service, env):

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
                            built_at TIMESTAMP NULL,
                            service VARCHAR(64) NULL,
                            env VARCHAR(8) NULL,
                            description TEXT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_etc (built_at, service, env, description, build_number)
                                    VALUES(%s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('built_at'), service, env,
                                 os.getenv('description'), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_yata(env):

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
                            built_at TIMESTAMP NULL,
                            host_url VARCHAR(256) NULL,
                            is_server VARCHAR(8) NULL,
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
            sql = """INSERT INTO info_yata (built_at, host_url, is_server, version_update, region, 
                                            env, app_cpu, app_memory, desired_count, static_host, gtm_value,
                                            rollback_version, build_number)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('built_at'), os.getenv('host_url'),
                                 os.getenv('is_server'), os.getenv('version_update'),
                                 os.getenv('region'), env, os.getenv('cpu'),
                                 os.getenv('memory'), os.getenv('desired_count'),
                                 os.getenv('static_host'), os.getenv('gtm_value'),
                                 os.getenv('rollback_version'), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_local(service):

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
                            built_at TIMESTAMP NULL,
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
            sql = """INSERT INTO info_local (built_at, service, additional_apk, debug, environment,
                                             stack_name, replica_num, memory_limit, cpu_limit, git_branch, build_number)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('built_at'), service,
                                 os.getenv('additional_apk'), os.getenv('debug'),
                                 os.getenv('environment'), os.getenv('stack_name'),
                                 os.getenv('replica_num'), os.getenv('memory_limit'),
                                 os.getenv('cpu_limit'), os.getenv('git_branch_env'),
                                 os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def deploy_info_local_yata():

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
                            built_at TIMESTAMP NULL,
                            is_server VARCHAR(8) NULL,
                            host VARCHAR(256) NULL,
                            port INT NULL,
                            build_number INT NULL,
                            PRIMARY KEY(id)
            )
            """

            cursor.execute(sql)

        with connection.cursor() as cursor:
            sql = """INSERT INTO info_local_yata (built_at, is_server, host, port, build_number)
                                          VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(sql, (os.getenv('built_at'), os.getenv('is_server'),
                                 os.getenv('host'), os.getenv('port'), os.getenv('BUILD_NUMBER')))

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
                                built_at TIMESTAMP NULL,
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
            sql = """INSERT INTO info_bastion (built_at, purpose, action_name, environment, 
                                                    service_name, request_user, build_number)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (os.getenv('built_at'), purpose, os.getenv('action'),
                                 os.getenv('environment'), os.getenv('service_name'),
                                 os.getenv('BUILD_USER_ID'), os.getenv('BUILD_NUMBER')))

    finally:
        connection.close()


def _get_latest_image_tag(service, region):

    command = "aws ecr describe-images --region {} ".format(region)
    command += "--repository-name mmt-server-{} ".format(service)
    command += "--query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' "
    command += "| awk '{print substr($0, 2, length($0) - 2)}'"
    latest_image_tag = local(command, capture=True)
    return latest_image_tag
