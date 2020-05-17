import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

DATE = 'date'
DATA_FILE = 'us_covid19_daily.csv'

st.write("### Covid-19 Data")
st.markdown(
"""
This chart shows Cumulative hospitalized and in ICU numbers by date
""")

@st.cache(persist=True)
def load_data(nrows):
    df = pd.read_csv(DATA_FILE, nrows=nrows)
    #lowercase = lambda x: str(x).lower()
    #data.rename(lowercase, axis="columns", inplace=True)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    return df

df = load_data(100)

# Filter date after March 20 as prior data has mostly NaNs
start_date = '03-20-2020'
mask = (df['date'] > start_date)
filtered_data = df.loc[df['date'] > start_date]

'''
fig1 = px.scatter(filtered_data, x="date", y="hospitalized", title="Hospitalized People",
            template="plotly_dark")
st.plotly_chart(fig1, use_container_width=True)
'''
#fig2 = px.line(filtered_data, x="date", y="death", title="Increase in Deaths")
fig = px.bar(filtered_data, x='date', y='hospitalized', title='Covid-19 Patient Statistics',
        hover_data=['inIcuCumulative','death'], color='death',
        labels={'inIcuCumulative': 'In Icu',
                'date': 'Date',
                'hospitalized': 'Hospitalized',
                'death': 'No. of Deaths'},
        template='plotly_dark')
fig.update(layout=dict(title=dict(x=0.5)))
st.plotly_chart(fig, use_container_width=True)

if st.checkbox('Show raw data'):
    filtered_data

