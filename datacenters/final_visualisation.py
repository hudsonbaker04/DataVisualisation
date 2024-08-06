import pandas as pd
import numpy as np
from pandas.core.groupby.generic import DataFrameGroupBy

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

BACKGROUND = '#121212'

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
                '''
            ),
            html.Div(className='compare-widget-container', children=[
                html.Div(className='compare-by', children=[
                    html.Label(className='compare-widget-label', children='Compare by:'),
                    dcc.Dropdown(className='compare-widget', id='compare-filter', options=[
                        {'label': html.Span(className='drop-text', children='Country'), 'value': 'COUNTRY'},
                        {'label': html.Span(className='drop-text', children='Company'), 'value': 'COMPANY'},
                    ], value='COUNTRY', searchable=False, clearable=False),
                ]),
                html.Div(className='adjust-minimum', children=[
                    html.Label(className='slider-label', children='Minimum #:'),
                    dcc.Slider(0.99, (max_ := 8), step=None, marks={i: str(2 ** i) for i in range(max_ + 1)}, value=4, id='minimum-slider', className='slider-widget'),
                ]),
            ]),
        ]),
        html.Div(className='col-7', children=[
            html.H2('Geographical Distribution of Data Centres'),
            html.Div(className='map-widget-container', children=[
                dcc.Graph(className='map-container', id='map-graph'),
                html.Div(className='map-widget', children=[
                    html.Label(className='map-label', children='Filter by Power'),
                    dcc.Checklist(className='checklist-container', id='power-filter', options=[
                        {'label': html.Span(className='check-text', children='With Power'), 'value': 'WITH_POWER'},
                        {'label': html.Span(className='check-text', children='Without Power'), 'value': 'WITHOUT_POWER'},
                    ], value=['WITH_POWER']),
                ]),
            ])
        ]),
    ]),
    html.Div(className='bottom-row', children=[
        html.Div(className='compare-container', children=[
            html.Div(className='plot1', children=[
                html.H3('Data Centre Quantity'),
                dcc.Graph(className='quantity-container', id='quantity-graph'),
            ]),
            html.Div(className='plot2', children=[
                html.H3('Data Centre Size'),
                dcc.Graph(className='size-container', id='size-graph'),
            ]),
            html.Div(className='plot3', children=[
                html.H3('Data Centre Power'),
                dcc.Graph(className='power-container', id='power-graph'),
            ]),
        ]),
    ])
])

def world_plot(lon, lat, text, marker) -> go.Figure:
    '''Create the map figure.'''
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(lon=lon, lat=lat, text=text, marker=marker))
    fig.update_layout(
        geo=dict(
            showland=True, landcolor=BACKGROUND,
            showocean=True, oceancolor='grey',
            showlakes=True, lakecolor='grey',
            bgcolor=BACKGROUND, # set background colour
            projection=dict(
                type='orthographic',
                rotation=dict(lon=-100, lat=40)  # default lon and lat
            ),
            scope='world', showcountries=True,
        ),
        margin=dict(l=0, r=0, t=0, b=0),  # remove outer whitespace
        paper_bgcolor=BACKGROUND,
    )
    return fig

@app.callback(  # callback to update map based on checklist selection
    Output('map-graph', 'figure'),
    [Input('power-filter', 'value')],
)
def update_map(filter) -> go.Figure:
    '''Redraw the map depending on which data is selected for plotting by the user.'''
    if filter == ['WITH_POWER']:
        filtered_data: pd.DataFrame = location_data[location_data['total power (MW)'] > 0]
    elif filter == ['WITHOUT_POWER']:
        filtered_data = location_data[location_data['total power (MW)'] == 0]
    elif len(filter) == 2:  # both selected
        filtered_data = location_data
    else:  # none selected
        return world_plot(lon=[0], lat=[0], text=[''], marker={'size': [0.5]})

    # Constant size for centres without power data, proportional for those with power data.
    sizes: pd.Series = filtered_data['total power (MW)'].apply(lambda x: 7 if x == 0 else x / 3)
    # Blue for centres without power data, red for those with power data.
    colours: list = ['blue' if x == 0 else 'red' for x in filtered_data['total power (MW)']]

    return world_plot(
        lon=filtered_data['longitude'],
        lat=filtered_data['latitude'],
        text=filtered_data.apply(
            lambda row: f"Power: {row['total power (MW)']} MW<br>Colocation Space: {row['colocation space (sqft)']} sqft<br>Total Space: {row['total space (sqft)']} sqft",
            axis=1,
        ),
        marker=dict(
            size=sizes,
            color=colours,
            line=dict(width=0)
        )
    )

def create_lollipop(data, filter, min_=1) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x=[a[0] for a in data if len(a[1]) > min_],  # strings
            y=[len(a[1]) for a in data if len(a[1]) > min_],  # data values
            mode='markers', marker=dict(color='red'), fillcolor=BACKGROUND
    ))
    shapes: list = []
    i = 0
    for _, group in data:
        if len(group) > min_:
            shapes.append(  # create the lines for the lollipop diagram
                dict(type='line', xref='x', yref='y', x0=i, y0=0.9, x1=i, y1=len(group), line=dict(color='#fff', width=1))
            )
            i += 1

    fig.update_layout(
        shapes=shapes,
        xaxis=dict(type='category', color='#fff', title=filter), yaxis=dict(type='log', color='#fff', title='Number'),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
    )

    fig.update_xaxes(
        gridcolor=BACKGROUND,
        showline=True,
        ticks='outside',
    )

    fig.update_yaxes(
        gridcolor=BACKGROUND,
        ticks='outside',
    )

    return fig

@app.callback(
    Output('quantity-graph', 'figure'),
    [Input('compare-filter', 'value'), Input('minimum-slider', 'value')],
)
def update_quantity(filter, num) -> go.Figure:
    '''Redraw the quantity lollipop chart depending on which comparison category is selected.'''
    if filter == 'COUNTRY':
        filtered_data: DataFrameGroupBy = location_data.groupby('country')
        return create_lollipop(data=filtered_data, filter='Country', min_=2 ** num)
    else:
        filtered_data = location_data.groupby('name')
        return create_lollipop(data=filtered_data, filter='Company', min_=2 ** num)

def create_box(data, filter, min_) -> go.Figure:
    '''Create the go.Box plot.'''
    traces: list = []
    for key, group in data:
        if len(y := group['total space (sqft)']) > min_:
            traces.append(go.Box(name=key, y=y))

    layout = go.Layout(
        xaxis_title=filter,
        yaxis=dict(title='Size (sqft)', type='log'),
        template='plotly_dark',
        margin=dict(l=0, r=0, t=0, b=0),
    )

    fig = go.Figure(data=traces, layout=layout)

    return fig

@app.callback(
    Output('size-graph', 'figure'),
    [Input('compare-filter', 'value'), Input('minimum-slider', 'value')],
)
def update_size(filter, num) -> go.Figure:
    '''Redraw the box plots depending on which comparison category is selected.'''
    if filter == 'COUNTRY':
        filtered_data: DataFrameGroupBy = location_data.groupby('country')
        return create_box(data=filtered_data, filter='Country', min_=2 ** num)
    else:
        filtered_data = location_data.groupby('name')
        return create_box(data=filtered_data, filter='Company', min_=2 ** num)

def create_pie(data, val_col, lab_col) -> go.Figure:
    total: float = data[val_col].sum()
    data['percentage'] = data[val_col] / total
    large: pd.Series = data[data['percentage'] >= 0.02]
    small: pd.Series = data[data['percentage'] < 0.02]
    other: float = small[val_col].sum()
    if other > 0:
        large = large._append(pd.DataFrame({lab_col: ['other'], val_col: other, 'percentage': [other / total]}))
    data = go.Pie(
        labels=large[lab_col],
        values=large[val_col],
        textinfo='label+percent',
        insidetextorientation='radial',
    )
    layout = go.Layout(
        template='plotly_dark',
    )
    return go.Figure(data=[data], layout=layout)

@app.callback(
    Output('power-graph', 'figure'),
    [Input('compare-filter', 'value'), Input('minimum-slider', 'value')]
)
def update_power(filter, num) -> go.Figure:
    '''Redraw the pie chart depending on which comparsion category is selected.'''
    if filter == 'COUNTRY':
        datacenter_counts = location_data['country'].value_counts()
        filtered_countries = datacenter_counts[datacenter_counts > 2 ** num].index
        filtered_data = location_data[location_data['country'].isin(filtered_countries)]
        grouped_data = filtered_data.groupby('country')['total power (MW)'].sum().reset_index()
        return create_pie(grouped_data, 'total power (MW)', 'country')
    else:
        datacenter_counts = location_data['name'].value_counts()
        filtered_companies = datacenter_counts[datacenter_counts > 2 ** num].index
        filtered_data = location_data[location_data['name'].isin(filtered_companies)]
        grouped_data = filtered_data.groupby('name')['total power (MW)'].sum().reset_index()
        return create_pie(grouped_data, 'total power (MW)', 'name')

app.run_server(debug=True)
