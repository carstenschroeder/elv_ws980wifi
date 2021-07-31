# elv_ws980wifi
Support for ELV WS980Wifi weather station

## Example
The following two code snippets have to be added to your **`configuration.yaml`**:

### Important
Please replace the **`host`** value in the first code snippet with the IP address of your weather station.

```javascript
elv_ws980wifi:
  devices:
    - name: elv_weather_station
      host: '192.168.0.2'
      port: 45000
```


```javascript
sensor:
  - platform: elv_ws980wifi
    name: "in_temp"
    unit_of_measurement: '°C'

  - platform: elv_ws980wifi
    name: "out_temp"
    unit_of_measurement: '°C'

  - platform: elv_ws980wifi
    name: "dewpoint"
    unit_of_measurement: '°C'

  - platform: elv_ws980wifi
    name: "windchill"
    unit_of_measurement: '°C'

  - platform: elv_ws980wifi
    name: "heatindex"
    unit_of_measurement: '°C'

  - platform: elv_ws980wifi
    name: "in_humidity"
    unit_of_measurement: '%'

  - platform: elv_ws980wifi
    name: "out_humidity"
    unit_of_measurement: '%'

  - platform: elv_ws980wifi
    name: "abs_baro"
    unit_of_measurement: 'mbar'

  - platform: elv_ws980wifi
    name: "rel_baro"
    unit_of_measurement: 'mbar'

  - platform: elv_ws980wifi
    name: "wind_dir"
    unit_of_measurement: '°'

  - platform: elv_ws980wifi
    name: "wind_speed"
    unit_of_measurement: 'km/h'
    factor: 3.6

  - platform: elv_ws980wifi
    name: "gust_speed"
    unit_of_measurement: 'km/h'
    factor: 3.6

  - platform: elv_ws980wifi
    name: "rain_rate"
    unit_of_measurement: 'mm/h'

  - platform: elv_ws980wifi
    name: "rain_day"
    unit_of_measurement: 'mm'

  - platform: elv_ws980wifi
    name: "rain_week"
    unit_of_measurement: 'mm'

  - platform: elv_ws980wifi
    name: "rain_month"
    unit_of_measurement: 'mm'

  - platform: elv_ws980wifi
    name: "rain_year"
    unit_of_measurement: 'mm'

  - platform: elv_ws980wifi
    name: "rain_totals"
    unit_of_measurement: 'mm'

  - platform: elv_ws980wifi
    name: "light"
    unit_of_measurement: 'lux'

  - platform: elv_ws980wifi
    name: "uv"
    unit_of_measurement: 'W/m2'

  - platform: elv_ws980wifi
    name: "uvi"
    unit_of_measurement: ''
```