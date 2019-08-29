# IOT Monitor Environment Data with Enviro pHAT for Raspberry Pi
Visit my dashboard at: https://canescent-cow-0653.dataplicity.io

User: pi

Password: GrandBudapest2014

The following are screenshots for the app in this repo:

![gif](/screenshots/captured.gif)

## Full Analysis of Sensor Data

https://grandpurpleocelot.github.io/IOTanlysis.github.io/

## Introduction

The Enviro pHAT from Pimoroni is an add-on board for Raspberry Pi with a set of sensors on-board to capture surrounding environment data. List of included sensors:

* BMP280 temperature/pressure sensor
* TCS3472 light and RGB colour sensor
* LSM303D accelerometer/magnetometer sensor

We can stream all of our enviro pHAT data to a Dash web application and have that service turn our data into a nice dashboard that we can access from our laptop or mobile device. This project includes the production of Dash app to displays conditions in your house in real-time, as well as provide statistics for light usage. The Enviro pHat costs \$21, pair with Pizero W \$5-\$10 and required accessories (microSD card and power cables), you have a complete IOT sensor solution for under \$40.

![screenshot3](/screenshots/complete.jpg)

## Hardware Requirements

1 x Pi Zero W with pre-soldered GPIO . If you want to solder the pin yourself, check out the guide from [Raspberry Website](https://www.raspberrypi.org/blog/getting-started-soldering/).

![screenshot1](/screenshots/pizero.jpg)

1 x [Enviro pHat](https://shop.pimoroni.com/products/enviro-phat)

![screenshot2](/screenshots/envirophat.jpg)

1 x microSD card (recommend at least 16gb)

1 x micro usb cable and 1.5A power supply

1 x  Pi Zero case ([optional](https://shop.pimoroni.com/products/pibow-zero-ver-1-3)). The closed case helps Enviro pHAT from staying directly above the pi's hot CPU that can throw off the temperature sensor.

## Getting Started

Download and flash [Raspbian Lite](https://www.raspberrypi.org/downloads/raspbian/) on the microSD card

## Data Collection

### Install python 3 libraries for the Enviro pHAT:

```bash
sudo apt-get install python3-envirophat
```

You can find the documentation for the functions in the Enviro pHAT python library here: http://docs.pimoroni.com/envirophat/

### Install MySQL database:

```bash
sudo apt-get install mariadb-server
sudo apt-get install python-mysqldb
```

You can find the tutorial for setup a MySQL database on a Raspberry Pi [here](https://pimylifeup.com/raspberry-pi-mysql/)

**Remote Server Configurations:**
Grant remote access connection to Mysql:

```sql
 GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'password' WITH GRANT OPTION;
 FLUSH PRIVILEGES;
 ```

If you want to connect to the Mysql from a remote server, such as another Raspberry Pi or your PC, you will likely get a 111 error: Connection refused. MySQL is bound to localhost by default, and we need to unbind the ip address so we can access MySQL remotely:

On your device, edit /etc/mysql/my.cnf

Find bind-address=127.0.0.1, edit it to bind-address=0.0.0.0

If bind-address=0.0.0.0 does not exist, add one into the my.cnf.

Restart MySQL

**Connect MySQL database in Python using MySQL Connector Python:**

```bash
pip install mysql-connector-python
```

**Test connection:**

Here is a little script that tests for database connection:

```python
import mysql.connector
from mysql.connector import Error
connection = mysql.connector.connect(host='localhost/remote IP',
                             database='python_db',
                             user='youruser',
                             password='yourpassword')
if connection.is_connected():
   db_Info = connection.get_server_info()
   print ("Connected to MySQL database... Version: ",db_Info)
   cursor = connection.cursor()
   cursor.execute("select database();")
   record = cursor.fetchone()
   print ("Connected to database - ", record)
else:
    print ("Error while connecting to MySQL")

if(connection.is_connected()):
    cursor.close()
    connection.close()
    print ("MySQL connection is closed")
```

Run the data collection script:

```bash
python data_havesting.py
```

Now the data can be stored and retrieved from MySQL database. I recommend running the sript as systemctl deamon so the Pi Zero can automatically resume data collection after a power failure.

## Data Visualization with Dash

### Running the app locally

First create a virtual environment with conda or venv inside a temp folder, then activate it.

```bash
virtualenv venv

# Windows
venv\Scripts\activate
# Or Linux
source venv/bin/activate
```
Install the requirements with pip:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

Dash uses Flash under the hood, so you can just deploy a Dash app just like you would a Flask app.
Deploy the app on WSGI HTTP Server - Gunicorn:

```bash
gunicorn app:server -b 0.0.0.0:5000 --timeout=1200 --workers 2
```

If you want to deploy to a web server, you might want to try NGINX or Apache. To share a Dash app, you need to "deploy" your Dash app to a server and open up the server's firewall to the public or to a restricted set of IP addresses.
 
