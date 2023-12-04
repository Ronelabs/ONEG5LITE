"""
RONELABS GATEWAY ONE G5 LITE Control plugin for Domoticz
Author: Ronelabs team,
Version:    0.0.1: alpha
            0.0.2: beta
            1.1.1: validate

"""
"""
<plugin key="ONEG5LITEGW" name="RONELABS GW ONE G5 LITE Control" author="Ronelabs team" version="1.1.1" externallink="https://github.com/Ronelabs/ONEG5LITE.git">
    <description>
        <h2>RONELABS'S GATEWAY ONE G5 LITE Control plugin</h2><br/>
        Easily control RONELABS'S GATEWAY ONE G5 LITE<br/>
        <h3>Set-up and Configuration</h3>
    </description>
    <params>
        <param field="Mode6" label="Logging Level" width="200px">
            <options>
                <option label="Normal" value="Normal"  default="true"/>
                <option label="Verbose" value="Verbose"/>
                <option label="Debug - Python Only" value="2"/>
                <option label="Debug - Basic" value="62"/>
                <option label="Debug - Basic+Messages" value="126"/>
                <option label="Debug - Connections Only" value="16"/>
                <option label="Debug - Connections+Queue" value="144"/>
                <option label="Debug - All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import urllib.parse as parse
import urllib.request as request
from datetime import datetime, timedelta
import time
import base64
import itertools
import os
import subprocess as sp
from distutils.version import LooseVersion

class deviceparam:

    def __init__(self, unit, nvalue, svalue):
        self.unit = unit
        self.nvalue = nvalue
        self.svalue = svalue


class BasePlugin:

    def __init__(self):

        self.debug = False
        self.PowerSupply = False
        self.PowerPresent = 0
        self.BatteryLevel = 0
        self.LEDpowerOn = 1
        self.LastBattUpdate = datetime.now() - timedelta(seconds=1200)
        self.statussupported = True
        self.Modeauto = True
        return


    def onStart(self):

        # setup the appropriate logging level
        try:
            debuglevel = int(Parameters["Mode6"])
        except ValueError:
            debuglevel = 0
            self.loglevel = Parameters["Mode6"]
        if debuglevel != 0:
            self.debug = True
            Domoticz.Debugging(debuglevel)
            DumpConfigToLog()
            self.loglevel = "Verbose"
        else:
            self.debug = False
            Domoticz.Debugging(0)

        # create the child devices if these do not exist yet
        devicecreated = []
        if 1 not in Devices:
            Domoticz.Device(Name="Power supply", Unit=1, TypeName="Switch", Image=9, Used=1).Create()
            devicecreated.append(deviceparam(1, 0, ""))  # default is Off
        if 2 not in Devices:
            Domoticz.Device(Name="Battery Level", Unit=2, Type=243, Subtype=6, Used=1).Create()
            devicecreated.append(deviceparam(2, 0, ""))  # default is 0
        if 3 not in Devices:
            Options = {"LevelActions": "||",
                       "LevelNames": "Off|Auto|Blue On|Green On|Red On|Blue breathe|Green breathe|Red breathe|Blue blink slow|Green blink slow|Red blink slow|Blue blink fast|Green blink fast|Red blink fast",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Domoticz.Device(Name="Gateway LED", Unit=3, TypeName="Selector Switch", Options=Options, Used=1).Create()
            devicecreated.append(deviceparam(3, 1, "10"))  # default is Auto

        #if any device has been created in onStart(), now is time to update its defaults
        for device in devicecreated:
            Devices[device.unit].Update(nValue=device.nvalue, sValue=device.svalue)

        Devices[3].Update(nValue=1, sValue=str(10))

    def onStop(self):

        Domoticz.Debugging(0)


    def onCommand(self, Unit, Command, Level, Color):

        # LED control
        if (Unit == 3):
            Devices[3].Update(nValue=self.LEDpowerOn, sValue=str(Level))
            if (Devices[3].sValue == "0"):  # Off
                self.ResetLED()
                self.LEDpowerOn = 0
                Devices[3].Update(nValue=0, sValue="0")
                self.Modeauto = False
            elif (Devices[3].sValue == "10"):  # Auto
                self.ResetLED()
                self.LEDpowerOn = 1
                Devices[3].Update(nValue=1, sValue="10")
                cmdLED = 'sudo /etc/init.d/ledauto restart'
                os.system(cmdLED)
                self.Modeauto = True
            else : # Manual control
                self.ResetLED()
                self.LEDpowerOn = 1
                time.sleep(2)
                self.Modeauto = False
                if (Devices[3].sValue == "20"):  # Blue On
                    cmdLED = 'sudo dsled b on'
                    os.system(cmdLED)
                    Domoticz.Debug("led b on")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="20")
                elif (Devices[3].sValue == "30"):  # Green On
                    cmdLED = 'sudo dsled g on'
                    os.system(cmdLED)
                    Domoticz.Debug("led g on")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="30")
                elif (Devices[3].sValue == "40"):  # Red On
                    cmdLED = 'sudo dsled r on'
                    os.system(cmdLED)
                    Domoticz.Debug("led r on")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="40")
                elif (Devices[3].sValue == "50"):  # Blue On
                    cmdLED = 'sudo dsled b breathe'
                    os.system(cmdLED)
                    Domoticz.Debug("led b breathe")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="50")
                elif (Devices[3].sValue == "60"):  # Green On
                    cmdLED = 'sudo dsled g breathe'
                    os.system(cmdLED)
                    Domoticz.Debug("led g breathe")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="60")
                elif (Devices[3].sValue == "70"):  # Red On
                    cmdLED = 'sudo dsled r breathe'
                    os.system(cmdLED)
                    Domoticz.Debug("led r breathe")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="70")
                elif (Devices[3].sValue == "80"):  # Blue On
                    cmdLED = 'sudo dsled b blink_slow'
                    os.system(cmdLED)
                    Domoticz.Debug("led b blink_slow")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="80")
                elif (Devices[3].sValue == "90"):  # Green On
                    cmdLED = 'sudo dsled g blink_slow'
                    os.system(cmdLED)
                    Domoticz.Debug("led g blink_slow")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="90")
                elif (Devices[3].sValue == "100"):  # Red On
                    cmdLED = 'sudo dsled r blink_slow'
                    os.system(cmdLED)
                    Domoticz.Debug("led r blink_slow")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="100")
                elif (Devices[3].sValue == "110"):  # Blue On
                    cmdLED = 'sudo dsled b blink_fast'
                    os.system(cmdLED)
                    Domoticz.Debug("led b blink_fast")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="110")
                elif (Devices[3].sValue == "120"):  # Green On
                    cmdLED = 'sudo dsled g blink_fast'
                    os.system(cmdLED)
                    Domoticz.Debug("led g blink_fast")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="120")
                elif (Devices[3].sValue == "130"):  # Red On
                    cmdLED = 'sudo dsled r blink_fast'
                    os.system(cmdLED)
                    Domoticz.Debug("led r blink_fast")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="130")
                else:  # Auto
                    cmdLED = 'sudo dsled b on'
                    os.system(cmdLED)
                    Domoticz.Debug("led auto")
                    Devices[3].Update(nValue=self.LEDpowerOn, sValue="20")



    def onHeartbeat(self):

        Domoticz.Debug("onHeartbeat Called...")
        # fool proof checking....
        if not all(device in Devices for device in (1,2,3)):
            Domoticz.Error("one or more devices required by the plugin is/are missing, please check domoticz device creation settings and restart !")
            return

        now = datetime.now()
        # cat UPS control....
        # Power supply
        self.PowerSupply = False
        #cmdPOWERSUP = 'cat /sys/class/power_supply/bq27546-0/status'
        cmdPOWERSUP = 'cat /sys/class/power_supply/bq27546-0/current_now'
        outputPOWER = sp.getoutput(cmdPOWERSUP)
        os.system(cmdPOWERSUP)
        self.PowerPresent = int(outputPOWER)
        Domoticz.Debug("Ic2 return power supply current : {}".format(self.PowerPresent))
        if self.PowerPresent < 0 :
            Domoticz.Debug("Power supply OFF")
            self.PowerSupply = False
        else :
            Domoticz.Debug("Power supply On")
            self.PowerSupply = True
        if self.PowerSupply :
            if (Devices[1].nValue == 0):
                Devices[1].Update(nValue=1, sValue=Devices[1].sValue)
        else :
            if (Devices[1].nValue == 1):
                Devices[1].Update(nValue=0, sValue=Devices[1].sValue)
        # Battery level
        if self.LastBattUpdate + timedelta(seconds=60) <= now:
            cmdLEVEL = 'cat /sys/class/power_supply/bq27546-0/capacity'
            outputLEVEL = sp.getoutput(cmdLEVEL)
            self.BatteryLevel = int(outputLEVEL)
            os.system(cmdLEVEL)
            Domoticz.Debug("Ic2 return battery level : {}".format(self.BatteryLevel))
            if self.BatteryLevel >= 95 :
                self.BatteryLevel = 100
            Devices[2].Update(nValue=self.BatteryLevel, sValue=str(self.BatteryLevel))
            self.LastBattUpdate = datetime.now()

    def ResetLED(self):
        if self.Modeauto :
            #cmd1 = 'sudo pkill -f /usr/bin/ledautocontrol.sh'
            cmd1 = 'sudo /etc/init.d/ledauto stop'
            os.system(cmd1)
            Domoticz.Debug("dsled daemon stopped")
            time.sleep(1)
        else :
            cmd2= 'sudo pkill dsled && dsled b off && dsled g off && dsled r off'
            os.system(cmd2)
            Domoticz.Debug("dsled off")

    def WriteLog(self, message, level="Normal"):

        if self.loglevel == "Verbose" and level == "Verbose":
            Domoticz.Log(message)
        elif level == "Normal":
            Domoticz.Log(message)

global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Plugin utility functions ---------------------------------------------------

def parseCSV(strCSV):
    listvals = []
    for value in strCSV.split(","):
        try:
            val = int(value)
        except:
            pass
        else:
            listvals.append(val)
    return listvals

def CheckParam(name, value, default):
    try:
        param = int(value)
    except ValueError:
        param = default
        Domoticz.Error("Readed '{}' has an invalid value of '{}' ! defaut of '{}' is instead used.".format(name, value, default))
    return param

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
