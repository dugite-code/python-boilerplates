import sys
if sys.version_info[0] < 3:
	raise Exception( "Python 3 is required to run" )

from version import __version__ as version
from version import state

import platform
import argparse
import logging
import yaml
import os
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout
import time
import threading

class BotTasks(object):

	def __init__( self ):
		self.options = { 'help':'help', 'echotest':'test', 'curtime':'time'}
		logger.debug( 'Enabled options' )

	def enabled_options( self ):
		return self.options

	def help( self, msg=None, help=False  ):
		if( help is True ):
			return "Display this help screen"

		logger.debug( 'Getting help' )
		help_message = "@" + msg['mucnick']
		help_message += (
			" Available Options\n"
			"=============================================\n"
		)
		help_message += "help           " + self.help( help=True ) + "\n\n"
		for key, opt in self.options.items():
			if key != 'help':

				help_message += str( opt ).ljust(15,' ')
				action = getattr( self, key )
				help_message += " " + action( help=True ) + "\n\n"

		help_message += "goodbye         I'll wait till you call me next\n\n"
		help_message += "============================================="

		return help_message

	def echotest( self, msg=None, help=False ):
		if( help is True ):
			return "Echo your message back to you"
		return msg['body']

	def curtime( self, msg=None, help=False ):
		if( help is True ):
			return "Returns the current time"
		return str( time.strftime("%c") )


class testBot( ClientXMPP ):

	def __init__( self, jid, password, room, nick, ltime ):
		ClientXMPP.__init__( self, jid, password )
		self.room = room
		self.nick = nick
		self.listen = False
		self.lextend = None
		self.ltime = ltime
		self.tasks = BotTasks()

		self.add_event_handler( "session_start", self.start )
		self.add_event_handler( "groupchat_message", self.muc_message )
		self.add_event_handler( "muc::%s::got_online" % self.room, self.muc_online )

	def start( self, event ):
		self.get_roster()
		self.send_presence()
		self.plugin['xep_0045'].joinMUC( self.room,
										self.nick,
										wait=True )

	def stop_listening( self, msg ):
		if time.time() <= ( self.lextend + 20 ):
			logger.info( 'Extending Listening')
			self.start_listening( msg, notif=False )
		elif self.listen == True:
			logger.info( 'Stop Listening')
			self.listen = False
			self.listento = None
			self.send_message( 	mto=msg['from'].bare,
								mbody="Call on me with @%s when you need me" % ( self.nick ), mtype='groupchat' )

	def listen_timer( self, msg ):
		logger.info( 'Starting Timer' )
		time.sleep( self.ltime )
		logger.info( 'Not Listening' )
		self.stop_listening( msg )

	def start_listening( self, msg, notif=True ):
		logger.info( 'Listening to ' +  msg['mucnick'] )
		self.listen = True
		self.listento = msg['mucnick']
		if notif == True:
			self.send_message( mto=msg['from'].bare,
								mbody="@%s I'm Listening for %s seconds" % ( msg['mucnick'], str( self.ltime ) ), mtype='groupchat' )
		ltimer_thread = threading.Thread(target=self.listen_timer, kwargs={ 'msg': msg })
		ltimer_thread.start()

	def opt_match( self, msg ):
		message = msg['body'].replace(self.nick, "")
		for key, opt in self.tasks.enabled_options().items():
			if opt in message:
				logger.info( 'Option Match: ' + opt )
				action = getattr( self.tasks, key )
				return_message = action( msg )
				logger.debug( 'Return message: ' + return_message )
				self.send_message( mto=msg['from'].bare,
									mbody=return_message, mtype='groupchat' )
		self.lextend = time.time()

	def muc_message( self, msg ):
		logger.debug( 'New Message: ' + msg['body'] )
		if msg['mucnick'] != self.nick and self.listen == True and self.listento in msg['mucnick']:
			if 'goodbye' in msg['body']:
				self.lextend = 0
				self.stop_listening( msg )
			else:
				self.opt_match( msg )

		elif msg['mucnick'] != self.nick and self.nick in msg['body'] and self.listen == False:
			self.start_listening( msg )
			self.opt_match( msg )

	def muc_online( self, presence ):
		if presence['muc']['nick'] != self.nick:
			logger.info( 'Welcomeing ' +  presence['muc']['nick'] )
			self.send_message( mto=presence['from'].bare,
								mbody="Hello, %s %s call me with @testbot" % ( presence['muc']['role'],
								presence['muc']['nick'] ), mtype='groupchat')

