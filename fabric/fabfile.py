# -*- coding: utf-8 -*-

from fabric.api import settings, task, local, hide
from validictory import validate, validator
from pprint import pprint
import json
import sys

# Esquemas JSON para la validación del fichero de centros

centros_schema = {"type": "object"}

centro_schema = {
    "type": "object",
    "properties": {
        "nombre": {"type": "string"},
        "envvars": {
            "type": "object",
            "properties": {
                "VIRTUAL_HOST": {"type": "string"},
                "DBHOST": {"type": "string"},
                "DBNAME": {"type": "string"},
                "DBUSER": {"type": "string"},
                "DBPASS": {"type": "string"},
                "WWWROOT": {"type": "string"},
                "DATAROOT": {"type": "string"},
            }
        }
    }
}

# Fin esquemas JSON

# Configuración del script


class Conf:
    centrosfile = 'centros.json'
    db_root_user = 'root'
    db_root_pass = 'root'
    db_dumpfile = '/home/juanda/Apps/moodleDocker/moodle_resources/moodle.sql'
    moodle_source_dir = '/home/juanda/Apps/moodleDocker/moodle'
    moodle_container_dir = '/var/www/html'
    moodle_config_file = \
        '/home/juanda/Apps/moodleDocker/moodle_resources/config.php'
    apache_container_image = 'juandalibaba/apache'
    fpm_container_name = 'fpm'
    fpm_image_name = 'juandalibaba/php-fpm'
    reverse_proxy_container_name = 'reverse_proxy'
    reverse_proxy_image_name = 'jwilder/nginx-proxy'
    reverse_proxy_port = "8080"

conf = Conf()

# Fin Configuración


def get_centros():
    """ Devueve un dictionary con todos los centros
    especificados en el archivo de centros.
    """
    try:
        json_centros = open(conf.centrosfile)
        data_centros = json.load(json_centros)
        validate(data_centros, centros_schema)
        return data_centros
    except IOError:
        print "Necesito un fichero '" + conf.centrosfile + "' para funcionar"
        sys.exit(0)
    except ValueError:
        print "El fichero '" + conf.centrosfile + u"' no parece un json válido"
        sys.exit(0)


def build_run_centro_command(centro):
    """ Construye un comando docler para la ejecución del
    container apache asociado al centro
    """
    try:
        validate(centro, centro_schema)
        envvars = centro['envvars']

        command = []

        command.append("sudo docker run -d ")
        command.append("-p :80 ")
        command.append("--name " + centro['nombre'] + " ")
        command.append("--link " + conf.fpm_container_name + ":" +
                       conf.fpm_container_name + " ")

        for var in envvars:
            command.append("-e " + var + "=" + envvars[var] + " ")

        command.append(conf.apache_container_image)
        command.append(" || sudo docker start " + centro['nombre'])

        command_str = ''.join(command)

        return command_str
    except validator.ValidationError, e:
        print "Alguno de los centros del fichero '" + conf.centrosfile + \
              "no está bien definido"
        print e
        sys.exit(0)


def create_db_centro(centro_name):
    """ Crea la base de datos del centro en caso de que no exista. """
    centros = get_centros()
    centro = centros[centro_name]
    dbname = centro['envvars']['DBNAME']
    dbhost = centro['envvars']['DBHOST']
    query = "SELECT count(*) FROM INFORMATION_SCHEMA.SCHEMATA WHERE " + \
            "SCHEMA_NAME = '" + dbname + "'"

    command_mysql = []
    command_query = []
    command_mysql.append("mysql -u " + conf.db_root_user + " ")
    command_mysql.append("-p" + conf.db_root_pass + " ")
    command_mysql.append("-h " + dbhost + " ")
    command_mysql.append(" -B --skip-column-names ")
    command_query.append("-e \"" + query + "\"")

    command_str = ''.join(command_mysql) + ''.join(command_query)

    number_of_databases = local(command_str, capture=True)
    print number_of_databases

    exist_database = number_of_databases != "0"

    if not exist_database:
        print "Creando la base de datos " + dbname + " en " + dbhost
        create_query = []
        create_query.append("create database " + dbname + ";")
        create_query.append("use " + dbname + ";")
        create_query.append("\. " + conf.db_dumpfile)
        create_query_str = ''.join(create_query)

        command_create_db = []
        command_create_db.append("-e \"" + create_query_str + "\"")
        command_create_db_str = ''.join(command_mysql) + \
            ''.join(command_create_db)

        local(command_create_db_str)

        return True

    return False


