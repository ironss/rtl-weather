Purpose
#######

Functionality
=============

* Receive local data from weather station over 433 MHz RF link
* Receive local data from other local devices via MQTT
* Receive local data from other local devices via HTTP API

* Receive weather forecasts from various weather forecast sites
* Receive tide forecasts from various sources
* Calculate satellite passes from satellite-prediction software
* Calculate sunrise, sunset, moonrise and moonset times

* Process local data
    * Convert wind speed and direction to cartesian (XY) values
    * Low-pass filter these values to remove noise
    * Calculate rain rates from rain counter
        * 1-hour rain rate
        * 24-hour rain rate

* Store raw and processed values in a suitable database

* Make data updates available via a local MQTT broker
* Send weather updates to various weather and IOT sites using their HTTP API
* Publish data updates to various MQTT brokers

* Make current data available via local HTTP API
* Make current data available via Modbus
* Make historical data (from the database) vailable via local HTTP API

* Make current and historical data available via a local website


Parameters of interest
======================

* Outside air temperature
* Inside air temperature
* Soil temperature

* Air pressure
* Air humidity

* Wind speed average
* Wind speed gust
* Wind direction raw
* Wind direction smoothed

* Battery level of each battery-powered device
* Signal level of each RF and WiFi device
* SNR of each RF and WiFi device

* Weather forecasts at various locations
* Sunrise, sunset, moonrise and moonset forecasts at various


Tide predictions
----------------
* Primary ports tide data, updated annually
* Secondary ports data
* Regions -- a named subset of ports
* Trips -- a named region over a range of dates; date range can be open-ended at either end
* Tide predictions are made for trips; the predictions are updated when
    * new primary port data is added (~annually)
    * a port is added to or removed from a region
    * a trip is modified by changing the date range


Satellite predictions
---------------------
* A list of TLE data file sources
* Historical values for TLE data files
* Named places with geo location data
* Named sets of places
* Named sets of satellites of interest
* Predictions: tuple of (place-set, satellite-set, time-range)


Measurement data
----------------
* Sensors (types of sensors)
* Sensor parameters - list of measurements for each type of sensor
* Available sensors - named instances of sensors
* Sensor reports - timestamped set of measurements from each available sensor
* Sensor measurements - an individual timestamp measurement from each sensor


Setup
=====

Local install
-------------

* sudo apt install rtl-433
* sudo apt install jq
* sudo apt install mosquitto-clients


Thingsboard server
------------------

* Create device with MQTT transport
* Use MQTT token authentication
    * In the MQTT client, use the MQTT token as 'username'

* Ensure that the firewall will pass MQTT traffic
    * sudo ufw allow 1883


Local device
------------

* Use rtl_433 to receive data from the weather station
* Use jq to modify JSON output from rtl_433 into a format expected by Thingsboard
* Use mosquitto_pub to send data from stdin to a MQTT topic in Thingsboard


Example
=======

RTL_SERIAL=<redacted>
MQTT_HOST=<redacted>
MQTT_PORT=1883
MQTT_VER=mqttv5
MQTT_TOPIC=v1/devices/me/telemetry
MQTT_TOKEN=<redacted>

rtl_433 -d:$RTL_SERIAL -F json -M time:unix:utc -M protocol -M level -C si | jq --compact-output --monochrome-output --unbuffered '{ ts: (.time | tonumber * 1000), values: {battery_ok, temperature_C, humidity, wind_dir_deg, wind_avg_km_h, wind_max_km_h, rain_mm, rssi, snr, noise}}' | mosquitto_pub -V $MQTT_VER --host $MQTT_HOST --port $MQTT_PORT --topic $MQTT_TOPIC --username $MQTT_TOKEN -l


Use SQLite to store the data from rtl_433, rather than a log file

Advantages
----------

* Can separate receiving raw data from uploading to server.
* Can record which data has been uploaded


Disadvantages
-------------

* How to know when new data has arrived


Notes
=====

Using


rtl_433 -> database
database -> script -> MQTT upload


# Initialise the database
rm rtl-weather.db
sqlite3 rtl-weather.db 'CREATE TABLE IF NOT EXISTS "rtl_json" ( "id" INTEGER PRIMARY KEY AUTOINCREMENT, "json" TEXT, "ts" INTEGER);'


# Use jq to modify the JSON
# This takes a few seconds for 20k records
(
echo "BEGIN TRANSACTION;";

cat rtl-thing.log | tail -n 100 | jq --unbuffered --compact-output -r '@sh "\(now) \(.|tostring)"' | (while true; do read ts json; if [ _$ts = _ ]; then exit 0; fi ; echo "INSERT OR IGNORE INTO rtl_json (json, ts) VALUES ($json, $ts);"; done);

echo "COMMIT TRANSACTION;"; ) | sqlite3 rtl-weather.db


# Use 'date +%s' to get the timestamp in unix1970 seconds
# This takes a few 10s of seconds for 20k records
(
echo "BEGIN TRANSACTION;";
cat rtl-thing.log | tail -n 100 | (while true; do read json; if [ "_$json" = "_" ]; then exit 0; fi ; echo "INSERT OR IGNORE INTO rtl_json (json, ts) VALUES ('$json', $(date +%s));"; done);
echo "COMMIT TRANSACTION;";
) sqlite3 rtl-weather.db


Note: Using jq, the data stored in the database has trailing zeros stripped from
floating point numbers. This reduces the size of the database.

For 20k records
* log file 7 MB
* sqlite database with trailing zero stripped: 6.3 MB
* sqlite database with original data: 7.4 MB

However, the sqlite database includes an additional timestamp
and a sequence number

The weather station sends a reading about every 45 seconds, or
about 2000 readings per day. Each reading is about 350 bytes of
JSON.

