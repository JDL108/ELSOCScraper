# Rubric Ticket Sniper README

## Setup

1. Install Python from python.org (Check "Add to PATH").
2. Open Terminal or Command Prompt.
3. Route to your folder: cd Documents/Personal/PythonStuff/ELSOCScraper
4. Install requirements: pip install requests selenium

## Edit Script Values

Open RubricScraper.py in a text editor and change:

* EVENT_ID = "64539"
* TICKETS_WANTED = 2

## Get Session ID

1. Go to campus.hellorubric.com and log in.
2. Press F12, go to the Console tab.
3. Paste this and press Enter: JSON.parse(localStorage.jStorage).sessionid
4. Copy the output code into the script: SESSION_ID = "your_code_here"

## Run

1. In your terminal, run: python RubricScraper.py
2. When tickets drop, a Chrome browser window will automatically launch with your cart. Complete the payment forms manually.
3. Press Ctrl+C in the terminal to stop the script.
