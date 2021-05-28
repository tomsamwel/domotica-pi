import pty, os, time, sys, signal, mysql.connector
from sense_hat import SenseHat

# Hostname (aanpasbaar met --hostname argument)
hostname = "MacBook-Pro-van-Imre.local"

database = None
cursor = None
mistakes = 0
debug = False
safemode = False

sense = SenseHat()

for opt in sys.argv:
    if opt == "-d" or opt == "--debug" or opt == '--verbose':
        debug = True
        print("INFO: Gebruik maken van debug.")
    elif "--hostname" in opt:
        # De gebruiker heeft een andere hostname opgegeven
        argument = (opt.split("="))
        if 0 <= 1 < len(argument):
            print("INFO: Andere host wordt ingesteld.")
            hostname = argument[1]
        else:
            print("WAARSCHUWING: Hostname argument wordt genegeerd.")
    elif opt == "--safemode" or opt == "--nodb":
        print("INFO: Veilige modus gebruiken, data zal niet worden opgeslagen.")
        safemode = True



def terminate(forced):
    # Het programma moet worden afgesloten
    if forced:
        print('INFO: Programma wordt afgesloten vanwege een niet-afhandelbare fout.')
    else:
        print('INFO: Programma wordt afgesloten.')

    sense.clear()
    sys.exit(0)

def log(message):
    # Iets uitprinten (mits -d of --debug als argument is meegegeven
    if debug:
        print(message)

try:
    # Poging tot het maken van een verbinding met de database
    database = mysql.connector.connect(
        host=hostname,
        user="root",
        password="root"
    )
    cursor = database.cursor()
except:
    log("FOUT: Databaseverbinding kon niet worden opgezet.")
    terminate(True)

def get_cpu_temp():
    # Temperatuur van de CPU ophalen voor een nauwkeurige omgevingstemperatuur
    res = os.popen("vcgencmd measure_temp").readline()
    t = float(res.replace("temp=", "").replace("'C\n", ""))
    return (t)

def get_smooth(x):
    # Afronden naar wat moois
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
        sense.clear(0, 255, 0)
    elif (temp < lowest_temp):
        # actie ondernemen om te verwarmen
        action = "verwarmen"
        sense.clear(255, 0, 0)
    else:
        # Todo: als de verwarming of verkoeling uit moet, dan moet hier een else komen
        sense.clear(255, 255, 255)
    return (action)

if debug == False:
    print("Gegevens worden nu gemeten en opgeslagen.")
    print("Gebruik CTRL + C om het programma af te sluiten.")

def signal_handler(sig, frame):
    # Iemand heeft CTRL+C ingedrukt
    log("INFO: Gebruiker probeert het programma te stoppen.")
    terminate(False)

def execute_sql(query):
    if not safemode:
        cursor.execute(query)
        database.commit()

def fetch_sql(query):
    cursor.execute(query)
    return cursor.fetchall()


# Gewenste temperatuur en maximale afwijking
# desired_temp = 20
max_diff = 1.5
desired_temp = None
try:
    # desired_temp = int(input("Wat moet de temperatuur worden? "))
    desired_temp = fetch_sql("SELECT temperature FROM domotica.users LIMIT 1")[0][0];
except KeyboardInterrupt:
    terminate(False)
print("")

highest_temp = desired_temp + max_diff
lowest_temp = desired_temp - max_diff

print("--- TEMPERATUUR ---")
print("Gewenste tempereratuur: %d C (opgehaald vanuit database)" % desired_temp)
print("Verwarmen bij: %d C" % lowest_temp)
print("Koelen bij: %d C" % highest_temp)
print("------------------------")
print("")


signal.signal(signal.SIGINT, signal_handler)

while True:
    # Temperaturen van de pi ophalen
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    t_cpu = get_cpu_temp()
    h = sense.get_humidity()
    p = sense.get_pressure()

    # de temperatuur corrigeren naar een accuratere vorm
    t = (t1 + t2) / 2
    t_corr = t - ((t_cpu - t) / 1.5)
    t_corr = get_smooth(t_corr)

    get_climate_action(t_corr)

    try:
        # Gewenste temperatuur ophalen
        desired_temp = fetch_sql("SELECT temperature FROM domotica.users LIMIT 1")[0][0]

        # Opgehaalde data naar de database schrijven
        execute_sql("INSERT INTO domotica.temperature (`temperature`) VALUES (" + str(t_corr) + ");")
        execute_sql("INSERT INTO domotica.humidity (`humidity`) VALUES (" + str(h) + ");")
        execute_sql("INSERT INTO domotica.pressure (`pressure`) VALUES (" + str(p) + ");")

        log("INFO: Data succesvol opgeslagen. " + "(" + str(round(t_corr, 1)) + " C, " + str(round(h)) + "%, " + str(round(p)) + " kPa)")
    except Exception as e:
        # Schrijven naar de database is niet gelukt
        mistakes += 1
        if mistakes > 1:
            # Tweede keer lukt het schrijven weer niet
            log("FOUT: Verbinding met database werd verbroken. MySQL heeft het volgende gemeld:")
            log(e)
            terminate(True)
        else:
            log("WAARSCHUWING: De volgende fout is opgetreden bij het opslaan van de data:")
            log(e)

    time.sleep(10)



