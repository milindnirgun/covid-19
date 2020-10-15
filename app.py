import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import datetime as dt
from vega_datasets import data

DATE = 'date'
# All data files with reference to sources

# https://covidtracking.com/ for daily numbers on covid data for individual states as well as national
STATES_DATA_FILE = 'data/us_states_covid19_daily.csv'
US_DATA_FILE = 'data/us_covid19_daily.csv'
# https://www.census.gov/data/tables/time-series/demo/popest/2010s-state-total.html for census data to get states' population
CENSUS_DATA_FILE = 'data/nst-est2019-alldata.csv'
# http://www.fonz.net/blog/archives/2008/04/06/csv-of-states-and-state-abbreviations/ for a list of states and abbreviations
US_STATES_FILE = 'data/all_states.csv'



# Need to add mtime by using hash_funcs to make sure the cache is rebuilt if the file has been modified
#@st.cache(persist=True)
def loadData(file):
    df = pd.read_csv(file)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    # Filter date after March 20 as prior data has mostly NaNs
    start_date = '03-20-2020'
    filtered_data = df.loc[df['date'] > start_date]
    return filtered_data

# Deprecated. Use loadData()
def load_c19_data(file):
    # read covid data first
    df = pd.read_csv(file)
    # convert the date column from input file to a datetime format
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    # Filter date after March 20 as prior data has mostly NaNs
    start_date = '03-20-2020'
    filtered_data = df.loc[df['date'] > start_date]
    
    # read census data for the states' 2019 population
    #pop-df = pd.read_csv(CENSUS_DATA_FILE, usecols='[]')
    return filtered_data

# Return data dictionary in Markdown
@st.cache(persist=True)
def getDataDict():

    return '''
    | Column Name | Desription |
    | ----------- | ---------- |
    | date        | Date for which the data applies |
    | state | Two letter state code |
    | positive | Total no. of people who have tested positive for COVID-19 so far |
    | negative | Total no. of people who have tested negative for COVID-19 so far |
    | pending | No. of tests whose results have yet to be determined |
    | hospitalizedCurrently | No. of people in hospital for COVID-19 on this day |
    | hospitalizedCumulative | Total no. of people who have gone to the hospital for COVID-19 so far, including those who have since recovered or died |
    '''

# Draw an area chart using Altair
def createAreaChart(df):
    area1 = alt.Chart(df).mark_area(opacity=0.3).encode(
                x="date:T",
                y=alt.Y("number:Q", stack=None),
                color=alt.Color("type:N", scale=alt.Scale(scheme='plasma'), legend=alt.Legend(title="Counts", orient="left"))
            ).properties(
                width=800, height=600
            )
    #area2 = area1.encode(
    #            y=alt.Y('deaths:Q')
    #        )
    #chart = area1 + area2
    return area1

# Draw a line chart with percent axis using Altair
# TODO - Add tooltip 
def createLineChart(df):
    return alt.Chart(df).mark_line().encode(
                x="date:T",
                y=alt.Y("number:Q", axis=alt.Axis(format='%')),
                color=alt.Color("type:N", scale=alt.Scale(scheme='plasma'), 
                            legend=alt.Legend(title="Counts", titleFontSize=14, orient="left", labelFontSize=14))
            ).properties(
                width=800, height=600
            )


# Draw an area chart with gradient using Altair
# deprecated - needs to be fixed
def type_gradient(df, type, color):
    return alt.Chart(df).transform_filter(
                f'datum.symbol==="{type}"'
            ).mark_area(
                line={'color':color},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                            alt.GradientStop(color=color, offset=1)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0
                )
            ).encode(
                x = alt.X('date:T', axis=alt.Axis(title='Weeks', titleFontSize=18, titlePadding=20, titleColor='gray')),
                y = alt.Y('number:Q', axis=alt.Axis(title='Number of Cases', titleFontSize=18, titlePadding=20, titleColor='gray'))
            )


# Create a bar chart for US Historical data using Plotly Express. Uses death column for color selection
def createBarChart(df):
    fig = px.bar(df, x='date', y='hospitalizedCurrently', 
                title='Number of people currently in hospitals across the USA',
                hover_data=['positive','inIcuCurrently','onVentilatorCurrently','death'], color='death',
                labels={'positive': 'Confirmed Cases',
                        'inIcuCurrently': 'In Icu',
                        'onVentilatorCurrently': 'On Ventilator',
                        'date': 'Date',
                        'hospitalizedCurrently': 'Hospitalized Count',
                        'death': 'Total No. of Deaths'},
                template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5), autosize=True))
    return fig

