#!/usr/bin/env python
# -*- coding:utf-8 -*
'''
	Fichier de configuration pour FERG
	
	Déclaration de l'installation
	
	
'''
#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FGPIO')
sys.path.insert(0,'../FUTIL')

try:
	from FGPIO.mcp300x_hspi_io import *
	from FGPIO.SCT013_v_io import *
	from FGPIO.relay_io import *
	from FGPIO.lcd_i2c_io import *
	from FGPIO.lum_capteur_io import *
	from FGPIO.buzz_io import *
	from FERG.compteur_edf import *
except ImportError: 
	pass
	
from FERG.tempeDB import *
from FERG.installation import *
from FERG.circuit import *
import FUTIL.mails

def get_installation(physical_device = True):
	'''Renvoie une installation configurée
		si physical_device == False : on ne déclara pas les capteurs, mais uniquement le "squelette" de l'installation
	'''
	#
	#########################################################
	#														#
	#				BASE DE DONNEES							#
	#														#
	#########################################################
	#
	# Base de données pour les consos electriques
	db_elect = conso_electriqueDB( \
					db_name = 'tempeDB', \
					user = 'fred', \
					passwd='achanger', \
					host = '192.168.10.10', \
					mail = FUTIL.mails.gmail(gmail_account='fredthx@gmail.com', gmail_pwd='GaZoBuMeuh'))
	#
	#########################################################
	#														#
	#				MATERIEL								#
	#														#
	#########################################################
	#
	nom_compteur = 'General'
	
	if physical_device:		
		# Nano pc : un Raspberry (ou pcduino)
		pc = rpiduino_io()
		#
		#Le capteur heure creuse est réalisé avec un detecteur de tension
		# Il fonctionne comme un bouton poussoir vers la masse.
		capteur_heure_creuse = bt_io(pc.bcm_pin(24))
		#
		#Convertisseur Analogique/Numérique pour lecture analogique sur Rpi
		mcp3008 = mcp3008_hspi_io()
		#
		# Detecteur optique pour detection bande noire sur roue du compteur edf
		capteur_roue = qrd1114_analog_io(mcp3008.pin[0])
		#
		# Led qui s'allume quand la bande noire de la roue est détectée
		led = led_io(pc.bcm_pin(16))
		#
		# Vieux compteur EDF
		compteur = compteur_edf( \
					capteur = capteur_roue, \
					capteur_hc = capteur_heure_creuse, \
					led = led, \
					intensity_max = 45, \
					energy_tr = 2.5, \
					nb_tours_mesure = 10, \
					counter = db_elect.get_last_counter(nom_compteur)*1000 )
		#
		# Les tores pour mesurer le courant sur différences circuits
		tores = {'circuit_1': SCT013_v_io(mcp3008.pin[1], Imax = 30.0, Vmax = 1.0), \
					'circuit_ce': SCT013_v_io(mcp3008.pin[2], Imax = 30.0, Vmax = 1.0), \
					'circuit_frigo': SCT013_v_io(mcp3008.pin[3], Imax = 30.0, Vmax = 1.0) \
					}
		#
		#Relais de delestage du chauffe eau
		deleste_chauffe_eau = relay_io(pc.bcm_pin(12))
		deleste_chauffe_eau.off() # off : circuit fermé (pas de délestage)
		#
		#Buzzer pour alertes
		buzzer = buzz_io(pc.bcm_pin(25))
		
	else:
		tores = {'circuit_1': None, \
					'circuit_ce': None, \
					'circuit_frigo': None, \
					}
		compteur = None
		deleste_chauffe_eau = None
		buzzer = None
	
	# Circuit général avec Compteur EDF de type vieux!
	circuit_0 = circuit_general( \
		nom = nom_compteur, \
		puissance_maxi = 10000,
		energie_maxi_jour = 50000, \
		compteur = compteur)
	#########################################################
	#														#
	#				LES CIRCUITS							#
	#														#
	#########################################################
	#
	
	#Circuits secondaires mesurés
	
	circuit_1 = circuit_mesure( \
			nom = 'circuit_1', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 2000, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_1'])

	circuit_ce = circuit_mesure( \
			nom = 'circuit_ce', \
			parent = circuit_1, \
			puissance_maxi = 1500, \
			energie_maxi_jour = 7000, \
			compteur = tores['circuit_ce'], \
			delest = deleste_chauffe_eau, \
			puissance_typique = 1300)

	circuit_frigo = circuit_mesure( \
			nom = 'circuit_frigo', \
			parent = circuit_0, \
			eclatable = True, \
			puissance_maxi = 350, \
			energie_maxi_jour = 3000, \
			compteur = tores['circuit_frigo'])
	
	circuits_mesures = [circuit_0, circuit_1, circuit_ce, circuit_frigo]
		
	# Circuit physique (ou appareil) non mesuré
	
	congelateur = electric_device( \
			nom = 'Congelateur', \
			parent = circuit_frigo, \
			puissance_maxi = 130, \
			energie_maxi_jour = 1500, \
			puissance_typique = 110, \
			#max_average_power = 0.75*110
			)
	
	refrigerateur = electric_device( \
			nom = 'Refrigerateur', \
			parent = circuit_frigo, \
			puissance_maxi = 230, \
			energie_maxi_jour = 2800, \
			puissance_typique = 190, \
			#max_average_power = 0.75*190
			)
			
	buanderie = electric_device( \
			nom = 'Buanderie_chaufferie', \
			parent = circuit_1)
	
	electric_devices = [congelateur, refrigerateur, buanderie]
	
	#
	#########################################################
	#														#
	#				L'INSTALLATION							#
	#														#
	#########################################################
	#
	return installation( \
				db = db_elect, \
				circuits_mesures = circuits_mesures,
				electric_devices = electric_devices, 
				seuil_delestage = 8000, \
				buzzer = buzzer)