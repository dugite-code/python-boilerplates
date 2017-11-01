import yaml
import os
import sys

from pyvirtualdisplay import Display

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.webdriver import FirefoxProfile

def what_hppend(StopNo):
    ts = datetime.datetime.now().isoformat()
    print ( ts, "Critical Fail: Refer to debug screenshot screen" + StopNo + ".png" )
    driver.save_screenshot( './screen' + StopNo + ".png" )
    driver.quit()
    display.stop()
    exit()

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

def main():
    # Fetch root directory
    root = os.path.dirname(os.path.realpath(__file__))

    # Load the configuration yaml file
    with open( os.path.join( root, "config.yml" ), 'r' ) as ymlfile:
        cfg = yaml.safe_load( ymlfile )

    # Set system paths
    dwnld = os.path.join( root, "downloads" ) # Download folder
    pfile = os.path.join( root, "profile" ) # Firefox profile folder

    # Start the pyvirtualdisplay
    display = Display( visible=0, size=( 800, 600 ) )
    display.start()

    try:
        # Browser Profile
        fp = webdriver.FirefoxProfile(pfile)
        fp.set_preference( "browser.download.folderList", 2 )
        fp.set_preference( "browser.download.manager.showWhenStarting", False )
        fp.set_preference( "browser.download.dir", dwnld )
        fp.set_preference( "browser.helperApps.neverAsk.saveToDisk", "text/csv" ) #Set firefox to never ask when downloading csv files
        driver = webdriver.Firefox( firefox_profile=fp )
        driver.set_window_size( 1024, 768 )
        driver.implicitly_wait( 120 ) # Measured in seconds
        actions = webdriver.ActionChains( driver )

    except:
        print("Critical Fail: Failed to load webbrowser")
        what_hppend("0")

    # Attempt to load url
    try:
        driver.get( cfg['Url'] ) # Open main webpage

    except:

        try:
            ts = datetime.datetime.now().isoformat()
            print ( ts, "Log: Re-attempting load Main Page" )
            driver.refresh() # Re-fresh webpage

        except:
            ts = datetime.datetime.now().isoformat()
            print ( ts, "Critical Fail: Failed to load Main Page" )
            what_hppend( "1" )

    # iframe password selection example.
    try:
        driver.switch_to.frame( "login" ) # Switch to the Login iframe

        driver.find_element_by_id( "username" ).send_keys( cfg['Username'] ) # Enter username
        driver.find_element_by_id( "password" ).send_keys( cfg['Password'] ) # Enter password
        driver.find_element_by_name( "password" ).send_keys( Keys.RETURN ) # Press the RETURN key

    except:
        ts = datetime.datetime.now().isoformat()
        print ( ts, "Critical Fail: Failed to enter username and password" )
        what_hppend( "2" )

    # Wait for element with id PageHead to be loaded
    try:
        waitforid( "PageHead" )

    except:

        try:
            ts = datetime.datetime.now().isoformat()
            print ( ts, "Log: Re-attempting to load First Page" )
            driver.refresh() # Re-fresh webpage
            waitforid( "mastHead" )

        except:
            ts = datetime.datetime.now().isoformat()
            print ( ts, "Critical Fail: Failed to load First Page" )
            what_hppend( "3" )

    # Click a download button
    try:
    	driver.find_element_by_xpath("//select[@class='button']/option[text()='Download']").click()
        time.sleep(10)

    except:
        ts = datetime.datetime.now().isoformat()
        print ( ts, "Critical Fail: Failed to click Download Button" )
        what_hppend( "4" )

if __name__ == '__main__':
    main()
