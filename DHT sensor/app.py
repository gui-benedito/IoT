from flask import Flask, render_template, request, jsonify
import mysql.connector
import serial
import threading
from datetime import datetime

app = Flask(__name__)

# Configure the serial connection
try:
    ser = serial.Serial('COM3', 9600)  # Change the serial port if necessary
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    ser = None

def create_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost', # your localhost
            user='root', # your user
            password='root', # your password
            database='database', # your database
            auth_plugin='mysql_native_password'  # specify the authentication plugin
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def banco_arduino(timestamp, temperature, humidity):
    conn = create_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO database (timestamp, temperature, humidity) VALUES (%s, %s, %s)",
                   (timestamp, temperature, humidity))
    
    conn.commit()
    cursor.close()
    conn.close()

def read_from_serial():
    if ser is None:
        return
    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            try:
                temperature, humidity = line.split(',')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                banco_arduino(timestamp, float(temperature), float(humidity))
            except ValueError:
                print(f"Invalid data received: {line}")

if ser:
    serial_thread = threading.Thread(target=read_from_serial)
    serial_thread.daemon = True
    serial_thread.start()

@app.route('/')
def main():
    conn = create_connection()
    if conn is None:
        return render_template('index.html', timestamp="No Data", temperature=0, humidity=0)

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM database ORDER BY timestamp DESC LIMIT 1")
    data = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    date = data['timestamp'][:10]
    time = data['timestamp'][11:]
    

    if data:
        return render_template('index.html', date=date, time=time, temperature=data['temperature'], humidity=data['humidity'])
    else:
        return render_template('index.html', timestamp="No Data", temperature=0, humidity=0)

if __name__ == '__main__':
    app.run(debug=True)
