#!/usr/bin/python3
import sys
import json
import os
from lxml import etree
from subprocess import call
from pathlib import Path

path = "/mnt/tmp/pc1/"

if len(sys.argv) > 1:
    orden = sys.argv[1]
    nServer = 0

    if orden == "prepare":
        nServer = 3
        if len(sys.argv) == 3:
            param = int(sys.argv[2])
            if (param >= 1 and param <= 5):
                nServer = param
            else:
                #lanzamos una excepción
                raise ValueError("Número de servidores fuera de rango")
        if len(sys.argv) > 3:
            raise ValueError("Demasiados argumentos")
        
        #Metemos en el json el número de servidores
        Path(path).mkdir(exist_ok=True) #Creamos el directorio si no existe
        os.chdir(path)        
        jsonData = []
        jsonData.append({
            "num_serv" : nServer
        })
        fout = open("auto-p2.json", "w") #MIRAR BIEN SI OPEN TAMBIEN CREA
        json.dump(jsonData, fout) #dump: python a json
                                    #loads : json a python
        fout.close()
        
        def conf(nombreMaquina):
            call (['qemu-img', 'create', '-f', 'qcow2', '-b', 'cdps-vm-base-pc1.qcow2', nombreMaquina+'.qcow2'])
            call (['cp', 'plantilla-vm-pc1.xml', nombreMaquina+'.xml'])
            tree = etree.parse(nombreMaquina+'.xml')
            root = tree.getroot()
            name = root.find('name')
            name.text = nombreMaquina
		            
        
            pathChange = root.find("./devices/disk/source[@file='/mnt/tmp/XXX/XXX.qcow2']")
            bridgeChange = root.find("./devices/interface/source[@bridge='XXX']")
            pathChange.set("file",path+nombreMaquina+".qcow2")

            primeraLetra = str(nombreMaquina)[0]
            if primeraLetra == 's':
                bridgeChange.set('bridge', "LAN2")
            elif primeraLetra == 'c':
                bridgeChange.set('bridge', "LAN1")
            elif primeraLetra == 'l':
                bridgeChange.set('bridge', "LAN1")
                    
            if (nombreMaquina == 'lb'):
                nuevaEtiqueta = etree.Element("interface")
                nuevaEtiquetaCambio = root.find("devices")
                nuevaEtiquetaCambio.append(nuevaEtiqueta)
                nuevaEtiqueta.set('type', "bridge")
                etree.SubElement(nuevaEtiqueta, "source", bridge = "LAN2")
                etree.SubElement(nuevaEtiqueta, "model", type = "virtio")
            
            fout = open(nombreMaquina+".xml","w")
            fout.write(etree.tounicode(tree, pretty_print=True))
            fout.close()

            #Tras modificar todos los xml, definimos las maquinas
            call(['sudo', 'virsh', 'define', nombreMaquina+".xml"])
        
        

        for i in range(1, nServer + 1):
            conf('s'+str(i))
        conf('c1')
        conf('lb')

        call(['sudo', 'brctl', 'addbr', 'LAN1'])
        call(['sudo', 'brctl', 'addbr', 'LAN2'])
        call(['sudo', 'ifconfig', 'LAN1', 'up'])
        call(['sudo', 'ifconfig', 'LAN2', 'up'])

        # Configuracion de las IPs:
        # Primero metemos el nombre de la maquina en el fichero /etc/hostname
        for i in range(1, nServer + 1):
            fout = open("hostname", "w") #Creamos un fichero hostname en nuestro host
            fout.write("s"+str(i))
            fout.close()
            call(['sudo', 'virt-copy-in', '-a', 's'+str(i)+'.qcow2', 'hostname', '/etc']) #Enviamos el fichero hostname a las maquinas virtuales
            call(['rm','-f', 'hostname'])

        fout = open("hostname", "w") 
        fout.write("c1")
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'c1.qcow2', 'hostname', '/etc'])
        call(['rm','-f', 'hostname'])

        fout = open("hostname", "w")
        fout.write("lb")
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'lb.qcow2', 'hostname', '/etc'])
        call(['rm', '-f', 'hostname'])

        # Editamos fichero /etc/hosts
        for i in range(1, nServer + 1):
            call(['sudo', 'virt-copy-out', '-a', 's'+str(i)+'.qcow2', '/etc/hosts', '.']) #Traemos el fichero /etc/hosts de las maquinas a nuestro host
            call(['mv', 'hosts', 'hostsOnlyRead'])
            fin = open('hostsOnlyRead', 'r')
            fout = open('hosts', 'w')
            for line in fin: #Escribimos linea por linea el fichero, modificando la linea correspondiente
                if '127.0.1.1' in line:
                    fout.write('127.0.1.1 s'+str(i)+'\n')
                else:
                    fout.write(line) 
            fin.close()
            fout.close()
            call(['sudo', 'virt-copy-in', '-a', 's'+str(i)+'.qcow2', 'hosts', '/etc'])
            call(['rm', '-f', 'hosts', 'hostsOnlyRead'])

        call(['sudo', 'virt-copy-out', '-a', 'c1.qcow2', '/etc/hosts', '.']) 
        call(['mv', 'hosts', 'hostsOnlyRead'])
        fin = open('hostsOnlyRead', 'r')
        fout = open('hosts', 'w')
        for line in fin:
            if '127.0.1.1' in line:
                fout.write('127.0.1.1 c1 \n')
            else:
                fout.write(line)
        fin.close()
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'c1.qcow2', 'hosts', '/etc'])
        call(['rm', '-f', 'hosts', 'hostsOnlyRead'])

        call(['sudo', 'virt-copy-out', '-a', 'lb.qcow2', '/etc/hosts', '.'])
        call(['mv', 'hosts', 'hostsOnlyRead'])
        fin = open('hostsOnlyRead', 'r')
        fout = open('hosts', 'w') 
        for line in fin:
            if '127.0.1.1' in line:
                fout.write('127.0.1.1 lb \n')
            else:
                fout.write(line)
        fin.close()
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'lb.qcow2', 'hosts', '/etc'])
        call(['rm', '-f', 'hosts', 'hostsOnlyRead'])

        # Configuracion de red. En la practica 2 se hace con ifconfig en la consola de cada maquina, pero aqui lo que hacemos es modificar el fichero /etc/network/interfaces
        
        for i in range(1, nServer + 1):
            fout = open("interfaces", "w") #Creamos un fichero interfaces en nuestro host
            fout.write("auto lo \n iface lo inet loopback \n auto eth0 \n iface eth0 inet static \n address 10.0.2.1"+str(i)+"\n netmask 255.255.255.0 \n gateway 10.0.2.1")
            fout.close()
            call(['sudo', 'virt-copy-in', '-a', 's'+str(i)+'.qcow2', 'interfaces', '/etc/network']) #Enviamos el fichero interfaces a las maquinas virtuales
            call(['rm', '-f', 'interfaces'])

        fout = open("interfaces", "w")
        fout.write("auto lo \n iface lo inet loopback \n auto eth0 \n iface eth0 inet static \n address 10.0.1.2 \n netmask 255.255.255.0 \n gateway 10.0.1.1")
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'c1.qcow2', 'interfaces', '/etc/network'])
        call(['rm', '-f', 'interfaces'])

        fout = open("interfaces", "w")
        fout.write("auto lo \n iface lo inet loopback \n auto eth0 \n iface eth0 inet static \n address 10.0.1.1 \n netmask 255.255.255.0 \n auto eth1 \n iface eth1 inet static \n address 10.0.2.1 \n netmask 255.255.255.0")
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'lb.qcow2', 'interfaces', '/etc/network'])
        call(['rm', '-f', 'interfaces'])

        # En lb configuramos el archivo /etc/sysctl.conf -> hay que descomentar la linea #net.ipv4.ip_forward=1
        call(['sudo', 'virt-copy-out', '-a', 'lb.qcow2', '/etc/sysctl.conf', '.'])
        call(['mv', 'sysctl.conf', 'sysctlOnlyRead.conf'])
        fin = open('sysctlOnlyRead.conf', 'r')
        fout = open('sysctl.conf', 'w')
        for line in fin:
            if '#net.ipv4.ip_forward=1' in line:
                fout.write('net.ipv4.ip_forward=1')
            else:
                fout.write(line)
        fin.close()
        fout.close()
        call(['sudo', 'virt-copy-in', '-a', 'lb.qcow2', 'sysctl.conf', '/etc'])
        call(['rm', '-f', 'sysctl.conf', 'sysctlOnlyRead.conf'])


        # Configuramos tambien en nuestro host:
        call(['sudo', 'ifconfig', 'LAN1', '10.0.1.3/24'])
        call(['sudo', 'ip', 'route', 'add', '10.0.0.0/16', 'via', '10.0.1.1'])

        # Modificar las paginas web (para diferenciarlas)
        for i in range(1, nServer + 1):
            fout = open("index.html", "w") #Creamos un fichero index.html en nuestro host
            fout.write("s"+str(i)+"\n")
            fout.close()
            call(['sudo', 'virt-copy-in', '-a', 's'+str(i)+'.qcow2', 'index.html', '/var/www/html']) #Enviamos el fichero a las maquinas virtuales
            call(['rm', '-f', 'index.html'])




    elif orden == "launch":
        fout = open("auto-p2.json", "r")
        conf = json.load(fout)
        nServer = int(conf[0]["num_serv"]) #Primero objeto del json (nombre-clave)
        fout.close()

        # Arrancamos las maquinas virtuales
        # Trabajamos con  os.system de forma sustitutiva a call para abrir las consolas
        for i in range(1, nServer + 1):
            call(['sudo', 'virsh', 'start', 's'+str(i)])
            #call(['xterm', '-e', 'sudo virsh console s'+str(i), '&'])
            os.system("xterm -e 'sudo virsh console s'"+str(i)+" &")
        call(['sudo', 'virsh', 'start', 'c1'])
        #call(['xterm', '-e', 'sudo virsh console c1', '&'])
        os.system("xterm -e 'sudo virsh console c1' &")
        call(['sudo', 'virsh', 'start', 'lb'])
        #call(['xterm', '-e', 'sudo virsh console lb', '&'])
        os.system("xterm -e 'sudo virsh console lb' &")


    elif orden == "stop":
        fout = open("auto-p2.json", "r")
        conf = json.load(fout)
        nServer = int(conf[0]["num_serv"]) #Primero objeto del json (nombre-clave)
        fout.close()

        for i in range(1, nServer + 1):
            call(['sudo', 'virsh', 'shutdown', 's'+str(i)])
        call(['sudo', 'virsh', 'shutdown', 'c1'])
        call(['sudo', 'virsh', 'shutdown', 'lb'])


    elif orden == "release":
        fout = open("auto-p2.json", "r")
        conf = json.load(fout)
        nServer = int(conf[0]["num_serv"]) # Primer objeto del json (nombre-clave)
        fout.close()
        
        #Destruimos las maquinas
        for i in range(1, nServer + 1):
            call(['sudo', 'virsh', 'destroy', 's'+str(i)])
            call(['sudo', 'virsh', 'undefine', 's'+str(i)])
            call(['rm', '-f', 's'+str(i)+'.xml'])
            call(['rm', '-f', 's'+str(i)+'.qcow2'])
        call(['sudo', 'virsh', 'destroy', 'c1'])
        call(['sudo', 'virsh', 'destroy', 'lb'])

        #Borramos todos los archivos excepto las plantillas y el auto-p2.py
        call(['sudo', 'virsh', 'undefine', 'c1'])
        call(['sudo', 'virsh', 'undefine', 'lb'])
        call(['rm', '-f', 'c1.xml'])
        call(['rm', '-f', 'lb.xml'])
        call(['rm', '-f', 'c1.qcow2'])
        call(['rm', '-f', 'lb.qcow2'])

        call(['rm', '-f', 'auto-p2.json'])
        
        #Borramos tambien las LAN!
        call(['sudo', 'ifconfig', 'LAN1', 'down'])
        call(['sudo', 'ifconfig', 'LAN2', 'down'])
        call(['sudo', 'brctl', 'delbr', 'LAN1'])
        call(['sudo', 'brctl', 'delbr', 'LAN2'])



