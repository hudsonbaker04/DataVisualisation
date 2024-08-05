import pandas as pd

data: pd.DataFrame = pd.read_csv('geo_data_centers_cleaned.csv', sep=',')  # read in csv data

data.drop(columns=['Unnamed: 0.1'], inplace=True)  # remove useless columns
data.drop(columns=['Unnamed: 0'], inplace=True)

# print(data.columns)
# print(data.info())

location_data: pd.DataFrame = data[data['latitude'].notna() & data['longitude'].notna()]  # drop data centres that were not geocoded successfully

def clean_total_power(value) -> float:
    '''Convert the power column to float values.'''
    if pd.isna(value):  # nan values are set to zero
        return 0.0
    if isinstance(value, str):  # remove erroneous data bits
        value = value.replace('MW', '').strip()
    try:
        value = float(value)  # convert to float
        if value > 1000000:  # account for incorrect units
            value /= 1000000
        elif value > 100:
            value /= 1000
        return value
    except ValueError:
        return 0.0  # set to zero if exception occurs

location_data['total power (MW)'] = location_data['total power (MW)'].apply(clean_total_power)  # clean the power column by applying the above function

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css', 'styles.css'])  # create dash application and reference bootstrap layout style sheet

app.layout = html.Div(className='main-container', children=[
    html.Div(className='top-row', children=[
        html.Div(className='col-5', children=[
            html.H1('Visualising Global Data Centres'),
            html.P(
                '''
                This is a dashboard to facilitate exploration of data centre
                locations and statistics globally. Note that some data is not
                openly available as these facilities are privately owned.
                
                This is a dashboard to facilitate exploration of data centre
                locations and statistics globally. Note that some data is not
                openly available as these facilities are privately owned.
                
                This is a dashboard to facilitate exploration of data centre
                locations and statistics globally. Note that some data is not
                openly available as these facilities are privately owned.
                '''
            ),
        ]),
        html.Div(className='col-7', children=[
            html.H2('Geographical Distribution of Data Centres'),
            html.Div(className='map-widget-container', children=[
                html.Label(className='map-label', children='Filter by Power'),
                dcc.Checklist(className='checklist-container', id='power-filter', options=[
                    {'label': html.Span(className='label-text', children='With Power'), 'value': 'WITH_POWER'},
                    {'label': html.Span(className='label-text', children='Without Power'), 'value': 'WITHOUT_POWER'},
                ], value=['WITH_POWER']),
                dcc.Graph(className='map-container', id='map-graph'),
            ])
        ]),
    ]),
    html.Div(className='bottom-row', children=[
        html.Div('Bottom'),
    ])
])

app.run_server(debug=True)
