import os
import time
from sense_hat import SenseHat

# Gewenste temperatuur en maximale afwijking
#desired_temp = 20
max_diff = 1.5

desired_temp = int(input("Wat moet de temperatuur worden? "))
print()

highest_temp = desired_temp + max_diff
lowest_temp = desired_temp - max_diff

# get CPU temperature
def get_cpu_temp():
    res = os.popen("vcgencmd measure_temp").readline()
    t = float(res.replace("temp=", "").replace("'C\n", ""))
    return (t)


# use moving average to smooth readings
def get_smooth(x):
    if not hasattr(get_smooth, "t"):
        get_smooth.t = [x, x, x]
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x
    xs = (get_smooth.t[0] + get_smooth.t[1] + get_smooth.t[2]) / 3
    return (xs)

def get_climate_action(temp):
    action = "-"
    if (temp > highest_temp):
        # actie ondernemen om te koelen
        action = "koelen"
    elif(temp < lowest_temp):
        # actie ondernemen om te verwarmen
        action = "verwarmen"
    # Todo: als de verwarming of verkoeling uit moet, dan moet hier een else komen
    return (action)

sense = SenseHat()

print("--- KLIMAATCONTROLE ---")
print("Gewenste tempereratuur: %d C" % desired_temp)
print("Verwarmen bij: %d C" % lowest_temp)
print("Koelen bij: %d C" % highest_temp)
print("------------------------")
print("")

while True:
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    t_cpu = get_cpu_temp()
    h = sense.get_humidity()
    p = sense.get_pressure()

    # dit zorgt er hopelijk voor dat de temperatuur een soort van klopt
    t = (t1 + t2) / 2
    t_corr = t - ((t_cpu - t) / 1.5)
    t_corr = get_smooth(t_corr)



    print("t=%.1f  h=%d  p=%d, act=%s" % (t_corr, round(h), round(p), get_climate_action(t_corr)))

    time.sleep(5)