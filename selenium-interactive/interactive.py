import logging
import yaml
import os
import csv
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

def pagedump( cfg, filename ):
	if cfg['Logging']['Page Dump']:
		dumppath = os.path.join( root, cfg['Folders']['Page Dump'], filename )
		dumpfile = open( dumppath,'w',encoding='utf-8' )
		dumpfile.write( driver.page_source )
		dumpfile.close()
	return

def waitforid( waitelement, waittime=30 ):
	element = WebDriverWait( driver, waittime ).until(
		EC.presence_of_element_located( ( By.ID, waitelement ) )
	)
	return

def waitforxpath( waitelement, waittime=10 ):
	element = WebDriverWait( driver, waittime ).until(
		EC.presence_of_element_located( ( By.XPATH, waitelement ) )
	)
	return

root = os.path.dirname (os.path.realpath( __file__ ) )
config_file = os.path.join( root, 'config.yml' )
with open( config_file, 'r' ) as ymlfile:
	cfg = yaml.safe_load( ymlfile )

dwnld = os.path.join( root, cfg['Folders']['Download'] )
pfile = os.path.join( root, cfg['Folders']['Profile'] )

if cfg['Binary']['In project root']:
	gecko = os.path.join( root, 'bin', cfg['Binary']['Geckodriver'] )
else:
	gecko = os.path.realpath( cfg['Binary']['Geckodriver'] )


# MIME List from: https://www.iana.org/assignments/media-types/media-types.xml
# Code from: https://stackoverflow.com/a/16503661
columns = defaultdict(list) # each value in each column is appended to a list
csvfile = os.path.join( root, cfg['MIME']['CSV File'] )

with open(csvfile) as f:
    reader = csv.DictReader(f) # read rows into a dictionary format
    for row in reader: # read a row as {column1: value1, column2: value2,...}
        for (k,v) in row.items(): # go over each column name and value
            columns[k].append(v) # append the value into the appropriate list
                                 # based on column name k

mimelist=";".join(columns[ cfg['MIME']['Column name'] ])
print(mimelist)

fp = webdriver.FirefoxProfile( pfile )
fp.set_preference( "browser.download.folderList", 2 )
fp.set_preference( "browser.download.manager.showWhenStarting", False )
fp.set_preference( "browser.download.dir", dwnld )
fp.set_preference( "browser.helperApps.neverAsk.saveToDisk", mimelist )
driver = webdriver.Firefox( executable_path=gecko, firefox_profile=fp )
driver.set_window_size( 1024, 768 )
actions = webdriver.ActionChains( driver )
print('Ready for selenium commands')