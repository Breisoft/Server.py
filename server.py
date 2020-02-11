from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketClientProtocol, WebSocketClientFactory, WebSocketServerFactory, listenWS

from twisted.internet.protocol import ReconnectingClientFactory

from twisted.internet import reactor, ssl
from twisted.internet.task import LoopingCall

from client_helper import ClientHandler

import time
import django_checker

import threading


import signal

import os

import custom_logging

handler = ClientHandler()


class SocketServer(WebSocketServerProtocol):
	
		def __init__(self):
				self.client_handler = handler

		def onConnect(self, request):
				logging.info("Client connecting: {0}".format(request.peer))
				self.client_handler.add_client(self)

		def onOpen(self):
				logging.info("WebSocket connection open.")
				
		def doSendMessage(self, message):
				payload = message.encode('utf-8')
				self.sendMessage(payload, False)

		def onMessage(self, payload, isBinary):				
				
				if isBinary:
						logging.info("Binary message received: {0} bytes".format(len(payload)))
				else:
						message = payload.decode('utf8')
						self.client_handler.process_message_received(self, message)


		def onClose(self, wasClean, code, reason):
				logging.info("WebSocket connection closed: {0}".format(reason))
				self.client_handler.remove_client(self)
				
				
class SocketClient(WebSocketClientProtocol):
	

		def onConnect(self, request):
				logging.info("Client connecting: {0}".format(request.peer))
				self.doSendMessage("SID1234")
				#self.client_handler.add_client(self)

		def onOpen(self):
				logging.info("WebSocket connection open.")
				
		def doSendMessage(self, message):
				payload = message.encode('utf-8')
				self.sendMessage(payload, False)

		def onMessage(self, payload, isBinary):				
				
				if isBinary:
						logging.info("Binary message received: {0} bytes".format(len(payload)))
				else:
						message = payload.decode('utf8')
						#self.client_handler.process_message_received(self, message)


		def onClose(self, wasClean, code, reason):
				logging.info("WebSocket connection closed: {0}".format(reason))
				#self.client_handler.remove_client(self)

class SocketClientFactory(WebSocketClientFactory, ReconnectingClientFactory):

		protocol = SocketClient
		maxDelay = 10
		maxRetries = 5000

		def clientConnectionFailed(self, connector, reason):
				print("Client connection failed .. retrying ..")
				self.retry(connector)

		def clientConnectionLost(self, connector, reason):
				print("Client connection lost .. retrying ..")
				self.retry(connector)

				
if __name__ == '__main__':

	import sys

	from twisted.python import log
		
	import custom_logging
		
	log.startLogging(sys.stdout)
	
	custom_logging.setup_logger()
	logging = custom_logging.get()
			
	
	def background_loop_thread():
			while True:
					handler.run_background_loop()
					time.sleep(10)
						
				
	def messager_loop():
			handler.run_messager_loop()
									
						
	def update_checker_loop():
			#django_checker.do_check_update()
			logging.info("ssag")
	
	
	contextFactory = ssl.DefaultOpenSSLContextFactory('ssl/key.pem','ssl/cert.pem')

	factory = WebSocketServerFactory("wss://0.0.0.0:443")
	
	factory.setProtocolOptions(
				maxConnections=100,
        allowedOrigins=[
            "https://app.bitomated.com:443",
        ]
    )
	factory.protocol = SocketServer
	
	listenWS(factory, contextFactory)
	
	factory_client = SocketClientFactory("wss://198.211.103.170:443")
	#factory_client.protocol = SocketClient
	context_client_factory = ssl.ClientContextFactory()
	
	def keyboardInterruptHandler(signal, frame):
			logging.info("Force quitting (ID: {}). Ending program...".format(signal))
			os._exit(1)

	signal.signal(signal.SIGINT, keyboardInterruptHandler)	
	

	try:
			background_thread = threading.Thread(target = background_loop_thread)
			background_thread.start()	
		
			reactor.listenSSL(8080, factory, contextFactory)
			reactor.connectSSL("198.211.103.170", 443, factory_client, context_client_factory)
			
			loop_messager = LoopingCall(messager_loop)
			loop_messager.start(0.5)
			loop_update_checker = LoopingCall(update_checker_loop)
			loop_update_checker.start(30)
			
			reactor.run()	
			
			background_thread.join()

			
	except KeyboardInterrupt:
			logging.info("Exiting...")
