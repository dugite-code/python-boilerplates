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
						'Logfile' : 'boilerplate.log'
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

	main()