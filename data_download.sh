#!/bin/bash

date=`date`
LOGFILE="./download_track.log"

# This uses relative path so run it in the code base directoy (covid)
# Download US daily data
curl https://api.covidtracking.com/v1/us/daily.csv -o ./data/us_covid19_daily.csv
if [ $? -ne 0 ]; then
    echo "$(date): Download us_covid19_daily failed" >> $LOGFILE
else
    echo "$(date): Download us_covid19_daily succeeded" >> $LOGFILE
fi

# Download all States daily data
curl https://api.covidtracking.com/v1/states/daily.csv -o ./data/us_states_covid19_daily.csv
if [ $? -ne 0 ]; then
    echo "$(date): Download us_states_covid19_daily failed" >> $LOGFILE
else
    echo "$(date): Download us_states_covid19_daily succeeded" >> $LOGFILE
fi

# Download County data for California from
# https://api.covidtracking.com/v1/states/ca/daily.csv
curl https://api.covidtracking.com/v1/states/ca/daily.csv -o ./data/ca_counties_covid19_daily.csv
if [ $? -ne 0 ]; then
    echo "$(date): Download ca_counties_covid19_daily failed" >> $LOGFILE
else
    echo "$(date): Download ca_counties_covid19_daily succeeded" >> $LOGFILE
fi

exit 0
