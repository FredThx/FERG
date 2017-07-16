#!/usr/bin/env python
# -*- coding:utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')

from FUTIL.my_logging import *

import paho.mqtt.client as paho

class node_red_dashboard():
	''' A la fois un client mqtt et un lien vers un tableau de bord géré par node-red.
	'''
	def __init__(self, base_topic, mqtt_host='localhost', mqtt_port=1883):
		'''Initialisation
				- base_topic		:	racine des topics qui seroint envoyés (ex : 'T-HOME/FERG/'
				- mqtt_host			:	broker mqtt
				- mqtt_port			:	port du broker mqtt
		'''
		logging.debug('node_red_dashboard created')
		if base_topic[-1] == '/':
			self.base_topic = base_topic
		else:
			self.base_topic = base_topic + '/'
		self.mqtt_client = paho.Client()
		self.mqtt_client.on_connect = self.on_connect
		try:
			self.mqtt_client.connect(mqtt_host, mqtt_port, 60)
		except Exception as e:
			logging.error("Mqtt error: %s"%(e))
		
	@staticmethod
	def on_connect(client, userdata, flags, rc):
		'''Callback fonction when connect
		'''
		if rc == 0:
			logging.info('Connection au broker MQTT.')
		else:
			logging.error('Connection refused by MQTT broker with result code ' + rc)
	
	def publish(self, topic='', value=''):
		'''Publie un message MQTT(base_topic+topic, value)
		'''
		try:
			self.mqtt_client.reconnect()
			self.mqtt_client.publish(topic = self.base_topic+topic,payload = value) #TODO : gerer qos et retain
		except Exception as e:
			logging.error("Error on node_red_dashboard.publish(%s,%s): %s"%(topic,value,e))