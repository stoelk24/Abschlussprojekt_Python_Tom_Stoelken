### Tom Stoelken – ETS24 – 04.05.2025 ###

## Dieses System dient dazu, die UID einer RFID-Karte auszulesen und mit zuvor hinterlegten Werten
## abzugleichen. Erkennt das System eine gespeicherte UID, leuchtet die RGB-LED grün auf.
## Gleichzeitig wird der zugehörige Name zusammen mit einem Zeitstempel über das MQTT-Protokoll
## an Node-RED gesendet. Wird hingegen eine unbekannte UID erkannt, schaltet sich die LED auf Rot.
## Desweiteren werden sowohl die aktuelle Temperatur, als auch die aktuelle Luftfeuchtigkeit
## durch einen AHT10 Sensor gemessen und sowohl in der Konsole als auch in der Datenbank ausgegeben.

### Version 1.0 – Stand: 12.05.2025

## Die Hardware besteht aus einem ESP32 mit WLAN-Funktion, einem RFID-Lesemodul vom Typ RC522
## sowie einer RGB-LED und einem AHT10 zur Messung von Temperatur und Luftfeuchtigkeit.
## Das RFID-Modul ist über SPI mit dem ESP32 verbunden.
## Dabei wird GPIO 21 für SCK, GPIO 19 für MISO, GPIO 23 für MOSI, GPIO 18 für den Chip-Select und
## GPIO 22 für den Reset verwendet. Die Stromversorgung erfolgt über 3V3 und GND.

## Die RGB-LED ist ebenfalls mit dem Mikrocontroller verbunden.
## Der rote Kanal ist auf GPIO 14 gelegt, der grüne auf GPIO 12 und der blaue auf GPIO 27.
## GND der LED ist mit GND des Controllers verbunden.

## Der AHT 10 ist auch mit dem Mikrocontroller verbunden.
## Der SCL Pin ist mit GPIO 16 verbunden, SDA mit GPIO 17. GND und 3V3 sind seitens des
## Controllers angeschlossen. Zwischen SDA und SCL Pin befinden sich aber noch jeweils
## ein Pull-Up-Widerstand mit 4,7k Ohm




from machine import Pin, SPI
import network
import time
import json
from machine import I2C					#fuer AHT10
from aht10 import AHT10
from mfrc522 import MFRC522				#Funktion aufrufen
from umqtt.simple import MQTTClient		#MQTT Client
import ujson


### WLAN Konfiguration ###

x = 0  									# Ausgabe ,,Verbinde..``

wlan = network.WLAN(network.STA_IF)  	# Client Konfiguration
wlan.active(False)  					# WLAN aus
time.sleep(0.5)  						# Wartezeit

wlan.active(True)  						# WLAN ein
time.sleep(0.5)  						# Wartezeit

if not wlan.isconnected():  						# wenn WLAN nicht verbunden
    wlan.connect('FRITZ!Box 5530 IQ', '56533538885076278550')  # individuelle Zugangsdaten

    timeout = 100  									# Timeout nach 10 Sekunden
    while not wlan.isconnected() and timeout > 0: 	# solange keine Verbindung besteht
        if x == 0:  								# einmalige Ausgabe
            print("Verbinde...")  					# Textausgabe
            x += 1
        time.sleep(0.1)								# Wartezeit
        timeout -= 1

    if wlan.isconnected():  				# wenn Verbindung hergestellt wurde
        print("Erfolgreich verbunden")  	# Textausgabe
        print("IP: ", wlan.ifconfig()[0])  	# IP-Adresse ausgeben
    else:
        print("Verbindung fehlgeschlagen")  # Ausgabe in Konsole

else:  										# ansonsten
    print("Bereits verbunden")  			# Textausgabe

### RFID-Leser ### 

reader = MFRC522(baudrate=1000000, spi_id=0, sck=18, miso=19, mosi=23, cs=21, rst=22)  # RFID Reader konfiguriert

### LED RGB ###

