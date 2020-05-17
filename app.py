import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

DATE = 'date'
DATA_FILE = 'data/us_covid19_daily.csv'

st.markdown('## Corona virus impact in the USA')
st.markdown('This webpage attempts to graphically visualize current pandemic data \
for informational purpose.')

@st.cache(persist=True)
def load_data(nrows):
    df = pd.read_csv(DATA_FILE, nrows=nrows)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    # Filter date after March 20 as prior data has mostly NaNs
    start_date = '03-20-2020'
    filtered_data = df.loc[df['date'] > start_date]
    return filtered_data

df = load_data(100)

option = st.sidebar.selectbox(
    'Select a chart type below',
    ('Patient Statistics','Death Statistics')
)

if (option == 'Patient Statistics'):
    fig = px.bar(df, x='date', y='hospitalized', title='Covid-19 Patient Statistics',
            hover_data=['inIcuCumulative','death'], color='death',
            labels={'inIcuCumulative': 'In Icu',
                    'date': 'Date',
                    'hospitalized': 'Hospitalized',
                    'death': 'No. of Deaths'},
            template='plotly_dark')
    fig.update(layout=dict(title=dict(x=0.5)))

    st.plotly_chart(fig, use_container_width=True)
    if (st.checkbox('Display raw data')):
        st.write(df)



