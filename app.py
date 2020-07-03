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
# Calls type_gradient to construct area for each variable
# deprecated - needs to be fixed
def createGradientChart(df):
    return alt.layer(
        type_gradient(df, 'positive', 'darkred'),
        type_gradient(df, 'deaths', 'darkgreen')
    ).encode(
        alt.Stroke('type', scale=alt.Scale(domain=['positive', 'deaths'], range=['darkred', 'darkgreen']))
    )


def createLayeredChart(df):
    chart = alt.Chart(df).mark_area(opacity=0.3).encode(
                x = "date:T",
                y = alt.Y("number:Q", stack=None),
                color = "type:O"
            )
    return chart


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

# Create a Chloropeth map of USA with States showing positive cases colored by death count
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


# Create a scatter chart for a given day to plot the number of positive cases for each state per 100,000 of population
def createStateScatterChart(df, day):
    day_df = df.loc[df['date'] == day]
    fig = px.scatter(day_df, x='name',y='normPositive', title='Positive cases identified per 100,000 of population',
                 size='death',
                 labels={'date': 'Date',
                         'normPositive': 'Total Number of Positive Cases per 100K',
                         'death': 'No. of Deaths',
                         'name': 'States',
                         'normHospitalizedCur': 'No. of hospitalized per 100K on this day'},
                 template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5)))
    fig.update_xaxes(tickangle=45)
    return fig

# Create a stacked bar chart for a given day showing number of people hospitalized and in ICU
def createStateBarChart(df, day):
    
    day_df = df.loc[df['date'] == day]

    fig = go.Figure(data=[
            go.Bar(name='Hospitalized', x=day_df['name'], y=day_df['normHospitalizedCur'], 
                    marker=dict(
                        color='rgba(246, 78, 139, 0.6)',
                        line=dict(color='rgba(246, 78, 139, 1.0)', width=1)
                    )),
            go.Bar(name='In ICU', x=day_df['name'], y=day_df['normInIcuCur'], 
                    marker=dict(
                        color='rgba(58, 71, 80, 0.6)',
                        line=dict(color='rgba(58, 71, 80, 0.8)', width=1)
                    ))
            ])
    fig.update_layout(template='plotly_white', barmode='stack')
    fig.update_xaxes(tickangle=45)
    return fig

# Returns a weekly summary dataframe by resampling. Works for US Daily data
def getWeeklySummary(df):
    tmp_df = df.set_index("date", inplace=False)
    weekly_df = pd.DataFrame()
    weekly_df['Confirmed'] = tmp_df.positive.resample('W').last()
    weekly_df['Deaths'] = tmp_df.death.resample('W').last()
    #weekly_df.reset_index(inplace=True)
    return weekly_df


# Returns a weekly summary dataframe of positive, recovered and deaths variables from the main US dataframe.
# This returns a melted dataframe which is useful for stacked area charts
def getMeltedDf(df):
    weekly_df = getWeeklySummary(df)
    weekly_df.reset_index(inplace=True)
    perc_df = wkly_summ_us.pct_change()
    perc_df.dropna(inplace=True)
    # Drop first 2 rows because the first few weeks from late March to mid April data was starting to be more 
    # accurate and hence shows a greater percentage increase making the later numbers seem insignificant.
    perc_df = perc_df[2:]
    perc_df.reset_index(inplace=True)
    ret_df = perc_df.melt(id_vars=['date'], var_name='type', value_name='number')
    ret_df.dropna(subset=['number'], inplace=True)
    return ret_df

# Normalize the data by calculating the figures for every 100,000 people 
def normalizeData(df):
    # normalize data for population of each state. The numbers are proportional to population size and
    # it is more meaningful to represent that instead of raw numbers
    df['normHospitalizedCur'] = np.around((df['hospitalizedCurrently']*100000/df['population']))
    df['normInIcuCur'] = np.around((df['inIcuCurrently']*100000/df['population']))
    df['normDeath'] = np.around((df['death']*100000/df['population']))
    df['normPositive'] = np.around((df['positive']*100000/df['population']))
    return df

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
    #daily_df = normalizeData(daily_df)
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

