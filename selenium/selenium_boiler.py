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
import traceback

import csv
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.webdriver import FirefoxProfile

# Import selenium exceptions
from selenium.common.exceptions import InsecureCertificateException
from selenium.common.exceptions import TimeoutException

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

def waitforid( waitelement ):
	element = WebDriverWait( driver, 20 ).until(
	EC.presence_of_element_located( ( By.ID, waitelement ) )
	)
	return

def waitforxpath( waitelement ):
	element = WebDriverWait( driver, 200 ).until(
	EC.presence_of_element_located( ( By.XPATH, waitelement ) )
	)
	return

def main( driver, config ):
	try:
		logger.debug( 'Opening URL: ' + config['Url'] )
		driver.get( config['Url'] ) # Open main webpage
	except InsecureCertificateException:
		raise Exception( 'Critical Fail: ' + str( InsecureCertificateException ) )

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
						'Enabled' : True,
						'Level' : 'WARNING',
						'Log to Console' : True,
						'Log to File' : False,
						'Logfile' : 'selenium_boiler.log'
						},
					'Virtual Display' : False,
					'Close Browser' : True}

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

	# Set system paths
	if config['Binary']['In project root']:
		gecko = os.path.join( root, config['Binary']['Geckodriver'] )
	else:
		gecko = os.path.realpath( config['Binary']['Geckodriver'] )

	dwnld = os.path.join( root, config['Folders']['Download Folder'] ) # Download folder

	if not os.path.exists(dwnld):
		os.makedirs(dwnld)

	pfile = os.path.join( root, config['Folders']['Profile Folder'] ) # Firefox profile folder

	# MIME List from: https://www.iana.org/assignments/media-types/media-types.xml
	# Code from: https://stackoverflow.com/a/16503661
	columns = defaultdict(list) # each value in each column is appended to a list
	csvfile = os.path.join( root, config['MIME']['CSV File'] )

	with open(csvfile) as f:
		reader = csv.DictReader(f) # read rows into a dictionary format
		for row in reader: # read a row as {column1: value1, column2: value2,...}
			for (k,v) in row.items(): # go over each column name and value
				columns[k].append(v) # append the value into the appropriate list
									 # based on column name k

	mimelist=";".join(columns[ config['MIME']['Column name'] ])

	if config['Virtual Display']:
		from pyvirtualdisplay import Display
		# Start the pyvirtualdisplay
		display = Display( visible=0, size=( 800, 600 ) )
		display.start()

	try:
		# Browser Profile
		fp = webdriver.FirefoxProfile(pfile)
		fp.set_preference( "browser.download.folderList", 2 )
		fp.set_preference( "browser.download.manager.showWhenStarting", False )
		fp.set_preference( "browser.download.dir", dwnld )
		fp.set_preference( "browser.helperApps.neverAsk.saveToDisk", mimelist ) #Set firefox to never ask when downloading csv files
		driver = webdriver.Firefox( executable_path=gecko, firefox_profile=fp )
		driver.set_window_size( 1024, 768 )
		driver.implicitly_wait( 120 ) # Measured in seconds

	except Exception as e:
		logger.error( 'Critical Fail: ' + str( e ) )
		driver.quit()
		if config['Virtual Display']:
			display.stop()

	try:
		main( driver, config )
	except Exception as e:
		try:
			driver.save_screenshot( './err_screenshot.png' )
		except Exception as e2:
			logger.error( 'Unable to produce Screenshot: ' + str( e2 ) )
		logger.error( 'Critical Fail: ' + str( e ) )

	if config['Close Browser']:
		driver.quit()
	if config['Virtual Display']:
		display.stop()