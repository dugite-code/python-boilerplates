# Selenium Interactive

Python 3
Requires firefox, [geckodriver](https://github.com/mozilla/geckodriver/releases) and selenium

```
python -i interactive.py
>>> driver.get("https://google.com")
>>>
>>> waitforid("logo-sub", 30)
>>>
>>> waitforxpath("//div[#id='logo-sub']", 30)
>>>
>>> pagedump("google_homepage.html")
>>>
>>> driver.quit()

```

A quick and dirty interactive setup for Selenium. Loads MIME types from `application.csv` downloaded from https://www.iana.org/assignments/media-types/media-types.xml and sets to download without prompts.

3 Helpers are included: `waitforid('id', [optional time int])`, `waitforxpath('xpath', [optional time int])` and `pagedump('Filename')`