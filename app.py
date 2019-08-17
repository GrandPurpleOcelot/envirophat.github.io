import dash
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.express as px
import plotly.graph_objs as go
import mysql.connector
import pandas as pd
import numpy as np

# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = [
    ['hello','world'],
    ['pi','raspberry']
]

data_dict = {
    "Ambient Temperature (\N{DEGREE SIGN} Celcius)": "temp",
    "CPU Temperature (\N{DEGREE SIGN} Celcius)": "cputemp",
    "Light (Lux)": "light",
    "Atmospheric Pressure (hPa)": "pressure"
}

def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-logo",
                children=[
                    html.Img(id="logo", src=app.get_asset_url("raspberrypi_logo.png")),
                ], style={'textAlign': 'center'}
            ),

            html.Div([
            html.H2('Enviro PHAT Sensors Data', style = {
                'textAlign': 'center'
            })
            ]),

            html.Div([
                html.H5("Owner: Thien Nghiem",style = {'textAlign': 'center'}),
                html.H6("Date Created: 2019-08-12",style = {'textAlign': 'center'})
            ])
            
        ],
    )

def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                colors = { 'border': '#d6d6d6', "primary": '#1975FA', "background": '#222222'},
                id="app-tabs",
                value="tab-1",
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="sensor-tab",
                        label="LIVE SENSORS DASHBOARD",
                        value="tab-1",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="algorithm-tab",
                        label="ANOMALY DETECTION",
                        value="tab-2",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="analytics-tab",
                        label="DATA ANALYTICS",
                        value="tab-3",
                        className="custom-tab",
                        selected_className="custom-tab--selected", children= html.Div(analytics_graphs)
                    )
                ],
            )
        ],
    )

def thresholding_algo(dataframe, variable, lag, threshold):
    dataframe.sort_values('timestamp', inplace = True)
    dataframe['moving_average'] = dataframe[variable].rolling(window = lag).mean()
    dataframe['std'] = dataframe[variable].rolling(window = lag).std()
    dataframe['lower_bound'] = dataframe['moving_average'] - threshold * dataframe['std']
    dataframe['upper_bound'] = dataframe['moving_average'] + threshold * dataframe['std']
    dataframe['anomaly'] = np.where((dataframe[variable] > dataframe['upper_bound']) | (dataframe[variable] < dataframe['lower_bound']), 'anomaly', 'None')
    dataframe['date'] = pd.to_datetime(dataframe['timestamp'], unit = 'ns')
    dataframe.set_index('date', inplace = True)

    return dataframe

# retrieve historical data ~ 7 days
# establish connection to MySQL on the Pi Zero that hosts the enviro sensors
connection = mysql.connector.connect(host = 'YourIPAddr',
                                    database = 'enviro',
                                    user='root',
                                    password='ROOT')
        
df = pd.read_sql_query('''SELECT timestamp, light, rgb FROM enviro_log
WHERE timestamp BETWEEN CURDATE() - INTERVAL 4 DAY AND CURDATE() - INTERVAL 1 SECOND;''', connection)

df.sort_values('timestamp', inplace = True)

# split RGB columns in to 3 separate components
rgb_cols = ['red', 'green', 'blue']
df[rgb_cols] = df['rgb'].str.split(',', expand=True)
df[rgb_cols] = df[rgb_cols].apply(pd.to_numeric, errors='coerce', axis=1)

# generate light classification
df.loc[df['light'] == 0, 'lighting_condition'] = 'no_light'
df.loc[(df['light'] > 0) & (df['light'] <= 100), 'lighting_condition'] = 'low_natural_light'
df.loc[(df['light'] > 100) & (df['light'] <= 130), 'lighting_condition'] = 'led_light'
df.loc[df['light'] > 130, 'lighting_condition'] = 'high_natural_light'

# filter LED using RGB values
df['red_to_blue'] = df['red']/df['blue']
df['red_to_blue'].fillna(0, inplace = True)
df.loc[(df['red_to_blue'] > 1.7) & (df['light'] > 130), 'lighting_condition'] = 'led_light'
df.loc[(df['red_to_blue'] < 1.7) & (df['light'] < 130) & (df['light'] > 100), 'lighting_condition'] = 'low_natural_light'

