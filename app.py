import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import altair as alt

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

# Draw an area chart using Altair
def createAreaChart():
    area1 = alt.Chart(wkly_summ_us.reset_index()).mark_area(opacity=0.3).encode(
                x="date:T",
                y="positive:Q"
            ).properties(
                width=800, height=600
            )
    area2 = area1.encode(
                y=alt.Y('recovered:Q')
            )
    chart = area1 + area2
    return chart

# Draw an area chart with gradient using Altair
def createGradientChart():
    area1 = alt.Chart(wkly_summ_us.reset_index()).transform_filter(
                'datum.positive > 0'
            ).mark_area(
                line={'color':'darkred'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                            alt.GradientStop(color='darkred', offset=1)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0
                )
            ).encode(
                x = alt.X('date:T', axis=alt.Axis(title='Weeks', titleFontSize=18, titlePadding=20, titleColor='gray')),
                y = alt.Y('positive:Q', axis=alt.Axis(title='Positive Cases', titleFontSize=18, titlePadding=20, titleColor='gray'))
            )
    area2 = area1.mark_area(
                line={'color':'darkgreen'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                            alt.GradientStop(color='darkgreen', offset=1)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0
                )
            ).encode(
                y = alt.Y('recovered:Q', axis=alt.Axis(title='Recovered Cases', titleFontSize=18))
            )
    chart = area1 + area2
    retChart = chart.properties(
                width=800, height=600,
                title='Weekly Summary of Positive vs. Recovered Cases in the US'
            ).configure_title(fontSize=24, color='gray', align='center')
    return retChart

def createLayeredChart(df):
    chart = alt.Chart(df).mark_area(opacity=0.3).encode(
                x = "date:T",
                y = alt.Y("number:Q", stack=None),
                color = "type:O"
            )
    return chart


# Create a bar chart for US Historical data using Plotly Express
def createUSChart(df):
    fig = px.bar(df, x='date', y='hospitalizedCurrently', 
                title='Total Daily Covid-19 Figures Across the USA',
                hover_data=['inIcuCurrently','onVentilatorCurrently','death'], color='death',
                labels={'inIcuCurrently': 'In Icu',
                        'onVentilatorCurrently': 'On Ventilator',
                        'date': 'Date',
                        'hospitalizedCurrently': 'People in Hospital',
                        'death': 'No. of Deaths'},
                template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5), autosize=True))
    return fig
    

def createStateChart(day):
    df = getStates()
    day_df = df.loc[df['date'] == day]
    fig = px.scatter(day_df, x='name',y='normHospitalizedCur', title='Covid-19 Patients Status',
                 size='death',
                 template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5)))
    fig.update_xaxes(tickangle=45)
    return fig

def getWeeklySummary(df):
    tmp_df = df.set_index("date", inplace=False)
    weekly_df = pd.DataFrame()
    weekly_df['positive'] = tmp_df.positive.resample('W').last()
    weekly_df['recovered'] = tmp_df.recovered.resample('W').last()
    #wkly_summ_us.reset_index('date')
    weekly_df['deaths'] = tmp_df.death.resample('W').last()
    return weekly_df

def getMeltedDf(df):
    tmp_df = df.set_index("date", inplace=False)
    weekly_df = pd.DataFrame()
    weekly_df['positive'] = tmp_df.positive.resample('W').last()
    weekly_df['recovered'] = tmp_df.recovered.resample('W').last()
    #wkly_summ_us.reset_index('date')
    weekly_df['deaths'] = tmp_df.death.resample('W').last()
    weekly_df.reset_index(inplace=True)
    ret_df = weekly_df.melt(id_vars=['date'], var_name='type', value_name='number')
    return ret_df

# Normalize the data by calculating the figures for every 100,000 people 
def normalizeData(df):
    # normalize data for population of each state. The numbers are proportional to population size and
    # it is more meaningful to represent that instead of raw numbers
    df['normHospitalizedCur'] = np.around((df['hospitalizedCurrently']*100000/df['popestimate2019']))
    df['normInIcuCur'] = np.around((df['inIcuCurrently']*100000/df['popestimate2019']))
    df['normDeath'] = np.around((df['death']*100000/df['popestimate2019']))
    df['normPositive'] = np.around((df['positive']*100000/df['popestimate2019']))
    return df

# Get normalized data for all States 
def getStates():
    us_states_df = pd.read_csv(US_STATES_FILE)
    # Get census data for all us states
    col_list = ["STATE", "NAME", "POPESTIMATE2019"]
    census_df = pd.read_csv(CENSUS_DATA_FILE, usecols=col_list)
    census_df = census_df.rename(columns = {'STATE':'fips', 'NAME':'state', 'POPESTIMATE2019':'popestimate2019'})
    # do an outer join to get state abbreviations
    states_df = census_df[['state', 'popestimate2019']].merge(us_states_df[['state', 'code']], on = 'state', how = 'left')
    states_df = states_df.rename(columns={'state':'name','code':'state'})
    #states_df.head(15)
    # Load daily state data and merge with states data
    daily_df = load_c19_data(STATES_DATA_FILE)
    daily_df = pd.merge(daily_df, states_df[['state','name','popestimate2019']], on = 'state', how = 'left')
    daily_df = normalizeData(daily_df)

    return daily_df

# Start main program

# Load data files into dataframes
us_df = loadData(US_DATA_FILE)
## cleanup of the dataframe - replace most of the NaN values with 0s
us_df['inIcuCumulative'].fillna(0, inplace=True)

# summarize weekly for the whole dataset - this is not grouping for states
#wkly_summ_us = getWeeklySummary(us_df)
#wkly_summ_us.head(10)
melted_summ_us = getMeltedDf(us_df)

option = st.sidebar.selectbox(
    'Select a chart type below',
    ('US Historical Statistics', 'US Recovery Rates', 'Hospitalized with Death Counts by State')
)

if (option == 'US Historical Statistics'):
    pchart = createUSChart(us_df)
    st.plotly_chart(pchart, use_container_width=True)

    if (st.checkbox('Display raw data')):
        st.write(us_df)

if (option == 'US Recovery Rates'):
    #st.write(melted_summ_us)
    #aChart = createAreaChart()
    #aChart = createGradientChart()
    aChart = createLayeredChart(melted_summ_us)

    st.altair_chart(aChart)
    if (st.checkbox('Display raw data')):
        st.write(wkly_summ_us)
    
if (option == 'Hospitalized with Death Counts by State'):

    barChart = createBarChart()

