import urllib.request

#Download states file from covidtracking.com
US_STATES_FILE = 'data/all_states.csv'
URL1 = "https://covidtracking.com/api/v1/states/"
URL2 = "/daily.csv"
DEST_FILE1 = "./data/states/"
DEST_FILE2 = "_counties_counties_daily19.csv"

