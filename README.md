# Una estrategia basada en Linux Containers para convertir una típica aplicación web PHP en un sistema  de tenencia múltiple.


## Resumen

En este trabajo se describe un sistema basado en linux containers mediante el 
cual se consigue que una sola instancia de una misma aplicación web PHP sirva a 
múltiples clientes u organizaciones como si se tratase de múltiples instancias 
independientes.

Cada cliente u organización accede a su aplicación a través de su propia URL, 
pero el código que se ejecuta es el mismo para todos, aunque con una 
configuración diferente, de manera que cada una de ellas puede tener, por 
ejemplo, su propia base de datos. 

Se describe, por tanto, una manera de conseguir la ["tenencia múltiple"][1]
(multitenancy) de una típica aplicación web  PHP que, en principio, está 
diseñada para dar servicio a una única organización. Dicha estrategia usa los 
[linux containers][2] como elemento clave y fundamental. 

El sistema propuesto permite añadir/eliminar organizaciones de forma inmediata y automática
sin que ello afecte al resto de las organizaciones (no hay que reiniciar ningún servicio ni
nada parecido).

Esto facilita el desarrollo aplicaciones mediante las cuales se gestionen los datos de
configuración de cada organización y se controle de manera automática el arranque o parada de 
sus servicios asociados siguiendo criterios económicos (pago del servicio) o cualquier otro que
pueda ser efectivamente monitorizado.

El sistema también ofrece una manera inmediata de  medir tiempo que cada organización ha estado 
utilizando el sistema, lo que puede interesar de cara a la facturación del servicio.

[1]: http://en.wikipedia.org/wiki/Multitenancy
[2]: https://linuxcontainers.org

## Descripción del sistema

El siguiente esquema representa la arquitectura del sistema.

![Arquitectura del sistema](arquitectura.png)

Los servicios del sistema se han agrupado en tres partes (en la práctica se 
pueden corresponder con tres servidores):

El *Container Host*, es donde se desplegarán todos los contenedores del sistema.
Su sistema operativo debe ser linux, ya que usamos linux containers.

El *Database server*, que alojará las bases de datos para cada una de las 
organizaciones que usan la aplicación.

El *Application Source File System* que almacenará el código de la aplicación 
PHP y que será montado por el *Container Host*.
   
La pieza clave del sistema es el *Container Host*, las otras dos no precisan 
ninguna explicación especial para entender el sistema que proponemos. Realizan 
las funciones de almacenamiento típicas y listo.

### El Container Host

En él desplegaremos 3 tipos de contenedores:

1. El *PHP-FPM Container*. Ejecuta un servidor PHP-FPM, que es el encargado de 
   procesar el código PHP de la aplicación. Obtiene el código del Sistema de 
   Ficheros y la base de datos del Servidor de base de datos.

2. Los *Apache Containers*. Cada uno de ellos se corresponde con una 
   organización y ejecutan un servidor apache simple (sin módulo php) en el 
   puerto 80 de cada container. Cada *apache container* expone al 
   *Container Host* su puerto ``80``


3. El *Reverse Proxy Container*. Este container ejecuta un servidor web *nginx*
   que actúa como reverse proxy de los *apache containers*. Las URL's de cada
   organización apuntan a este proxy y él se encarga de dirigir el tráfico al
   *apache container* que corresponda. Este container está diseñado de tal 
   manera que detecta automáticamente los apache containers que se están
   ejecutando y reconfigura su tabla de redirecciones a medida que los *apache
   containers* se crean o destruyen. En este [artículo][3] se muestra el 
   funcionamiento en detalle de este magnífico proxy.

[3]: http://jasonwilder.com/blog/2014/03/25/automated-nginx-reverse-proxy-for-docker 


## Descripción a fondo del sistema

En este apartado vamos a describir la implementación concreta que hemos 
realizado en nuestra prueba de concepto. El código completo puede obtenerse en 
este [repositorio][4] de GitHub.

[4]: https://github.com/juanda/sed.git

### Descripción del sistema usado en la prueba de concepto

Los tres componentes del sistema se han implementado en una sola máquina con 
las siguientes características:

* Sistema Operativo: Ubuntu 14.04, kernel 3.13.0-44-generic 
* Tecnología de gestión de containers: Docker 1.4.1
* Sistema Gestor de bas de datos: MySQL 5.5.41
* Sistema de Ficheros para el código PHP: Un directorio de la propia máquina
* Aplicación PHP: Moodle 2.7

### Construcción de la imagen para el PHP-FPM container

La imagen del *PHP-FPM container* se ha realizado usando el siguiente 
[Dockerfile][5].

[5]: https://github.com/juanda/sed/blob/master/DockerfilePhpFpm/Dockerfile

Los puntos a destacar son:

- la creación del directorio ``/moodledata``, donde se ubicarán los directorios
  de datos de todos los moodles del sistema.