red = Pin(14, Pin.OUT)  	# roter Pin der RGB-LED an Pin14
green = Pin(12, Pin.OUT)	# grüner Pin der RGB-LED an Pin14
blue = Pin(13, Pin.OUT) 	# blauer Pin der RGB-LED an Pin14

### Temperatur- und Feuchtigkeitssensor AHT10 ###
i2c = I2C(1, scl=Pin(16), sda=Pin(17))		# Pinbelegung des AHT10, 3V3 und GND von Controller
aht = AHT10(i2c)

### MQTT Konfiguration ###

MQTT_SERVER = "192.168.178.56" 			# IP des MQTT-Servers
CLIENT_ID = "STOE"  					# Client Bezeichnung (persoenl. Kuerzel)

mqttClient = MQTTClient(CLIENT_ID, MQTT_SERVER, port=1883, user=None, password=None, keepalive=30, ssl=False, ssl_params={})


### Timestamp ###

def stamp():
    zeit = time.localtime() 	# Lokale Zeit abrufen
    
    datum = str(str(zeit[2]) + "." + str(zeit[1]) + "." + str(zeit[0]) + " um " + str(zeit[3]) + ":" + str(zeit[4]) + ":" + str(zeit[5]))
    print(datum)  				# Ausgabe des aktuellen Datums
    return datum  				# Verwendung außerhalb der Funktion

### Hauptprogramm ###

RFID = [446639667, 447506051]  	# Zugangsberechtigte 
names = ["Tom", "Henning"]  	# Namen der Zugangsberechtigten
liste = 2  						# Anzahl der Berechtigten für die For-Schleife

while True:
    reader.init()  				# RFID initialisieren
    (stat, tag_type) = reader.request(reader.REQIDL)

    if stat != reader.OK:
        time.sleep(0.5)			# Wartezeit
        continue

    print("UID wird gelesen...")	# Ausgabe in Konsole
    (stat, uid) = reader.SelectTagSN()

    if stat != reader.OK:
        print("UID konnte nicht gelesen werden.")	# bei fehlerhafter/falscher Karte
        time.sleep(0.5)								# Wartezeit
        continue

    print("UID erkannt.")							# Ausgabe in Konsole
    card = int.from_bytes(bytes(uid), "little", False)
    print("Card ID:", card)							# Ausgabe in Konsole

    # Standardwerte
    save = 0				# Angabe von Standardwerten
    person = "Unbekannt"

    for code in range(liste):
        if RFID[code] == card:
            save = 1
            person = names[code]
            break

    # LED
    if save:
        green.value(1)		# Einschalten der gruenen LED
        time.sleep(3)		# Wartezeit
        green.value(0)
    else:
        red.value(1)		# Einschalten der roten LED
        time.sleep(3)		# Wartezeit
        red.value(0)

    # Zeit erfassen
    t = time.localtime()	# Lokale Zeit
    datum = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])

    # Temperatur / Luftfeuchtigkeit
    try:
        temp, hum = aht.read()
        print("Temp: {:.1f}°C, Feuchte: {:.1f}%".format(temp, hum))
    except Exception as e:
        print("Sensorfehler:", e)
        temp, hum = None, None

    # JSON vorbereiten
    data = {
        "Name": person,		# Name 
        "CardID": card,		# Kartennummer
        "Datum": datum,		# Stempeldatum & Zeit
        "Temperatur": round(temp, 1) if temp is not None else None,
        "Luftfeuchtigkeit": str(round(hum)) + " %" if hum is not None else None
    }

    log_in = json.dumps(data)			# Login
    print("Sende MQTT:", log_in)		# Ausgabe in Konsole

    # Senden der Daten an MQTT
    try:
        mqttClient.connect()
        mqttClient.publish("zugang", log_in)	# Publishen in ,,Zugang´´
        mqttClient.disconnect()
    except Exception as e:
        print("MQTT Fehler:", e)				# Ausgabe bei Fehler
        
