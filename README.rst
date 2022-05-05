

Setup
=====

Local install
=============

* sudo apt install rtl-433
* sudo apt install jq
* sudo apt install mosquitto-clients


Thingsboard server
==================

* Create device with MQTT transport
* Use MQTT token authentication
    * In the MQTT client, use the MQTT token as 'username'

* Ensure that the firewall will pass MQTT traffic
    * sudo ufw allow 1883


Local device
============

* Use rtl_433 to receive data from the weather station
* Use jq to modify JSON output from rtl_433 into a format expected by Thingsboard
* Use mosquitto_pub to send data from stdin to a MQTT topic in Thingsboard


Example
=======

RTL_SERIAL=77771111153705700
MQTT_HOST=iot.irons.nz
MQTT_PORT=1883
MQTT_VER=mqttv5
MQTT_TOPIC=v1/devices/me/telemetry
MQTT_TOKEN=d6be36748d0a44368dab6515f8807f71

rtl_433 -d:$RTL_SERIAL -F json -M time:unix:utc -M protocol -M level -C si | jq --compact-output --monochrome-output --unbuffered '{ ts: (.time | tonumber * 1000), values: {battery_ok, temperature_C, humidity, wind_dir_deg, wind_avg_km_h, wind_max_km_h, rain_mm, rssi, snr, noise}}' | mosquitto_pub -V $MQTT_VER --host $MQTT_HOST --port $MQTT_PORT --topic $MQTT_TOPIC --username $MQTT_TOKEN -l