# Load US data file into dataframes
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
normalizedDaily_df = normalizeData(daily_df)

# summarize weekly for the whole dataset - this does not work for grouping by states
wkly_summ_us = getWeeklySummary(us_df)
pct_change_df = wkly_summ_us.pct_change()
pct_change_df.dropna(inplace=True)
# Drop first 2 rows because the first few weeks from late March to mid April data was starting to be more 
# accurate and hence shows a greater percentage increase making the later numbers seem insignificant.
pct_change_df = pct_change_df[2:]

##############################
# Setup for monthly Area Chart
melted_summ_us = getMeltedDf(us_df)
months = ['April', 'May', 'June']


#st.markdown("# **Covid-19 Data Visualization**")
st.title("Covid-19 Data Visualization")

st.markdown("This application shows different visualizations for the most current Covid-19 data. A selection of\
            different types of charts can be made in the sidebar to display the chart.")
st.write("**Most recent data showing confirmed cases and deaths in the United States for  -  ", 
        latest_us_df_date.strftime("%m/%d/%Y"),"**")

cases = getConfirmedCases(latest_us_df_date)
prev_cases = getConfirmedCases(prev_date)
deaths = getConfirmedDeaths(latest_us_df_date)
prev_deaths = getConfirmedDeaths(prev_date)
header1 = "**Confirmed Cases: **" + '{:,}'.format(cases[0]) + "....change from yesterday: " + '{:,}'.format((cases[0] - prev_cases[1]))

header2 = "**Confirmed Deaths: **" + '{:,}'.format(deaths[0]) + "....change from yesterday: " + '{:,}'.format((deaths[0] - prev_deaths[1]))


st.subheader(header1)
st.subheader(header2)


## Create a menu for selection
options_list = [
    'Hospitalized & Deaths',
    'Confirmed Cases across USA',
    'Weekly Percentage Change',
    'Percentage Change by Month',
    'Confirmed Cases by State'
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

# Confirmed Cases across USA
if (options_list.index(option) == 1):
    day_df = daily_df.loc[normalizedDaily_df['date'] == normalizedDaily_df['date'].max()]    
    states = alt.topo_feature(data.us_10m.url, 'states')

    cChart = createCholorpeth(day_df)
    st.altair_chart(cChart)
    
# Weekly Percentage Change
if (options_list.index(option) == 2):
    # Get the string for selected month and find the index in the months list with the chosen option and add 3 to get the value of month
    mth = st.sidebar.selectbox('Select a month', months)
    melted_summ_us = melted_summ_us.loc[melted_summ_us['date'].dt.month == months.index(mth)+4]

    st.altair_chart(createLineChart(melted_summ_us))
    #st.line_chart(pct_change_df)
    #aChart = createAreaChart()
    #aChart = createLayeredChart(melted_summ_us)

    #st.altair_chart(aChart)
    if (st.checkbox('Display raw data')):
        st.write(pct_change_df)

# Percentage Change by Month
if (options_list.index(option) == 3):
    # Get the string for selected month and find the index in the months list with the chosen option and add 3 to get the value of month
    mth = st.sidebar.selectbox('Select a month', months)
    melted_summ_us = melted_summ_us.loc[melted_summ_us['date'].dt.month == months.index(mth)+4]

    aChart = createAreaChart(melted_summ_us)
    st.altair_chart(aChart)

    if (st.checkbox('Display raw data')):
        st.write(melted_summ_us)

if (option == 'Confirmed Cases by State'):

    sChart = createStateScatterChart(states_df, '06-20-2020')
    st.plotly_chart(sChart, use_container_width=True)

    bChart = createStateBarChart(states_df, '06-20-2020')
    st.plotly_chart(bChart, use_container_width=True)

    if (st.checkbox('Display raw data')):
        st.write(states_df)
        if (st.checkbox('Display Data Dictionary')):
            st.write(getDataDict())

