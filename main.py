#!/usr/bin/python3
from pydbus import SystemBus
import paho.mqtt.client as mqtt
from gi.repository import GLib
import configparser
import sys

config = configparser.ConfigParser()
config.read(sys.argv[1])

knownNumbers = config["signal"]["knownNumbers"].replace(" ", "").split(",")
ownNumber = config["signal"]["ownNumber"]

mqttConfig = {
	"host": config["mqtt"]["host"],
	"port": int(config["mqtt"]["port"]),
	"clientId": "signalGateway" + ownNumber[-3:],
	"username": config["mqtt"]["username"],
	"password": config["mqtt"]["password"],
"caCert": config["mqtt"]["caCert"] if config.has_option("mqtt", "caCert") else "",
	"notifyPresence": True if config["mqtt"]["notifyPresence"] == "1" else False
}

class MqttSignal:
	def __init__(self):
		self._bus = SystemBus()
		self._signal = self._bus.get('org.asamk.Signal', '/org/asamk/Signal/' + ownNumber.replace("+", "_")) #('org.asamk.Signal', '/org/asamk/Signal/_number')
		self._signal.onMessageReceived = self._onSignalMsg
		c = {}
		c["/help"] = { "fn": self._onSignalHelp, "info": "Shows all commands available" }
		c["/ping"] = { "fn": self._onMqttPing, "info": "Sends mqtt publish and returns a /pong if it was received back" }
		self._signalCommands = c

		#mqtt
		self._mqtt = mqtt.Client(mqttConfig["clientId"])
if len(mqttConfig["caCert"]) > 0:
			self._mqtt.tls_set(mqttConfig["caCert"])
			self._mqtt.tls_insecure_set(True)
		self._mqtt.username_pw_set(mqttConfig["username"], mqttConfig["password"])
		if mqttConfig["notifyPresence"]:
			self._mqtt.will_set("clients/" + mqttConfig["clientId"], "0", 0, True)
		self._mqtt.on_connect = self._onMqttConnect
		self._mqtt.on_message = self._onMqttMessage
		self._mqtt.connect_async(mqttConfig["host"], mqttConfig["port"])

	#signal

	def _sendSignalMsg(self, message, to):
		self._signal.sendMessage(message, [], [to])

	def _onSignalMsg(self, timestamp, source, groupID, message, attachments):
		if(not source in knownNumbers):
			return

		if(len(message) == 0): #happens if you send a attachment without text
			return
		elif(message[0] == "/"):
			args = message.split(" ")
			cmd = args[0]
			if(cmd in self._signalCommands):
				self._signalCommands[cmd]["fn"](timestamp, source, args[1:])
			else:
				self._sendSignalMsg('Use /help to get information about the provided commands', source)
		else:
			self._publishMqtt("signal/from/" + source[1:], message)
		
	def _onSignalHelp(self, timestamp, source, params):
		m = ""
		for c in self._signalCommands:
			m += c + " - " + self._signalCommands[c]["info"] + "\n"
		self._sendSignalMsg(m, source)

	def _onMqttPing(self, timestamp, source, params):
		self._publishMqtt("signal/ping", source)
	
	#mqtt

	def _publishMqtt(self, topic, message, qos=0, retain=False):
		self._mqtt.publish(topic, message, qos, retain)

	def _onMqttConnect(self, client, userdata, flags, rc):
		if mqttConfig["notifyPresence"]:
			self._publishMqtt("clients/" + mqttConfig["clientId"], "1", 0, True)
		self._mqtt.subscribe("signal/ping", 2)
		for n in knownNumbers:
			self._mqtt.subscribe("signal/to/" + n[1:])
	
	def _onMqttMessage(self, client, userdata, m):
		m.payload = m.payload.decode("UTF-8")
		if(m.topic == "signal/ping"):
			self._onMqttPong(m)
		elif(m.topic.find("signal/to/") != -1):
			receiver = "+" + m.topic.split("/")[-1:][0]
			if(receiver in knownNumbers):
				self._sendSignalMsg(m.payload, receiver)

	def _onMqttPong(self, m):
		if(m.payload in knownNumbers):
			self._sendSignalMsg("/pong", m.payload)

	def loop(self):
		self._mqtt.loop_start()

	
MQTTSIGNAL = MqttSignal()
MQTTSIGNAL.loop()
loop = GLib.MainLoop()
loop.run()