# summary df to get count for each lighting_condition group
grouped_df = df.set_index('timestamp').groupby([pd.Grouper(freq='D'), 'lighting_condition']).count()
grouped_df['duration'] = grouped_df['light'] * 6.7 /3600
summarized_df = pd.melt(grouped_df.unstack()['duration'].reset_index(),id_vars = 'timestamp', value_vars=['high_natural_light', 'led_light', 'low_natural_light', 'no_light'],value_name='Hours')

summarized_df['Day of Week'] = summarized_df['timestamp'].dt.day_name()

analytics_graphs = []

analytics_graphs.append(
    html.Div(
        dcc.Graph(
                    id='led-usage_trend',
                    figure= (px.line(summarized_df, x = 'Day of Week', y = 'Hours', color = "lighting_condition", line_shape="spline",title = 'Lighting Condition Trend') .update_traces(mode='lines+markers'))
                )))

analytics_graphs.append(
    html.Div(
        dcc.Graph(
                    id='led-usage_bar',
                    figure= px.bar(summarized_df, x = 'Day of Week', y = 'Hours', color = "lighting_condition", title = 'Lighting Condition Daily')
                )))
                

cards = dbc.CardDeck(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Ambient Temperature", className="card-title"),
                    html.H2(
                        id = 'ambient_temperature',
                        className="card-text",
                    )
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("CPU Temperature", className="card-title"),
                    html.H2(
                        id = 'cpu_temperature',
                        className="card-text",
                    )
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Light", className="card-title"),
                    html.H2(
                        id = 'light_value',
                        className="card-text",
                    )
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("RGB", className="card-title"),
                    html.H4(
                        id = 'rgb_value',
                        className="card-text",
                    )
                ]
            )
        ),
    ]
)

app = dash.Dash(__name__,  external_stylesheets=[dbc.themes.DARKLY] )

# basic HTTP authentication
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

server = app.server

app.layout = html.Div(children =
[
        build_banner(),

        cards,

        build_tabs(),

        html.Div(children = html.Div(id='graphs')),

        dcc.Interval(
            id='graph-update',
            interval=3000,
            n_intervals = 0
        ),
    ]
)

@app.callback(
    Output('graphs', 'children'),
    [Input('graph-update', 'n_intervals'),
    Input('app-tabs', 'value')]
        )