# Modified from https://stackoverflow.com/a/27974027
def sanitize( data ):
	if not isinstance( data, ( dict, list ) ):
		return data
	if isinstance( data, list ):
		return [ v for v in ( sanitize(v) for v in data ) if v ]
	return { k: v for k, v in ( (k, sanitize( v ) ) for k, v in data.items() ) if v is not None }

# From https://stackoverflow.com/a/7205672
def mergedicts(dict1, dict2):
	for k in set(dict1.keys()).union(dict2.keys()):
		if k in dict1 and k in dict2:
			if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
				yield (k, dict(mergedicts(dict1[k], dict2[k])))
			else:
				# If one of the values is not a dict, you can't continue merging it.
				# Value from second dict overrides one in first and we move on.
				yield (k, dict2[k])
				# Alternatively, replace this with exception raiser to alert you of value conflicts
		elif k in dict1:
			yield (k, dict1[k])
		else:
			yield (k, dict2[k])

if __name__ == '__main__':
	# Fetch root directory
	root = os.path.dirname (os.path.realpath( __file__ ) )

	congifg_file = os.path.join( root, 'config.yml' )

	parser = argparse.ArgumentParser()
	parser.add_argument( '-v', '--version',
							dest='version',
							action='store_true',
							default=False,
							help='Print Version Number' )
	parser.add_argument( '-q', '--quiet',
							dest='quiet',
							action='store_true',
							default=False,
							help='Disable console output' )
	parser.add_argument( '-c', '--configuration',
							dest='config_file',
							default=congifg_file,
							help='Specify a different config file' )

	args = parser.parse_args()

	if args.version:
		print( "Version: " + version + " - " + state )
		exit()

	# Set default configuration options
	cfg_default = { 'Logging Settings' : {
						'Level' : 'WARNING',
						'Log to Console' : True,
						'Log to File' : False,
						'Logfile' : 'xbot.log'
						} }

	# Load the configuration yaml file
	with open( args.config_file, 'r' ) as ymlfile:
		cfg_file = yaml.safe_load( ymlfile )

	cfg_user = sanitize( cfg_file )

	config = dict( mergedicts(cfg_default,cfg_user) )

	del cfg_default
	del cfg_user

	# Set up Logging
	logger = logging.getLogger( __name__ )

	log_file = os.path.join( root, config['Logging Settings']['Logfile'] )

	# Set Log Level
	level = logging.getLevelName( config['Logging Settings']['Level'] )
	logger.setLevel( level )

	# Create a logging format
	formatter = logging.Formatter( '%(asctime)s %(levelname)s: %(message)s' )

	# Add the handlers to the logger
	if config['Logging Settings']['Log to File']:
		logfile_handler = logging.FileHandler( log_file )
		logfile_handler.setFormatter( formatter )
		logger.addHandler( logfile_handler )

	if config['Logging Settings']['Log to Console'] and not args.quiet:
		console_handler = logging.StreamHandler()
		console_handler.setFormatter( formatter )
		logger.addHandler( console_handler )

	# Enable/Disable Logging
	logger.disabled = not config['Logging Settings']['Enabled']

	logger.info( 'Platform: ' + platform.system() )
	logger.info( "Version: " + version + " - " + state )
	if state != 'stable':
		logger.warning( "State is not stable: " + state )

	xmpp = testBot(
					config['Server Settings']['Username'],
					config['Server Settings']['Password'],
					config['Server Settings']['Room'],
					config['Server Settings']['Nickname'],
					config['Bot Settings']['Listen Time']
	)

	xmpp.register_plugin('xep_0030') # Service Discovery
	xmpp.register_plugin('xep_0045') # Multi-User Chat
	xmpp.register_plugin('xep_0199') # XMPP Ping

	if xmpp.connect( ( config['Server Settings']['Server'], config['Server Settings']['Port'] ) ):
		xmpp.process(block=True)
		print("Done")
	else:
		print("Unable to connect.")
