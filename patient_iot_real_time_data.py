import network
import urequests
import ujson
from time import sleep, ticks_ms, ticks_diff
from machine import Pin, I2C
from ahtx0 import AHT10


i2c = I2C(1, scl=Pin(15), sda=Pin(6))

sensor = AHT10(i2c)

# WiFi and backend config
ssid = 'Spectranet-LTE_B509'
password = '9031733864'
EMERGENCY_URL = "http://192.168.8.101:8080/api/monitoring/emergency/"
VITALS_URL  = "http://192.168.8.101:8080/api/monitoring/vitals/receive/"
DEVICE_ID = "SMM_bed_201_node"

button = Pin(14, Pin.IN, Pin.PULL_DOWN)  
DEBOUNCE_MS = 2000

SEND_INTERVAL_MS = 1 * 60 * 1000   # Send vitals every 5 minutes
CHECK_INTERVAL_MS = 30 * 1000        # Check for spikes every 10 seconds

TEMP_HIGH    = 38.0   # Fever threshold (°C)
TEMP_LOW     = 35.0   # Hypothermia threshold (°C)
TEMP_SPIKE   = 1.5

def read_temperature():
    try:
        data = sensor.temperature
        return round(data, 1)
    except Exception as e:
        print("Temperature read error: {}".format(e))
        return None

def send_alert(reason):
    payload = {
        "device_id": DEVICE_ID,
        "message": reason
    }
    try:
        print("Sending alert: {}".format(reason))
        response = urequests.post(
            EMERGENCY_URL,
            headers={"Content-Type": "application/json"},
            data=ujson.dumps(payload),
            timeout=10
        )
        print("Alert sent! Status:", response.status_code)
        response.close()
    except Exception as e:
        print("Failed to send alert: {}".format(e))

# ===== SPIKE DETECTION =====
def check_temp_spike(current_temp, previous_temp):
    """Returns an alert message if a spike or threshold is exceeded, else None"""
    reasons = []

    # Absolute threshold breach
    if current_temp >= TEMP_HIGH:
        reasons.append("HIGH TEMP ALERT: {}C (threshold: {}C)".format(current_temp, TEMP_HIGH))
    elif current_temp <= TEMP_LOW:
        reasons.append("LOW TEMP ALERT: {}C (threshold: {}C)".format(current_temp, TEMP_LOW))

    # Sudden spike from previous reading
    if previous_temp is not None:
        change = abs(current_temp - previous_temp)
        if change >= TEMP_SPIKE:
            direction = "up" if current_temp > previous_temp else "down"
            reasons.append("TEMP SPIKE: jumped {} {}C ({}C -> {}C)".format(
                direction, round(change, 1), previous_temp, current_temp))

    return " | ".join(reasons) if reasons else None

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        print("Waiting for connection...")
        sleep(1)
    print("Connected!", wlan.ifconfig())

def send_alert(reason):
    payload = {
        "device_id": DEVICE_ID,
        "patient_id": "PAT004",
        "message": reason
    }
    try:
        print("Sending alert: {}".format(reason))
        response = urequests.post(
            EMERGENCY_URL,
            headers={"Content-Type": "application/json"},
            data=ujson.dumps(payload),
            timeout=10
        )
        print("Alert sent! Status:", response.status_code)
        print("Body:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send alert: {}".format(e))
        
def send_vitals(temp):
    payload = {
        "device_id": DEVICE_ID,
        "patient_id": "PAT004",
        "temperature": temp,
        "heart_rate": 0,   # Set to 0 if no HR sensor yet
        "spo2": 0          # Set to 0 if no SpO2 sensor yet
    }
    try:
        response = urequests.post(
            VITALS_URL,
            headers={"Content-Type": "application/json"},
            data=ujson.dumps(payload),
            timeout=10
        )
        print("Vitals sent: {} -> Status {}".format(payload, response.status_code))
        response.close()
    except Exception as e:
        print("Failed to send vitals: {}".format(e))

def main():
    connect()
    print("Ready. Button on GP16, connect to GND.")
    last_trigger = 0
    last_vitals_time  = 0
    last_check_time   = 0
    last_button_time  = 0
    last_alert_time   = 0
    ALERT_COOLDOWN_MS = 60 * 1000   # Don't spam alerts, max 1 per minute
    previous_temp     = None
    print(sensor.temperature)
    while True:
        now = ticks_ms()

        if button.value() == 1:  # Button pressed (LOW)
            now = ticks_ms()
            if ticks_diff(now, last_trigger) > DEBOUNCE_MS:
                print("BUTTON PRESSED!")
                send_alert("EMERGENCY: Patient pressed call button")
                last_trigger = now
                
        if ticks_diff(now, last_check_time) >= CHECK_INTERVAL_MS:
            temp = read_temperature()
            if temp is not None:
                print("Temp check: {}C".format(temp))
                alert_msg = check_temp_spike(temp, previous_temp)
                if alert_msg:
                    if ticks_diff(now, last_alert_time) > ALERT_COOLDOWN_MS:
                        send_alert(alert_msg)
                        last_alert_time = now
                    else:
                        print("Alert suppressed (cooldown): {}".format(alert_msg))
                previous_temp = temp
            last_check_time = now
            
        if ticks_diff(now, last_vitals_time) >= SEND_INTERVAL_MS:
            temp = read_temperature()
            if temp is not None:
                print("Temperature: {}C".format(temp))
                send_vitals(temp)
            else:
                print("Could not read temperature, skipping...")
            last_vitals_time = now

        sleep(0.05)

if __name__ == "__main__":
    main()
