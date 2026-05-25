# Rubric Ticket Sniper README
This requires google chrome to be installed on your computer, not tested for mac currently. 
## Setup

1. Install Python from python.org (Check "Add to PATH").
2. Open Terminal or Command Prompt.
3. Route to where your folder has been downloaded to and ensure python is running in the environment
4. Install requirements: pip install requests selenium

## Edit Script Values

Open RubricScraper.py in a text editor and ensure these lines are uncommented, feel free to change ticket amount (ensure its below the purcahse max) or event id if you want to use this scraper for another purcahse:

* EVENT_ID = "64539"
* TICKETS_WANTED = 2

## Get Session ID

1. Go to campus.hellorubric.com and ensure that you are logged in.
2. Press F12, go to the Console tab.
3. Paste this and press Enter: 
```
JSON.parse(localStorage.jStorage).sessionid
```
4. Copy the output code into the script: SESSION_ID = "PASTE_SESSION_ID_HERE" (around line 23)

## Run
Make sure you start running the script about a minute or five before the tickets to drop, you could keep it running a day before but you might get IP banned.

1. In your terminal, run: python RubricScraper.py
2. When tickets drop, a Chrome browser window will automatically launch with your cart. Complete the payment forms manually. The cart request has already been sent 15ms after the order goes through, it's now sitting in your cart and you have 10 minutes to purchase the ticket
3. Press Ctrl+C in the terminal to stop the script. 