def update_graph_scatter(n, tab):
    if tab == 'tab-1':
        # establish connection to MySQL on the Pi Zero that hosts the enviro sensors
        connection = mysql.connector.connect(host = 'YourIPAddr',
                                            database = 'enviro',
                                            user='root',
                                            password='ROOT')
        
        df = pd.read_sql_query('''SELECT * FROM enviro_log 
        ORDER BY timestamp DESC LIMIT 150;''', connection)

        # correction for temperature:
        df['temp'] -= 6
        df['pressure'] = df['pressure'] / 100

        df.sort_values('timestamp', inplace = True)
        df['date'] = pd.to_datetime(df['timestamp'], unit = 'ns')
        df.set_index('date', inplace = True)

        # split RGB columns in to 3 separate components
        rgb_cols = ['red', 'green', 'blue']
        df[rgb_cols] = df['rgb'].str.split(',', expand=True)
        df[rgb_cols] = df[rgb_cols].apply(pd.to_numeric, errors='coerce', axis=1)

        graphs = []
        X = df.index
        for name, variable in data_dict.items():

            Y = df[variable].values

            data = go.Scatter(
                    x=list(X),
                    y=list(Y),
                    fill = 'tozeroy',
                    fillcolor = '#6897bb',
                    name='Scatter',
                    mode= 'lines+markers'
                    )

            graphs.append(html.Div(dcc.Graph(
                id=variable,
                animate = False,
                figure =  {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                        yaxis=dict(range=[min(Y),max(Y)]),
                                                        title = '{}'.format(name))})))

        graphs.append(html.Div(dcc.Graph(
            id='rgb',
            figure=go.Figure(
                data=[
                    go.Scatter(
                        x= X,
                        y= df['red'],
                        name='Red',
                        line = dict(color = "red")
                    ),
                    go.Scatter(
                        x= X,
                        y= df['green'],
                        name='Green',
                        line = dict(color = "green")
                    ),

                    go.Scatter(
                        x= X,
                        y= df['blue'],
                        name='Blue',
                        line = dict(color = "blue")
                    )
                ],
                layout=go.Layout(
                    title='RGB Values',
                    showlegend=True,
                    legend=go.layout.Legend(
                        x=0,
                        y=1.0
                    ),
                    xaxis=dict(range=[min(X),max(X)]),
                    yaxis=dict(range=[df['blue'].min()-10, df['red'].max()+10])
                )
            ),
            style={'height': 500}
        )))
        return graphs

    elif tab == 'tab-2':
        connection = mysql.connector.connect(host = 'YourIPAddr',
                                            database = 'enviro',
                                            user='root',
                                            password='ROOT')
        
        df = pd.read_sql_query('''SELECT * FROM enviro_log 
        ORDER BY timestamp DESC LIMIT 300;''', connection)

        threshold = 3.5
        lag = 50
        variable = 'cputemp'

        anomalies = thresholding_algo(df, threshold = threshold, lag = lag, variable = variable)

        graphs = []
        X = anomalies.index

        graphs.append(html.Div(dcc.Graph(
            id='rgb',
            figure=go.Figure(
                data=[
                    go.Scatter(
                        x= X,
                        y= anomalies['cputemp'],
                        name='CPU Temperature',
                        line = dict(color = "blue")
                    ),
                    go.Scatter(
                        x= X,
                        y= anomalies['moving_average'],
                        name='Moving Average',
                        line = dict(color = "red")
                    ),

                    go.Scatter(
                        x= X,
                        y= anomalies['upper_bound'],
                        name='Upper bound',
                        line = dict(color = "yellow")
                    ),

                    go.Scatter(
                        x= X,
                        y= anomalies['lower_bound'],
                        name='Lower bound',
                        line = dict(color = "yellow")
                    ),

                    go.Scatter(
                        x= anomalies.index[anomalies['anomaly'] == 'anomaly'],
                        y= anomalies[anomalies['anomaly'] == 'anomaly']['cputemp'],
                        name='Anomalies',
                        mode = 'markers',
                        marker = dict(color = "purple", size = 12, symbol = "x")
                    )
                ],
                layout=go.Layout(
                    title='Detect Temperature Anomalies',
                    showlegend=True,
                    legend=go.layout.Legend(
                        x=0,
                        y=1.0
                    ),
                    xaxis=dict(range=[min(X),max(X)]),
                    yaxis=dict(range=[anomalies['lower_bound'].min()-2, anomalies['upper_bound'].max()+2])
                )
            ),
            style={'height': 500}
        )))
        return graphs

@app.callback(
    [Output('ambient_temperature', 'children'),
    Output('cpu_temperature', 'children'), 
    Output('light_value', 'children'), 
    Output('rgb_value', 'children')],
    [Input('graph-update', 'n_intervals')]
        )

def get_current_readings(n):
    connection = mysql.connector.connect(host = 'YourIPAddr',
                                            database = 'enviro',
                                            user='root',
                                            password='ROOT')
        
    df = pd.read_sql_query('''SELECT * FROM enviro_log 
    ORDER BY timestamp DESC LIMIT 1;''', connection)

    ambient_temperature = str(round(df['temp'].values[-1] - 6, 2)) + " \N{DEGREE SIGN} C"
    cpu_temperature = str(round(df['cputemp'].values[-1], 2)) + " \N{DEGREE SIGN} C"
    light_value = str(round(df['light'].values[-1], 2)) + " Lux"
    rgb_value = df['rgb'].values[-1]

    return ambient_temperature, cpu_temperature, light_value, rgb_value





if __name__ == '__main__':
    app.run_server(debug=True, host = '0.0.0.0')