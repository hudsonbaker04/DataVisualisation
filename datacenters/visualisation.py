import pandas as pd

data = pd.read_csv('geo_data_centers_cleaned.csv', sep=',')

data.drop(columns=['Unnamed: 0.1'], inplace=True)
data.drop(columns=['Unnamed: 0'], inplace=True)

# print(data.columns)
# print(data.info())

location_data = data[data['latitude'].notna() & data['longitude'].notna()]

def clean_total_power(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace('MW', '').strip()
    try:
        value = float(value)
        if value > 1000000:
            value /= 1000000
        elif value > 100:
            value /= 1000
        return value
    except ValueError:
        return 0.0


# Apply the function to the total power column
location_data['total power (MW)'] = location_data['total power (MW)'].apply(clean_total_power)

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Create a Dash application
app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css', 'styles.css'])

# Define the layout with a dropdown for filtering
app.layout = html.Div(
    className='container',
    children=[
        html.Div(
            className='row',
            style={'border': '1px solid black', 'padding': '10px'},
            children=[
                html.Div(
                    className='col-5',
                    style={'border': '1px solid black', 'padding': '10px'},
                    children=[
                        html.H1(
                            children='Visualising Global Data Centres',
                            style={'font-family': 'sans-serif'},
                        ),
                        html.Div(
                            children='Introductory paragraph.',
                        ),
                    ]
                ),
                html.Div(
                    className='col-7',
                    style={'border': '1px solid black', 'padding': '10px'},
                    children=[
                        html.H2(
                            'Geographical Distribution of Data Centres'
                        ),
                        html.Label(
                            children='Filter by Power',
                            className='checklist-label',
                        ),
                        dcc.Checklist(
                            id='power-filter',
                            className='checklist-container',
                            options=[
                                {'label': 'With Power Values', 'value': 'WITH_POWER'},
                                {'label': 'Without Power Values', 'value': 'WITHOUT_POWER'}
                            ],
                            value=['WITH_POWER'],
                            inline=True,
                        ),
                        dcc.Graph(
                            id='map-graph',
                            style={'width': '100%', 'height': '400px', 'margin': '0', 'padding': '0px', 'border': '1px solid black'},
                        ),
                    ]
                ),
            ]
        ),
        html.Div(
            className='row',
            style={'display': 'flex', 'justifyContent': 'center', 'border': '1px solid black', 'padding': '10px'},
            children=[
                html.Label('Compare by:'),
                dcc.Dropdown(
                    id='compare-filter',
                    options=[
                        {'label': 'Country', 'value': 'COUNTRY'},
                        {'label': 'Company', 'value': 'COMPANY'},
                        {'label': 'Continent', 'value': 'CONTINENT'},
                    ],
                    value='COUNTRY',
                ),
                html.Div(
                    className='col-3',
                    style={'border': '1px solid black', 'padding': '10px'},
                    children=[
                        html.H3('Data Centre Quantity'),
                        dcc.Graph(
                            id='quantity-graph',
                        ),
                    ]
                ),
                html.Div(
                    className='col-3',
                    style={'border': '1px solid black', 'padding': '10px'},
                    children=[
                        html.H3('plot 2'),
                    ]
                ),
                html.Div(
                    className='col-3',
                    style={'border': '1px solid black', 'padding': '10px'},
                    children=[
                        html.H3('plot 3'),
                    ]
                ),
            ]
        )
    ]
)

def world_plot(lon, lat, text, marker) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=lon, lat=lat, text=text, marker=marker))
    fig.update_layout(
        geo=dict(
            showland=True,
            landcolor='black',  # Land colour
            showocean=True,
            oceancolor='grey',  # Ocean colour
            showlakes=True,
            lakecolor='grey',
            bgcolor="#fff",  # Background colour
            projection=dict(
                type='orthographic',
                rotation=dict(lon=-100, lat=40)
            ),
            scope='world',
            showcountries=True,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig

# Define the callback to update the graph based on dropdown selection
@app.callback(
    Output('map-graph', 'figure'),
    [Input('power-filter', 'value')]
)
def update_map(filter_value) -> go.Figure:
    # Filter data based on dropdown selection
    if filter_value == ['WITH_POWER']:
        filtered_data = location_data[location_data['total power (MW)'] > 0]
    elif filter_value == ['WITHOUT_POWER']:
        filtered_data = location_data[location_data['total power (MW)'] == 0]
    elif len(filter_value) == 2:  # both selected
        filtered_data = location_data
    else:
        return world_plot(lon=[0], lat=[0], text=[''], marker={'size': [0.5]})

    # Define marker sizes and colors
    marker_sizes = filtered_data['total power (MW)'].fillna(0).apply(lambda x: 7 if x == 0 else x / 3)
    marker_colors = ['blue' if x == 0 else 'red' for x in filtered_data['total power (MW)']]  # Colors based on power values

    return world_plot(
        lon=filtered_data['longitude'],
        lat=filtered_data['latitude'],
        text=filtered_data.apply(lambda row: f"Power: {row['total power (MW)']} MW<br>Colocation Space: {row['colocation space (sqft)']} sqft<br>Total Space: {row['total space (sqft)']} sqft", axis=1),
        marker=dict(
            size=marker_sizes,  # size based on power
            color=marker_colors,  # colour based on owning power attribute
            line=dict(width=0)
        )
    )

# Define the callback to update the graph based on dropdown selection
@app.callback(
    Output('quantity-graph', 'figure'),
    [Input('compare-filter', 'value')]
)
def update_quantity(filter_value) -> go.Figure:
    # Filter data based on dropdown selection
    if filter_value == 'COUNTRY':
        filtered_data = location_data.groupby('country')
    elif filter_value == 'COMPANY':
        filtered_data = location_data.groupby('name')
    else:
        pass

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[a[0] for a in filtered_data], y=[len(a[1]) for a in filtered_data], mode='markers', marker=dict(color='red')))
    shapes = []
    for i, (_, group) in enumerate(filtered_data):
        shapes.append(dict(type='line', xref='x', yref='y', x0=i, y0=0.9, x1=i, y1=len(group), line=dict(color='grey', width=1)))

    fig.update_layout(shapes=shapes, xaxis=dict(type='category'), yaxis=dict(type='log'), margin=dict(l=0, r=0, t=0, b=0),)

    return fig

app.run_server(debug=True)
