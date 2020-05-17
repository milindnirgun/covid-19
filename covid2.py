import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

DATE = 'date'
DATA_FILE = 'us_covid19_daily.csv'

st.write("### Covid-19 Data")
st.markdown(
"""
This chart shows Cumulative hospitalized and in ICU numbers by date
""")

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_FILE, nrows=nrows)
    #lowercase = lambda x: str(x).lower()
    #data.rename(lowercase, axis="columns", inplace=True)
    data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
    return data

data = load_data(100)

fig1 = go.Figure()

fig1.add_trace(go.Scatter(x=data['date'], y=data['hospitalized'], name="Hospitalized",
                    line=dict(color='firebrick', width=4)))
fig1.add_trace(go.Scatter(x=data['date'], y=data['recovered'], name="Recovered",
                    line=dict(color='royalblue', width=4)))
fig1.update_layout(title='Hospitalized Stats',
                    xaxis_title='Date', yaxis_title='No. of people')

st.plotly_chart(fig1, use_container_width=True)

fig2 = go.Figure()

fig2.add_trace(go.Scatter(x=data['date'], y=data['death'], name="Increase in Death",
                    line=dict(color='firebrick', width=4)))
#fig1.add_trace(go.Scatter(x=data['date'], y=data['inIcuCumulative'], name="In ICU",
                    #line=dict(color='royalblue', width=4)))
#fig1.add_trace(go.Scatter(x=data['date'], y=data['onVentilatorCumulative'], name="On Ventilator",
                    #line=dict(color='green', width=4)))
fig2.update_layout(title='Deaths Reported',
                    xaxis_title='Date', yaxis_title='No. of people')

st.plotly_chart(fig2, use_container_width=True)
if st.checkbox('Show raw data'):
    data

