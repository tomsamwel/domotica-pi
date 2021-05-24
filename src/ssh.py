import pty
from pexpect import pxssh
from sense_hat import SenseHat

import sys
import signal

connection = 0
sense = SenseHat()

print("INFO: Verbinding wordt opgezet met de host")
s = pxssh.pxssh()
if not s.login('192.168.2.2', 'imrevansurksum', 'wachtwoord van laptop hier'):
    print("FOUT! Verbinding kon niet opgezet worden.")
    # print str(s)
else:
    print("INFO: Verbinding opgezet met host.")
    connection = 1


def send_temp(temp):
    if connection > 0:
        sql = "INSERT INTO kbs.temp (temp) VALUES (" + str(temp) + ");"

        s.sendline('/Applications/XAMPP/xamppfiles/bin/mysql -u root -e "' + sql + '"')
        s.prompt()  # output van de terminal ophalen

        # print(s.before)  # voor debug alles van de terminal printen
        print("INFO: Opdracht(en) uitgevoerd.")
    else:
        print("FOUT: Communicatie met host niet mogelijk.")

def signal_handler(sig, frame):
    print('INFO: Verbinding wordt afgesloten')
    s.logout()
    sense.clear()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
