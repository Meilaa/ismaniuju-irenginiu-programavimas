# pirmiausia paleist subscriberi
import json
import requests
import paho.mqtt.client as mqtt

# Nustatykite MQTT brokerio URL ir temą
mqttBroker = "broker.mqttdashboard.com"
topic = "Kursinis/z"

# Sukurkite MQTT klientą
mqtt_client = mqtt.Client()

# Funkcija siųsti duomenis į MQTT brokerį
def send_to_mqtt():
    with open('artists.json', 'r') as file:
        data = json.load(file)
        mqtt_client.publish(topic, json.dumps(data))

# Autorizacijos tokenas
token = 'BQDozoES0QxAphH6Ac1_xM_Fv_t8HtCqCxYdf_PGp0J5QZE29RjEC1NRP50-Vn-qGXzt5cGDrNcjoBs5Yuhu31LM_9RcTKxJGpYUZpefWlXI1a8At4TUYiDOJjoHgQ0i_J7PuVU6oApaJwRArHg-2W1F_zbd_dv-1d6jPY0YEVSYD45knTPAXzQqwVn3UF3TqbN6m5ACkZvadKyqWJtHuncrWKpq7WDn2QRvREt6rAM1hsNVmGVl8pDxIC33emuz0JmjDlbkbJOqIBDC_qxOt3mk'

def fetch_web_api(endpoint, method, body=None):
    url = f'https://api.spotify.com/{endpoint}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=body)
    return response.json()

def get_top_artists():
    response = fetch_web_api(
        'v1/me/top/artists?time_range=long_term&limit=5', 'GET'
    )
    if response and 'items' in response:
        artists_info = []
        for item in response['items']:
            artist_info = {
                'name': item['name'],
                'type': item['type'],
                'genres': item.get('genres', []),
                'popularity': item.get('popularity', 0),
                'uri': item['uri']
            }
            # Pridėkime gauti dainos pavadinimą
            top_track_response = fetch_web_api(
                f'v1/artists/{item["id"]}/top-tracks?country=US', 'GET'
            )
            if top_track_response and 'tracks' in top_track_response:
                top_track_name = top_track_response['tracks'][0]['name']
                artist_info['song_name'] = top_track_name
            else:
                artist_info['song_name'] = 'Unknown'
            
            artists_info.append(artist_info)
        
        # Įrašykite duomenis į JSON failą
        with open('artists.json', 'w') as file:
            json.dump(artists_info, file)
        
        return artists_info
    else:
        return []

if __name__ == "__main__":
    # Prijunkite prie MQTT brokerio
    mqtt_client.connect(mqttBroker, 1883)
    
    # Gauti duomenis iš Spotify API ir siųsti juos į MQTT brokerį
    top_artists = get_top_artists()
    send_to_mqtt()
