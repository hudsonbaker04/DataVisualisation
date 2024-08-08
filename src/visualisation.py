import pandas as pd
from pandas.core.groupby.generic import DataFrameGroupBy

data: pd.DataFrame = pd.read_csv('data/geo_data_centers_cleaned.csv', sep=',')  # read in csv data

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
import plotly.express as px
import pandas as pd

BACKGROUND = '#121212'

app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css', 'styles.css'])  # create dash application and reference bootstrap layout style sheet

app.layout = html.Div(className='main-container', children=[
    html.Div(className='top-row', children=[
        html.Div(className='col-5', children=[
            html.H1('Visualising Global Data Centres'),
            html.P(
                '''
                Data centres play a vital but largely unseen role in everyday
                internet activity. This dashboard explores where these centres
                are located, who owns them, and how large they are.
                '''
            ),
            html.P(
                '''
                *Note, some data (particularly related to China) is not openly
                available. Keep this in consideration during comparisons.
                '''
            ),
            html.P('''Use the drop down to filter all graphs and compare by country or by owning company.
                   Use the range slider to filter based on the number of data centres owned.'''),
            html.Div(className='compare-widget-container', children=[
                html.Div(className='compare-by', children=[
                    html.Label(className='compare-widget-label', children='Compare by:'),
                    dcc.Dropdown(className='compare-widget', id='compare-filter', options=[
                        {'label': html.Span(className='drop-text', children='Country'), 'value': 'COUNTRY'},
                        {'label': html.Span(className='drop-text', children='Company'), 'value': 'COMPANY'},
                    ], value='COUNTRY', searchable=False, clearable=False),
                ]),
                html.Div(className='adjust-minimum', children=[
                    html.Label(className='slider-label', children='# Centres:'),
                    dcc.RangeSlider(min=0.99, max=(max_ := 8), step=None, marks={i: str(2 ** i) for i in range(max_ + 1)}, value=[4, 8], id='minimum-slider', className='slider-widget'),
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
                        {'label': html.Span(className='check-text', children='Power Known'), 'value': 'WITH_POWER'},
                        {'label': html.Span(className='check-text', children='Power Unknown'), 'value': 'WITHOUT_POWER'},
                    ], value=['WITH_POWER']),
                    html.P(className='map-description', children=
                           '''
                           Explore data centre locations on this interactive globe with sizes
                           proportionate to power consumption (where known).
                           '''
                    ),
                ]),
            ])
        ]),
    ]),
    html.Div(className='bottom-row', children=[
        html.Div(className='compare-container', children=[
            html.Div(className='plot1', children=[
                html.H3('Data Centre Quantity'),
                dcc.Graph(className='quantity-container', id='quantity-graph'),
                html.P(className='plot-description', children=
                       '''
                       Compare the number of data centres located in a specific country or
                       owned by a certain company.
                       '''
                ),
            ]),
            html.Div(className='plot2', children=[
                html.H3('Data Centre Size'),
                dcc.Graph(className='size-container', id='size-graph'),
                html.P(className='plot-description', children=
                       '''
                       Compare the average and spread of data centre sizes located in a specific
                       country or owned by a certain company.
                       '''
                ),
            ]),
            html.Div(className='plot3', children=[
                html.H3('Data Centre Power'),
                dcc.Graph(className='power-container', id='power-graph'),
                html.P(className='plot-description', children=
                       '''
                       Compare the proportion of total power that data centres located in a
                       specific country or owned by a certain company account for.
                       '''
                ),
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
    [Input('power-filter', 'value'), Input('compare-filter', 'value'), Input('minimum-slider', 'value')],
)
def update_map(power, owner, num) -> go.Figure:
    '''Redraw the map depending on which data is selected for plotting by the user.'''
    if max(num) == 8:
        num[num.index(max(num))] = 2048
    if owner == 'COUNTRY':
        key = 'country'
    else:
        key = 'name'
    counts = location_data[key].value_counts()
    filtered = counts[(counts > 2 ** min(num)) & (counts < 2 ** max(num))].index
    filtered_data = location_data[location_data[key].isin(filtered)]

    if power == ['WITH_POWER']:
        filtered_data: pd.DataFrame = filtered_data[filtered_data['total power (MW)'] > 0]
    elif power == ['WITHOUT_POWER']:
        filtered_data = filtered_data[filtered_data['total power (MW)'] == 0]
    elif len(power) == 2:  # both selected
        filtered_data = filtered_data
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

def create_lollipop(data, filter, min_, max_) -> go.Figure:
    if max_ == 256:
        max_ = 2048  # set the max to go above the range slider and show top values
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x=[a[0] for a in data if len(a[1]) > min_ and len(a[1]) < max_],  # strings
            y=[len(a[1]) for a in data if len(a[1]) > min_ and len(a[1]) < max_],  # data values
            mode='markers', marker=dict(color='red'), fillcolor=BACKGROUND
    ))
    shapes: list = []
    i = 0
    for _, group in data:
        if len(group) > min_ and len(group) < max_:
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
        title_font=dict(size=20),
        tickfont=dict(size=15),
    )

    fig.update_yaxes(
        gridcolor=BACKGROUND,
        ticks='outside',
        title_font=dict(size=20),
        tickfont=dict(size=15),
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
        return create_lollipop(data=filtered_data, filter='Country', min_=2 ** min(num), max_=2 ** max(num))
    else:
        filtered_data = location_data.groupby('name')
        return create_lollipop(data=filtered_data, filter='Company', min_=2 ** min(num), max_=2 ** max(num))

def create_box(data, filter, min_, max_) -> go.Figure:
    '''Create the go.Box plot.'''
    if max_ == 256:
        max_ = 2048
    traces: list = []
    colours = px.colors.qualitative.Plotly
    for i, (key, group) in enumerate(data):
        if len(y := group['total space (sqft)']) > min_ and len(y := group['total space (sqft)']) < max_:
            traces.append(go.Box(
                name=key, y=y,
                marker=dict(color=colours[i % len(colours)])
            ))

    layout = go.Layout(
        xaxis=dict(title=filter, title_font=dict(size=20), tickfont=dict(size=15)),
        yaxis=dict(title='Size (sqft)', title_font=dict(size=20), tickfont=dict(size=15), type='log'),
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
        return create_box(data=filtered_data, filter='Country', min_=2 ** min(num), max_=2 ** max(num))
    else:
        filtered_data = location_data.groupby('name')
        return create_box(data=filtered_data, filter='Company', min_=2 ** min(num), max_=2 ** max(num))

def create_pie(data, val_col, lab_col) -> go.Figure:
    total: float = data[val_col].sum()
    data['percentage'] = data[val_col] / total
    large: pd.DataFrame = data[data['percentage'] >= 0.02]
    small: pd.DataFrame = data[data['percentage'] < 0.02]
    other: float = small[val_col].sum()
    if other > 0:
        large = pd.concat([large, pd.DataFrame({lab_col: ['Other'], val_col: [other], 'percentage': [other / total]})])

    pie_data = go.Pie(
        labels=large[lab_col],
        values=large[val_col],
        textinfo='label+percent',
        insidetextorientation='radial',
        hoverinfo='label+percent+value',
        marker=dict(
            colors=px.colors.qualitative.Plotly,  # Use Plotly's qualitative color palette
            line=dict(color='#121212', width=2)  # White borders with width 2
        ),
    )

    layout = go.Layout(
        template='plotly_dark',
        legend=dict(
            title=dict(text=lab_col.capitalize(), font=dict(size=16)),
            x=1, y=1,
        )
    )

    return go.Figure(data=[pie_data], layout=layout)

@app.callback(
    Output('power-graph', 'figure'),
    [Input('compare-filter', 'value'), Input('minimum-slider', 'value')]
)
def update_power(filter, num) -> go.Figure:
    '''Redraw the pie chart depending on which comparsion category is selected.'''
    if max(num) == 8:
        num[num.index(max(num))] = 11
    if filter == 'COUNTRY':
        key = 'country'
    else:
        key = 'name'
    datacenter_counts = location_data[key].value_counts()
    filtered = datacenter_counts[(datacenter_counts > 2 ** min(num)) & (datacenter_counts < 2 ** max(num))].index
    filtered_data = location_data[location_data[key].isin(filtered)]
    grouped_data = filtered_data.groupby(key)['total power (MW)'].sum().reset_index()
    return create_pie(grouped_data, 'total power (MW)', key)

app.run_server(debug=True)