# Create a bar chart for US Historical data for positive cases using Plotly Express. Uses death column for color selection
def createPositiveBarChart(df):
    fig = px.bar(df, x='date', y='positive', 
                title='Number of people tested positive across the USA',
                hover_data=['hospitalizedCurrently','inIcuCurrently','onVentilatorCurrently','death'], color='death',
                labels={'hospitalizedCurrently': 'In Hospitals',
                        'inIcuCurrently': 'In Icu',
                        'onVentilatorCurrently': 'On Ventilator',
                        'date': 'Date',
                        'death': 'Total No. of Deaths'},
                template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5), autosize=True))
    return fig

# Create an Altair bar chart to show increments in positive cases over a weekly period
def createIncrementalBarChart(df):
    bar = alt.Chart(df).mark_bar(opacity=0.6).encode(
                x = alt.X("date:T", axis=alt.Axis(title='Date')),
                y = alt.Y("positive:Q", stack=None, axis=alt.Axis(title='Daily Change in confirmed Cases'))
            ).properties(
                width=800,
                height=600
            )
    line = alt.Chart(df).mark_line().encode(
            alt.X("date:T"),
            alt.Y("EMA:Q"),
            color=alt.value('red')
    )
    return (bar + line)

# Create a Chloropeth map of USA with States showing positive cases colored by death count
#TODO: add state code to be displayed for state using a centroid
def createCholorpeth(df):
    states = alt.topo_feature(data.us_10m.url, 'states')
    return alt.Chart(df).mark_geoshape().encode(
                shape=alt.Shape(field='geo', type='geojson'),
                color=alt.Color('normPositive:Q', 
                                scale=alt.Scale(scheme='reds'), legend=alt.Legend(title=["Confirmed Cases","per 100,000 People",""])),
                tooltip=[alt.Tooltip('state:N', title='State'), 
                        alt.Tooltip('positive:N', title='Confirmed Cases'), 
                        alt.Tooltip('death:N', title='Confirmed Deaths')]
            ).transform_lookup(
                lookup='id',
                from_=alt.LookupData(data=states, key='id'),
                as_='geo'
            ).properties(
                width=800,
                height=600
            ).project(
                type='albersUsa'
            )


# Normalize the data by calculating the figures for every 100,000 people 
def getNormalizedData(df):
    # normalize data for population of each state. The numbers are proportional to population size and
    # it is more meaningful to represent that instead of raw numbers
    df['normHospitalizedCur'] = np.around((df['hospitalizedCurrently']*100000/df['population']))
    df['normInIcuCur'] = np.around((df['inIcuCurrently']*100000/df['population']))
    df['normDeath'] = np.around((df['death']*100000/df['population']))
    df['normPositive'] = np.around((df['positive']*100000/df['population']))
    return df

# For each state, calculate the change in all the variables from previous day
def getIncrementalData(df):
    return

# Get a good dataframe for all States with their names, id, codes (two letter abbreviations), and population. The id
# value has to match with the states data from vega_datasets so use the population dataset from there as a reference
def getStatesPopulation():
    us_states_df = pd.read_csv(US_STATES_FILE)
    # Get census data for all us states and rename some columns
    col_list = ["STATE", "NAME", "POPESTIMATE2019"]
    census_df = pd.read_csv(CENSUS_DATA_FILE, usecols=col_list)
    census_df = census_df.rename(columns = {'STATE':'fips', 'NAME':'state', 'POPESTIMATE2019':'population'})
    # Get the population dataset from vega_datasets and merge with the us_states_df to combine the codes
    pop = data.population_engineers_hurricanes()
    pop.drop(['population','engineers', 'hurricanes'], axis=1, inplace=True)
    pop_df=pop.merge(us_states_df[['state','code']], on='state', how='inner')
    # Now merge with the census_df to add the latest population estimates from 2019
    census_df = census_df.convert_dtypes()
    pop_df = pop_df.merge(census_df[['state','population']], on='state', how='inner')

    return pop_df

# Get the daily data for all states
def getDailyData(pop_df):
    # Load daily state data and merge with states data
    daily_df = loadData(STATES_DATA_FILE)
    daily_df = daily_df.rename(columns={'state':'code'})
    pop_df.convert_dtypes()
    daily_df = pd.merge(daily_df, pop_df[['state','id', 'code','population']], on = 'code', how = 'inner')
    #daily_df.dropna(subset=['name'], inplace=True)
    #daily_df = getNormalizedData(daily_df)
    return daily_df

