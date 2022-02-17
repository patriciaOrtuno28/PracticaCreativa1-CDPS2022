# PracticaCreativa1-CDPS2022
Práctica creativa 1 de la asignatura de CDPS curso académico 2021-2022.

ETSIT - UPM

## Introducción
Este entorno se tiene que desplegar en un directorio que contenga la imagen de disco *cdps-vm-base-pc1.qcow2* y el archivo *plantilla-vm-pc1.xml* con los ajustes y componentes.

## Ejecución
- Creamos las máquinas virtuales que vamos a utilizar en un rango de 1 a 5, conectándolas a la LAN correspondiente para generar el escenario.
~~~
python3 auto-p2.py prepare [1, 5]
~~~
- Arrancamos dichas máquinas virtuales con consola.
~~~
python3 auto-py.py launch
~~~
- Paramos la ejecución de las máquinas virtuales. 
~~~~
python3 auto-p2.py stop
~~~~
- Destruimos las máquinas virtuales junto con su imágen y archivo xml. 
~~~~
python3 auto-p2.py release
~~~~
