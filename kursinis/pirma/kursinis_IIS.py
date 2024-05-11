from flask import Flask, render_template, jsonify, request, send_file
import requests
import json
import paho.mqtt.client as mqtt
from PIL import Image
import io
from threading import Thread

app = Flask(__name__)

# Nustatomas MQTT brokerio URL ir temą
mqttBroker = "broker.hivemq.com"
topic = "Kursinis/z"

# Globalus kintamasis, kuriame saugomi gauti MQTT pranešimai
mqtt_messages = []

# Sukurtas MQTT klientą
mqtt_client = mqtt.Client()

# Funkcija siųsti duomenis į MQTT brokerį
def send_to_mqtt():
    with open('artists.json', 'r') as file:
        data = json.load(file)
        mqtt_client.publish(topic, json.dumps(data))

# Funkcija, kuri bus iškviečiama, kai gaunamas MQTT pranešimas
def on_message(client, userdata, message):
    payload = json.loads(message.payload)
    mqtt_messages.append("Atsakymas gautas")
    mqtt_messages.append(payload)


# Nustatyta on_message funkcija kaip veiksmas, kai gaunamas naujas pranešimas
mqtt_client.on_message = on_message

# Prenumeruojama tema, kad gauti pranešimus
mqtt_client.connect(mqttBroker, 1883)
mqtt_client.subscribe(topic)
mqtt_client.loop_start()

# Autorizacijos tokenas, kuris sukurtas anksčiau. Žr.: https://developer.spotify.com/documentation/web-api/concepts/authorization
token = 'BQDozoES0QxAphH6Ac1_xM_Fv_t8HtCqCxYdf_PGp0J5QZE29RjEC1NRP50-Vn-qGXzt5cGDrNcjoBs5Yuhu31LM_9RcTKxJGpYUZpefWlXI1a8At4TUYiDOJjoHgQ0i_J7PuVU6oApaJwRArHg-2W1F_zbd_dv-1d6jPY0YEVSYD45knTPAXzQqwVn3UF3TqbN6m5ACkZvadKyqWJtHuncrWKpq7WDn2QRvREt6rAM1hsNVmGVl8pDxIC33emuz0JmjDlbkbJOqIBDC_qxOt3mk'

#funkcija, kuri naudojama padaryti užklausas į Spotify API
def fetch_web_api(endpoint, method, body=None):
    url = f'https://api.spotify.com/{endpoint}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=body)
    return response.json()

# funkcija, kuri naudoja užklausų funkciją, kad gautų informaciją apie tam tikrus duomenis (atlikėjus )
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
            top_track_response = fetch_web_api(
                f'v1/artists/{item["id"]}/top-tracks?country=US', 'GET'
            )
            if top_track_response and 'tracks' in top_track_response:
                top_track_name = top_track_response['tracks'][0]['name']
                artist_info['song_name'] = top_track_name
            else:
                artist_info['song_name'] = 'Unknown'
            
            artists_info.append(artist_info)
        
        # Įrašomi duomenys į JSON failą
        with open('artists.json', 'w') as file:
            json.dump(artists_info, file)
        
        return artists_info
    else:
        return []

@app.route('/')
def index():
    # duomenų gavimas iš Spotify API ir įrašyti  į JSON failą
    top_artists = get_top_artists()
    # duomenų siuntimas į MQTT brokerį
    send_to_mqtt()
    return render_template('index.html', top_artists=top_artists)

#įėjus į web šiuo keliu galima matyti žinutes kurios json formatu buvo siųstos iš mqtt
@app.route('/mqtt_messages')
def get_mqtt_messages():
    return jsonify({'messages': mqtt_messages})


if __name__ == '__main__':
    app.run(debug=True)