def getDayAsDatetime(day):
    minTime = dt.datetime.min.time()
    dateTimeObj = dt.datetime.combine(day, minTime)
    return dateTimeObj
    
# Get commulative confirmed cases on a given date
def getConfirmedCases(day):
    searchDate = getDayAsDatetime(day)
    cases = us_df.loc[us_df['date'] == searchDate, 'positive']
    return cases

# Return cummulative death count on a given date
def getConfirmedDeaths(day):
    searchDate = getDayAsDatetime(day)    
    deaths = us_df.loc[us_df['date'] == searchDate, 'death']
    return deaths.astype(int)

###################################
# Start main program
###################################

# Load US daily data file
us_df = loadData(US_DATA_FILE)
## cleanup of the dataframe - replace most of the NaN values with 0s
us_df['inIcuCumulative'].fillna(0, inplace=True)
# Get the most recent date from the us dataset as a datetime object
#latest_us_df_date = us_df['date'].max().to_pydatetime()
latest_us_df_date = us_df['date'].max()
prev_date = latest_us_df_date - dt.timedelta(days=1)

# Get daily data for all states
states_df = getStatesPopulation()
daily_df = getDailyData(states_df)
# Get a normalized version of daily_df which is calculates values per 100K 
normalizedDaily_df = getNormalizedData(daily_df)

# Get daily differential from all states daily data (STATES_DATA_FILE)
d_df = daily_df.groupby("date")
s = d_df['positive'].sum()    # gets a Series
d = pd.DataFrame(s.diff())    # gets the difference in values from previous day and create a dataframe
d['EMA'] = d.ewm(span=30, adjust=False).mean()  

d = d[2:]   # Remove first two elements (Nan)
d.reset_index(inplace=True)

##############################

#st.markdown("# **Covid-19 Data Visualization**")
st.title("Covid-19 Data Visualization")

st.markdown("This application shows different visualizations for the most current Covid-19 data. A selection of\
            different types of charts can be made in the sidebar to display the chart.")

cases = getConfirmedCases(latest_us_df_date)
prev_cases = getConfirmedCases(prev_date)
deaths = getConfirmedDeaths(latest_us_df_date)
prev_deaths = getConfirmedDeaths(prev_date)
header1 = "Confirmed Cases: **" + '{:,}'.format(cases[0]) + "**, change from previous day: **" + '{:,}'.format((cases[0] - prev_cases[1]))  + "**"

header2 = "Confirmed Deaths: **" + '{:,}'.format(deaths[0]) + "**, change from previous day: **" + '{:,}'.format((deaths[0] - prev_deaths[1]))  + "**"

st.write("**Number of confirmed cases and no. of deaths recorded to date with change from previous day for  -  ", 
        latest_us_df_date.strftime("%m/%d/%Y"),"**")
st.markdown(header1)
st.markdown(header2)


## Create a menu for selection
options_list = [
    'Hospitalized & Death Counts',
    'Confirmed Cases by State',
    'Cummulative Count of Positive Cases',
    'Daily Change in # of Positive Cases',
]
option = st.sidebar.selectbox(
    'Select a chart type below',
    options_list
)


# Hospitalized & Deaths
if (options_list.index(option) == 0):
    pchart = createBarChart(us_df)
    st.plotly_chart(pchart, use_container_width=True)

    if (st.checkbox('Display raw data')):
        st.write(us_df)

if (options_list.index(option) == 1):
    day_df = daily_df.loc[normalizedDaily_df['date'] == normalizedDaily_df['date'].max()]    
    states = alt.topo_feature(data.us_10m.url, 'states')

    cChart = createCholorpeth(day_df)
    st.altair_chart(cChart)
    st.write(day_df)
    
# Positive cases
if (options_list.index(option) == 2):
    positive_chart = createPositiveBarChart(us_df)
    st.plotly_chart(positive_chart, use_container_width=True)
    if (st.checkbox('Display raw data')):
        st.write(us_df)

# Percentage Change by Month
if (options_list.index(option) == 3):
    
    bChart = createIncrementalBarChart(d)
    st.altair_chart(bChart)
    st.markdown("The red line shows the exponential moving average over 30 days")
    if (st.checkbox('Display raw data')):
        st.write(us_df)

