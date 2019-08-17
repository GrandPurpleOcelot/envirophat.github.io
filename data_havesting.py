from envirophat import light, weather, motion, analog, leds
import io
import mysql.connector
import datetime
import sys
from time import sleep

# Set up db connection to dump sensor data into:
db = mysql.connector.connect(user='root', password ='root', unix_socket='/var/run/mysqld/mysqld.sock', database='enviro')
cursor = db.cursor()

SLEEP_INTERVAL = 5

# Parameters for blinking LED
SHORT_BLINK = 0.2
LONG_BLINK = 1.5

def blink_3_times(): # 3 blinks means script has been interrupted
    for i in range(3):
        leds.on()
        sleep(SHORT_BLINK)
        leds.off()
        sleep(SHORT_BLINK)
 
def blink_long(): # long blink means the data has been pushed to MySQL
    for i in range(1):
        leds.on()
        sleep(LONG_BLINK)
        leds.off()

try:
    while True:
        timestamp = datetime.datetime.now().isoformat()
        lux = light.light()
        rgb = str(light.rgb())[1:-1].replace(' ', '')
        acc = str(motion.accelerometer())[1:-1].replace(' ', '')
        temp = weather.temperature()
        press = weather.pressure()
        cpu_temp = float(open("/sys/class/thermal/thermal_zone0/temp", "r").readline())/1000
        # print("INSERT INTO enviro_log VALUES('%s',%f,'%s','%s',%f,%f,%f);" % (timestamp, lux, rgb, acc, temp, press, cpu_temp))
        cursor.execute("INSERT INTO enviro_log VALUES('%s',%f,'%s','%s',%f,%f,%f);" % (timestamp, lux, rgb, acc, temp, press, cpu_temp))
        db.commit()
        blink_long()
        sleep(SLEEP_INTERVAL)

except KeyboardInterrupt:
    blink_3_times()
    leds.off()
    db.close()
