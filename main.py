import requests
import pandas as pd
import plotly.express as px
import datetime
import json
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

df_json = requests.get("http://api.citybik.es/v2/networks").json()
cities = []
for network in df_json["networks"]:
    cities.append(network["location"]["city"])

def get_city_data(city):
    city_bike_networks = requests.get("http://api.citybik.es/v2/networks").json()
    list_of_dicts = []
    for city_bike_dict in city_bike_networks['networks']:
        new_city = city_bike_dict['location']['city']
        if new_city.lower() == city.lower():
            list_of_dicts.append(city_bike_dict)

    return list_of_dicts

def get_stations_info(city):
    station_dict = get_city_data(city)
    if not station_dict:
        print("Error: No bike company found for {}".format(city))
        return None
    for station in station_dict :
        network_address = station['href']
        url = "http://api.citybik.es/{}".format(network_address)
    return requests.get(url).json()['network']['stations']


def get_available_stations(city="Paris"):
    '''
    Takes in the city name and returns a pandas dataframe containing information about the city
    Default city name is Paris
    '''
    station_info = get_stations_info(city)

    station_list = []
    for info in station_info:
        a_dict = {
            'Station Name': info['name'],
            'empty_slots': info['empty_slots'],
            'free_bikes': info['free_bikes'],
            'latitude': info['latitude'],
            'longitude': info['longitude'],
            'timestamp': info['timestamp'],
        }
        if 'ebikes' in info['extra']:
            a_dict['ebikes'] = info['extra']['ebikes']
        else:
            a_dict['ebikes'] = "No_ebikes"
        if "payment" in info['extra']:
            a_dict['payment'] = info['extra']['payment']
        else:
            a_dict['payment'] = "Do_Not_Accept_Credit_Card"
        if "uid" in info['extra']:
            a_dict['Unique ID'] = info['extra']['uid']
        else:
            a_dict['Unique ID'] = ""

        station_list.append(a_dict)

    return pd.DataFrame(station_list)


ACCESS_MAP_TOKEN = "pk.eyJ1IjoiYWpvc2VndW4iLCJhIjoiY2t3NnVlZXVrMDIyZjJ1cW1wY2lraGpscSJ9.iPudHyKbx7WXazNrcPH1rA"

app = Dash(__name__)

app.layout = html.Div([
    html.Center(
        html.H3(
            "dashboard for bike stations visualisation",
            className="uppercase title",
    )),
    dcc.Graph(
        id='graph',
        hoverData={'points': [{'city': 'paris'}]}
    ),
    dcc.Markdown('''
    _enter the city you want to visualize it's bike stations_
    '''),
    dcc.Dropdown(
        cities,
        'Bruxelles',
        clearable=False,
        id='input_city'
            ),
    html.Br(),
    html.A("check source code in my github",
           id="github",
           href="https://github.com/ahmedaazri",
           target="_blank",
           ),


])



@app.callback(
    Output('graph', 'figure'),
    Input('input_city', 'value'))
def show_map(city):
    '''
    Takes in data of the station info in a dataframe format

    Shows a map
    '''

    station_data = get_available_stations(city)

     ## Get the current date and time
    current_date = pd.to_datetime(station_data['timestamp'][0]).strftime('%a %d %B, %Y at %H:%M')

    map_title = 'Map Showing Number of Bikes in {} at {}'.format(city, current_date)

    # Get access token from ploty
    px.set_mapbox_access_token(ACCESS_MAP_TOKEN)

    fig = px.scatter_mapbox(station_data, lat="latitude", lon="longitude", hover_name="Station Name",
                            color="free_bikes",
                            hover_data=["empty_slots", "free_bikes", "ebikes", "payment"],
                            title=map_title,
                            color_continuous_scale=px.colors.sequential.Plasma, size_max=20, zoom=12)
    fig.update_layout(transition_duration=500)
    return fig

if __name__ == '__main__':
    app.run_server(debug = True)