> Nota: Moodle require para su correcto funcionamiento, además de la base de 
> datos, un directorio de datos.

- la exposición a la máquina anfitrión del puerto 9000 

### Construcción de la imagen para los apache containers

La imagen de los apache containers se ha realizado usando el siguiente 
[Dockerfile][6]

Los puntos a destacar son los siguientes:

- La instalación y habilitación del módulo *proxy_fcgi*, para la comunicación 
  con el *PHP-FPM container*.

- Se añade un virtual host cuya configuración viene dada por el siguiente 
  [fichero][7]. En dicho fichero se definen las variables de entorno ``DBHOST``,
  ``DBNAME``, ``DBUSER``, ``DBPASS``, ``WWWROOT``, ``DATAROOT``, para que sean 
  pasadas al *PHP-FPM container*. Estos valores harán posibles que la ejecución 
  del código PHP sea realizada con los parámetros de configuración adecuados a 
  cada organización. Estas variables de entorno son *propias* de apache, y se 
  definen a partir de otras variables de entorno propias del sistema para las 
  que hemos usado los mismos nombres. Para que apache las reconozca cuando se 
  inicia el servicio hay que exportarlas en el fichero [envvars][8], el cual 
  también se exporta al contenedor.

- Se añade el fichero [envvars][8] al contenedor, el cual, como acabamos de
  decir, sirve para indicar a apache qué variables de entorno debe exportar. 
  Es importante observar que, además de las indicadas anteriormente, también
  se exporta una variable denominada ``FPM_IP`` 
  (``export FPM_IP=$FPM_PORT_9000_TCP_ADDR``). Se trata de la ip interna del 
  *PHP_FPM container*, y es inyectada desde el *PHP_FPM container* a cada uno de
  los apache container cuando se ejecutan estos últimos "enlazados" (linked) al
  primero. La variable de entorno que se crea en los apache containers se 
  llama ``FPM_PORT_9000_TCP_ADDR``.

[6]: https://github.com/juanda/sed/blob/master/DockerfileApache/Dockerfile
[7]: https://github.com/juanda/sed/blob/master/DockerfileApache/VirtualHost
[8]: https://github.com/juanda/sed/blob/master/DockerfileApache/envvars

### Construcción de la imagen para el reverse_proxy container

Se ha utilizado directamente la imagen [jwilder/nginx-proxy][9]. La construcción
de dicha imagen se puede hacer el siguiente [Dockerfile][10].

En este [artículo][11] se describe cómo se ha concebido y construido esta bestia. 

En esencia, el contenedor crea un fichero de configuración para nginx que lo hace 
funcionar como reverse proxy de cada una de los containers que definan la 
variable de entorno ``VIRTUAL_HOST``. Detecta el puerto que cada uno de estos 
containers tiene mapeado sobre el anfitrión y lo utiliza para llevar a cabo la 
redirección desde ``http://VIRTUAL_HOST:port_reverse_proxy`` hasta 
``http://VIRTUAL_HOST:port_web``, donde ``port_reverse_proxy`` es el puerto
mapeado sobre el anfitrión por el reverse_proxy container y ``port_web`` es 
el puerto mapeado sobre el anfitrión por cada contenedor que defina la variable
de entorno ``VIRTUAL_HOST``. 

Es importante que cada uno de los dominios definidos en cada uno de los 
``VIRTUAL_HOST``'s apunten a la IP del *Container Host*.

Lo impresionante de este container es que es capaz de detectar cuando se arranca
o para un nuevo container, verificar si define la variable de entorno 
``VIRTUAL_HOST`` y, en su caso, rehacer y recargar la configuración de nginx 
para tener en cuenta al nuevo container.

[9]: https://registry.hub.docker.com/u/jwilder/nginx-proxy
[10]: https://github.com/jwilder/nginx-proxy
[11]: http://jasonwilder.com/blog/2014/03/25/automated-nginx-reverse-proxy-for-docker

## Puesta en marcha del sistema

El sistema completo se arranca de la siguiente manera:

### Arranque del reverse_proxy container

Se lanza la siguiente instrucción por CLI:

    sudo docker run -d -p 8080:80 -v /var/run/docker.sock:/tmp/docker.sock --name reverse_proxy jwilder/nginx-proxy

Es decir, se ejecuta como *daemon* la imagen ``jwilder/nginx-proxy`` y se le 
asigna el nombre ``reverse_proxy``. El container expone su puerto 80 que es 
mapeado en el 8080 del anfitrión. Además se monta directorio 
``/var/run/docker.sock`` del anfitrión en el container. Esta es la pieza clave 
que permite al container conocer el estado del sistema.

### Arranque del PHP-FPM container

Se lanza la siguiente instrucción por CLI:

    sudo docker run -d --name fpm \
    -v /home/juanda/Apps/moodleDocker/moodle:/var/www/html \
    -v /home/juanda/Apps/moodleDocker/moodle_resources/config.php:/var/www/html/config.php \
    juandalibaba/php-fpm

