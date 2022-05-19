from datetime import datetime
from time import sleep
import pytz
import getopt, sys
import RPi.GPIO as GPIO

NUM_CPU_CORES = 4
UPDATE_INTERVAL = 60
MAX_TEMP = 70

PIN = 14
TEMP_LIMIT = 40.0
VERBOSE = False


def parse_args():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "p:t:v", ["pin=", "temp=", "verbose"])
    except getopt.GetoptError:
        print("Usage: fantemp.py [-t <temperature] [-p <GPIO pin #>]")
        sys.exit(2)

    global PIN, TEMP_LIMIT, VERBOSE
    for opt, arg in opts:
        if opt in ("-p", "--pin"):
            PIN = int(arg)
        elif opt in ("-t", "--temp"):
            TEMP_LIMIT = float(arg)
        elif opt in ("-v", "--verbose"):
            VERBOSE = True

def get_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            file_content = f.read()
    except:
        print("temperature could not be read")
        set_fan(True) # enable fan to prevent overheating due to the program not beeing able to read the right temperature
        sys.exit(2)

    file_content = file_content.strip('\n')
    temp_in_degrees = int(file_content) / 1000
    return temp_in_degrees

def get_cpu_load():
    try:
        with open('/proc/loadavg') as f:
            file_content = f.read()
    except:
        print("/proc/loadavg could not be read")
        set_fan(True) # enable fan to prevent overheating due to the program not beeing able to read the right cpu load
        sys.exit(2)

    file_content = file_content.strip('\n')

    # Total amount of CPU cores used by processes over the last: [1, 5, 15] minutes
    # https://www.tecmint.com/understand-linux-load-averages-and-monitor-performance/
    cpu_utilization = file_content.split(' ')[:3]

    # calculate relative values
    cpu_load = []
    for x in cpu_utilization:
        cpu_load.append(float(x)/NUM_CPU_CORES)
    
    return cpu_load

def set_fan(status):
    if status:
        if VERBOSE:
            print("turn on fan via pin: %d" % PIN)
        GPIO.output(PIN, GPIO.HIGH)
    else:
        if VERBOSE:
            print("turn off fan via pin: %d" % PIN)
        GPIO.output(PIN, GPIO.LOW)

def update_fan_status():
    # Calculate temp_limit based on day/night mode
    now_utc = datetime.now(pytz.utc)
    now_cet = now_utc.astimezone(pytz.timezone("CET"))
    if now_cet.hour > 23 or now_cet.hour < 9:
        # Night mode (incrase TEMP_LIMIT by 50% to prevent loud fan noise at night)
        temp_limit = TEMP_LIMIT * 1.5
    else:
        # Day mode
        temp_limit = TEMP_LIMIT

    cpu_load = get_cpu_load()
    cpu_temp = get_temp()

    if VERBOSE:
        print("cpu_load: %1.2f, cpu_temp: %2.1f, temp_limit: %2.1f, max_temp: %2.1f" % (cpu_load[0], cpu_temp, temp_limit, MAX_TEMP))
        

    # only enable Fan if cputemp >= temp_limit & cpu_load > 25% over the last minute OR cpu_temp >= MAX_TEMP
    if (cpu_temp >= temp_limit and cpu_load[0] > 0.25) or cpu_temp >= MAX_TEMP:
        # Enable Fan
        set_fan(True)
    # only disable Fan if cputemp < temp_limit & cpu_load < 50% over the last minute
    elif cpu_temp < temp_limit and cpu_load[0] < 0.5:
        # Disable Fan
        set_fan(False)


if __name__ == "__main__":
    parse_args()

    #use GPIO pin numbering not physical
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN, GPIO.OUT)

    while True:
        update_fan_status()
        sleep(UPDATE_INTERVAL)
