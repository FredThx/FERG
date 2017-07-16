FERG Lib  Une bibliotheque pour Gerer - analyse les energies d'un maison individuelle
========================================================================

	Hardware :
		- Raspberry Pi (ou pcduino)
		- arduino ou atmega328, ou ...
		- compteur edf de type antique (avec une roue)
		- detecteur de bande noire du compteur (détecteur optique QRD1114)
		- tores SCT013 30A
		- detecteur de tension maison (voir schéma) à base de résistance, condensateur, diode et optocoupleur.
		- modules de transmission de données 433 Mhz
		- capteurs de température numériques DS18x20
		- capteur ultrason HRLV MaxSonar EZ pour lecture niveau cuve fuel
		- microcontroleur ATMEGA328 pour gérer les sondes (température, cuve fuel) et envoyer les infos au Rpi
		- convertisseur analogique / numérique MCP3008 pour lecture analogique sur Rpi
		- led, cables, ......
		- eventuellement un serveur nas pour base de données
	
	Software :
		- bibliotheque FGPIO pour gestion de tout le matériel ci-dessus
		- bibliotheque FUTIL pour débogage
		- python avec plein de lib.
		- php, MyQsql
		

Installation :
     pip install FERG
	 installer la base de données MySQL ou Mariadb ou .....
	 
	 mettre en place les 3 deamons
		- sur Rpi : lecture des températures
		- sur Rpi : lecture du compteur
		- sur serveur Bdd : alertes