Es decir, se ejecuta el container como demonio y se monta el volumen donde se 
encuentra el código de Moodle en el directorio ``/var/www/html`` del container,
además se sobreescribe el fichero de configuración del Moodle original por 
[config.php][12]. 

La gracia de este último archivo es que define algunos de los parámetros de 
configuración como valores pasados al *PHP_FPM container* desde cada uno de los
apaches a través de la configuración de sus virtual host (recuerdese la 
definición de las variables de entorno en el fichero de configuración de los 
apache containers). De esta forma el *PHP-FPM container* sabe con qué 
configuración debe ejecutar el código Moodle en función de la organización que 
haya realizado la petición.

También se le asigna el nombre ``fpm`` al container.

[12]: https://github.com/juanda/sed/blob/master/moodle_resources/config.php

### Arranque de los apache containers

Se lanza la siguiente instrucción por CLI:

    sudo docker run -d -p :80 --name centro1 --link fpm:fpm \
    -e VIRTUAL_HOST=centro1.sed.local \
    -e DBHOST=10.200.16.27 \
    -e DBNAME=moodle_centro1 \
    -e DBUSER=root \
    -e DBPASS=root \ 
    -e WWWROOT="http://centro1.sed.local:8080" \
    -e DATAROOT=moodledata_centro1 juandalibaba/apache

Se ejecuta el container como demonio, se enlaza con el *PHP-FPM* container y se pasan explicitamente las variables de entorno:

- ``VIRTUAL_HOST``, que sirve para que el reverse_proxy lo tenga en cuenta,

- ``DBHOST``, ``DBNAME``, ``DBUSER``, ``DBPASS``, ``WWWROOT``, ``DATAROOT`` que
  sirve para que se pasen al PHP-FPM y este, a su vez, sepa con que parámetros
  de configuración debe ejecutarse el código Moodle.

Además, por estar "enlazado" (linked) con el *PHP-FPM container*, este último 
le inyecta las siguientes variables de entorno.

   FPM_PORT_9000_TCP_ADDR=172.17.0.9
   FPM_PORT_9000_TCP_PORT=9000
   FPM_NAME=/centro1/fpm
   FPM_PORT_9000_TCP_PROTO=tcp
   FPM_PORT=tcp://172.17.0.9:9000
   FPM_PORT_9000_TCP=tcp://172.17.0.9:9000

> Nota: Los valores son ejemplos concretos de uno de los apache containers en 
> nuestra prueba de concepto

Recuerdese que la variable ``FPM_PORT_9000_TCP_ADDR`` es utilizada por los 
*apache containers* para definir la IP del *PHP-FPM container*. Esto se hace en
la configuración de apache:

    ProxyPassMatch ^/(.*\.php(/.*)?)$ fcgi://${FPM_IP}:9000/var/www/html/$1
    ProxyPassMatch ^/(.*(/.*)?)$ fcgi://${FPM_IP}:9000/var/www/html/$1/index.php 


Recuerdese también que esta información es exportada en la variable ``FPM_IP``, 
lo cual se hace en el archivo ``envvars``.


Y con esto ya tenemos el sistema funcionando. Cada vez que queramos añadir una 
organización basta con ejecutar el siguiente comando:

    sudo docker run -d -p :80 --name NOMBRE_ORGANIZACION --link fpm:fpm \
    -e VIRTUAL_HOST=DOMINIO_ORGANIZACION \
    -e DBHOST=HOST_BASE_DATOS \
    -e DBNAME=NOMBRE_BASE_DATOS \
    -e DBUSER=USERNAME_BASE_DATOS \
    -e DBPASS=PASSWORD_BASE_DATOS \ 
    -e WWWROOT="URL_ORGANIZACION" \
    -e DATAROOT=DIRECTORIO_DATOS_ORGANIZACION juandalibaba/apache

Y la aplicación queda lista para ser usada por la organización en cuestión a
través de la URL que tenga asignada.

Automatización del despliegue
-----------------------------

Con el fin de facilitar el despliegue del sistema se ha elaborado un 
[fabfile][13] mediante el cual podemos llevar a cabo las siguientes tareas:

- print_centros      Impirime todos los centros y sus datos
- ps_running         Muestra todos los containers que se están ejecutando.
- run                Ejecuta todos los containers.
- run_centro         Ejecuta el container apache asociado al centro dado como argumento.
- run_centros        Ejecuta los containers apache de todos los centros.
- run_fpm            Ejecuta el contenedor fpm.
- run_reverse_proxy  Ejecuta el contenedor reverse_proxy
- stop               Para y borra todos los containers que se están ejecutando.

El script utiliza como base de datos un [fichero json][14]) con los datos de las
organizaciones que utilizarán la aplicación Moodle


[13]: http://www.fabfile.org
[14]: https://github.com/juanda/sed/blob/master/fabric/centros.json