@task
def print_centros(name=False):
    """ Impirime todos los centros y sus datos """
    try:
        centros = get_centros()
        if name:
            pprint(centros[name])
        else:
            pprint(centros)
    except KeyError:
        print "No existe un centro con nombre " + name


def get_container_info(container_name):
    """ Devueve un JSON con la información del containe que se pasa como
    argumento, en caso de que exista. Si no existe no devuelve nada.
    """
    command_str = "sudo docker inspect " + container_name

    with settings(hide('everything'), warn_only=True):
        out = local(command_str, capture=True)

    out = False if out.failed else out

    return out


def container_is_running(container_name):
    """ Devuelve True si el container cuyo nombre se pasa como argumento
    se está ejecutando, y False en caso contrario.
    """
    container_info = get_container_info(container_name)
    if not container_info:
        return False
    else:
        info = json.loads(container_info)
        return info[0]['State']['Running']


@task
def run_fpm():
    """ Ejecuta el contenedor fpm. """
    if container_is_running(conf.fpm_container_name):
        print "El container fpm ya está ejecutándose"
        return False

    command = []
    command.append("sudo docker run -d ")
    command.append("--name " + conf.fpm_container_name + " ")
    command.append("-v " + conf.moodle_source_dir + ":" +
                   conf.moodle_container_dir + " ")
    command.append(" -v " + conf.moodle_config_file + ":" +
                   conf.moodle_container_dir + "/config.php ")
    command.append(conf.fpm_image_name)
    command.append(" || sudo docker start " + conf.fpm_container_name)

    command_str = ''.join(command)

    with settings(warn_only=True):
        local(command_str)

    return True


@task
def run_reverse_proxy():
    """ Ejecuta el contenedor reverse_proxy """
    if container_is_running(conf.reverse_proxy_container_name):
        print "El container reverse_proxy ya está ejecutándose"
        return False

    command = []
    command.append("sudo docker run -d ")
    command.append("--name " + conf.reverse_proxy_container_name + " ")
    command.append(" -p " + conf.reverse_proxy_port + ":80 ")
    command.append("-v /var/run/docker.sock:/tmp/docker.sock ")
    command.append(conf.reverse_proxy_image_name)
    command.append(" || sudo docker start " + conf.reverse_proxy_container_name)

    command_str = ''.join(command)

    with settings(warn_only=True):
        local(command_str)

    return True


@task
def run_centro(centro_name):
    """ Ejecuta el container apache asociado al centro dado como argumento. """
    centros = get_centros()

    if centro_name in centros:
        if not container_is_running(conf.fpm_container_name):
            print "El container '" + conf.fpm_container_name + \
                  "' debe estar ejecutándose antes de que este centro " + \
                  "se pueda desplegar"
            return False
        if not container_is_running(conf.reverse_proxy_container_name):
            print "El container '" + conf.reverse_proxy_container_name + \
                  "' debe estar ejecutándose antes de que este centro " + \
                  "se pueda desplegar"
            return False

        if container_is_running(centro_name):
            print "El container '" + centro_name + "' ya esta ejecutandose"
            return False

        # Se crea la base de datos si no existe
        create_db_centro(centro_name)

        command = []
        command.append(build_run_centro_command(centros[centro_name]))

        command_str = ''.join(command)

        with settings(warn_only=True):
            local(command_str)

        return True
    else:
        print "El centro '" + centro_name + "' no existe"
        return False


@task
def run_centros():
    """ Ejecuta los containers apache de todos los centros. """
    centros = get_centros()

    for centro in centros:
        run_centro(centro)

    return


@task
def run():
    """ Ejecuta todos los containers. """
    run_fpm()
    run_reverse_proxy()
    run_centros()


@task
def ps_running():
    """ Muestra todos los containers que se están ejecutando. """
    command_str = "sudo docker ps"
    local(command_str)
    return


@task
def stop():
    """ Para y borra todos los containers que se están ejecutando. """
    command = []
    command.append("sudo docker stop `sudo docker ps -a -q`;")
    command.append("sudo docker rm `sudo docker ps -a -q`")

    command_str = ''.join(command)

    local(command_str)

    return
