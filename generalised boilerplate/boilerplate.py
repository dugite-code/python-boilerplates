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

def main():
	print( "Boiler Plate" )

# Modified from https://stackoverflow.com/a/27974027
def sanitize( data ):
	if not isinstance( data, ( dict, list ) ):
		return data
	if isinstance( data, list ):
		return [ v for v in ( sanitize(v) for v in data ) if v ]
	return { k: v for k, v in ( (k, sanitize( v ) ) for k, v in data.items() ) if v is not None }

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
						'Logfile' : 'boilerplate.log'
						} }

	# Load the configuration yaml file
	with open( args.config_file, 'r' ) as ymlfile:
		cfg_file = yaml.safe_load( ymlfile )

	cfg_user = sanitize( cfg_file )

	# Modified from: https://stackoverflow.com/a/29241297
	config = { k: dict( cfg_default.get( k, {} ), **cfg_user.get( k, {} ) )
				for k in cfg_default.keys() | cfg_user.keys()
			}

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

	main()