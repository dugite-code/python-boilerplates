from version import __version__ as version
from version import state

import platform
import argparse
import logging
import yaml
import os
import sys
from mako.template import Template
from mako.lookup import TemplateLookup
from bs4 import BeautifulSoup

def main( cfg, base, root ):
	tmpldir = os.path.join( root, cfg['Templates Directory'] )
	logger.debug( 'Templates Directory: ' + tmpldir )

	tmpllookup = TemplateLookup( directories=[ tmpldir ] )

	base_tmpl = os.path.join( root, cfg['Templates Directory'], base )
	logger.debug( 'Using Base Template: ' + base_tmpl )

	signature = Template( filename = base_tmpl, lookup = tmpllookup )

	outputdir = os.path.join( root, cfg['Output Directory'], base )
	if not os.path.exists(outputdir):
		os.makedirs(outputdir)

	for user in cfg['Users']:
			try:
				logger.debug( 'Parsing signature for: ' + user )
				output = BeautifulSoup( signature.render( name=user, position=cfg['Users'][user] ), "html.parser" ).prettify()
				filename = user.replace(" ", "_") + '.html'
				logger.debug( 'Storing signature for: ' + user + ' in ' + filename )
				outpath = os.path.join( outputdir, filename )
				logger.debug( 'Signature filepath: ' + outpath )
				try:
				   outfile = open( outpath,'w',encoding='utf-8' )
				   outfile.write( output )
				   outfile.close()
				   logger.debug( 'Signature writen for: ' + user )
				except:
				   logger.warning( 'Faile to open/write signature file for: ' + user)
			except:
			   logger.warning( 'Signature for: ' + user + ' failed')

if __name__ == '__main__':
	# Fetch root directory
	root = os.path.dirname (os.path.realpath( __file__ ) )

	congifg_file = os.path.join( root, 'config.yml' )

	parser = argparse.ArgumentParser()
	parser.add_argument( '-v',
							dest='version',
							action='store_true',
							default=False,
							help='Print Version Number' )
	parser.add_argument( '-t',
							dest='base',
							default='regular.tmpl',
							help='Base template to be used' )
	parser.add_argument( '-c',
							dest='config_file',
							default=congifg_file,
							help='Specify a different config file' )

	args = parser.parse_args()

	if args.version:
		print( "Version: " + version + " - " + state )
		exit()

	# Load the configuration yaml file
	with open( args.config_file, 'r' ) as ymlfile:
		cfg = yaml.safe_load( ymlfile )

	# Set up Logging
	logger = logging.getLogger( __name__ )

	log_file = os.path.join( root, cfg['Logging']['Logfile'] )
	# Create a Log file handler
	handler = logging.FileHandler( log_file )

	# Set Log Level
	level = logging.getLevelName( cfg['Logging']['Level'] )
	logger.setLevel( level )

	# Create a logging format
	formatter = logging.Formatter( '%(asctime)s %(levelname)s: %(message)s' )
	handler.setFormatter( formatter )

	# Add the handlers to the logger
	logger.addHandler( handler )
	logger.debug( 'Platform: ' + platform.system() )

	main( cfg, args.base, root )