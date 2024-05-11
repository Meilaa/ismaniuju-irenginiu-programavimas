# app2.py
from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Nustatykite MQTT brokerio URL ir temą
mqttBroker = "broker.mqttdashboard.com"
topic = "Kursinis/z"

# Globalus kintamasis, kuriame saugomi gauti MQTT pranešimai
mqtt_messages = []

# Sukurkite MQTT klientą
mqtt_client = mqtt.Client()

json_payload = None

# Funkcija, kuri bus iškviečiama, kai gaunate MQTT pranešimą
def on_message(client, userdata, message):
    global json_payload
    json_payload = json.loads(message.payload)
    mqtt_messages.append("Atsakymas gautas")
    mqtt_messages.append(json_payload)

# Nustatykite on_message funkciją kaip veiksmą, kai gaunate naują pranešimą
mqtt_client.on_message = on_message

# Prenumeruokite temą, kad gautumėte pranešimus
mqtt_client.connect(mqttBroker, 1883)
mqtt_client.subscribe(topic)
mqtt_client.loop_start()

@app.route('/')
def index():
    if json_payload:
        return render_template('index.html', top_artists=json_payload)
    else:
        return "Waiting for MQTT message..."

@app.route('/mqtt_messages')
def get_mqtt_messages():
    return jsonify({'messages': mqtt_messages})

if __name__ == '__main__':
    app.run(debug=True)
