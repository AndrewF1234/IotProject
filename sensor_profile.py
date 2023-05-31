import smbus
import board
import math
import adafruit_ahtx0
import busio
import adafruit_tsl2561
import time
import datetime
import csv
import boto3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

access_key = ''
secret_key = ''
bucket_name = 'collecttestexample'
file_path = '/var/www/html/5-31-2023.csv'
key_name = ''
samples = int((1 * 60)/ 5)

try:
    filepath = '/home/raspberry/IotEnvironmentProject/readingValues/'
    filename = '5-31-2023.csv'
    filesvg = 'data.svg'
    i2c = busio.I2C(board.SCL, board.SDA)
    light_sensor = adafruit_tsl2561.TSL2561(i2c, 0x29)
    humidity = adafruit_ahtx0.AHTx0(board. I2C())
    bus = smbus.SMBus(1)
    tmpAddress=0x50 # 12c connection
    beta =  2180# represents maximum digital value should be 4096
    humidity.calibrate()
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
except Exception as e:
    print(e)


header = ['date', 'Temperature', 'Temperature 2', 'Humidity', 'Light Intensity(Lux)']
if (not os.path.exists(filepath + filename)):
    with open(filepath + filename, "w+") as f:
        writer = csv.writer(f)
        writer.writerow(header)

def read_temp():
    data =bus.read_i2c_block_data(tmpAddress, 0, 2) # gets block data
    raw_data = ((data[0] & 0x0f) << 8 | data[1]) & 0xfff # takes block data from device (analog) converts raw data
    voltage = (raw_data / beta)* 3.3 # find voltage and ratio it using beta to max voltage
    thermistor_resistance = (100000* (3.3-voltage))/voltage # resistance found using voltage divider equation
    # temperature found based on steinhart-hard equation.
    temperature = (1/(1/298.15+ ((1/beta) * math.log(thermistor_resistance/100000)))) - 273.15
    return temperature
def read_AHT20():
    return humidity.temperature;
def read_humidity():
    if (humidity.relative_humidity> 0 and humidity.relative_humidity < 100):
        return humidity.relative_humidity
    else:
        return 0.0
def read_light():
    light_sensor = adafruit_tsl2561.TSL2561(i2c, 0x29)
    return light_sensor.lux;
def read_time():
    return datetime.datetime.today()
last_reading = 0
while True:
    if (last_reading + 5 < time.time()):
        last_reading = time.time()
        try:
            temp = read_temp()
        except Exception as e:
            temp = e
        try:
            aht20 = read_AHT20()
        except Exception as e:
            aht20 = e
        try:
            humid = read_humidity()
        except Exception as e:
            humid = e
        try:
            light = read_light()
        except Exception as e:
            light = e
            
        print(f"Time: {read_time()}")
        print(f"Temp_1.1: {temp}")
        print(f"Temp_AHT20: {aht20}")
        print(f"Humidity: {humid}")
        print(f"Light: {light}")
        
        with open(filepath + filename, 'a') as f:
            writer = csv.writer(f)
            data = [read_time(), temp, aht20, humid, light]
            writer.writerow(data)
            f.close()
        #try:
        #    s3.upload_file(file_path,bucket_name,"data/new.csv")
        #except Exception as e:
        #    print("yuh:" + str(e))
        
        df = pd.read_csv(filepath + filename)
        samples = min(len(df.index)-1,samples)
        plt.figure()
        df['date'] = pd.to_datetime(df['date'], format="mixed")
        plt.plot(df['date'][-samples:], df['Temperature'][-samples:])
        plt.plot(df['date'][-samples:], df['Temperature 2'][-samples:])
        plt.plot(df['date'][-samples:], df['Humidity'][-samples:])
        plt.plot(df['date'][-samples:], df['Light Intensity(Lux)'][-samples:])
        plt.legend(["TemperatureOne (C)", "TemperatureTwo (C)", "Humidity (%)", "Lux"],
                   loc = "lower right")
        plt.savefig(filepath + filesvg)
        plt.close()
        #plt.show()