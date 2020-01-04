#!/usr/bin/env python
"""
Polyglot v2 NodeServer for Sony Audio Control API devices (e.g. STR-DN1070 and STR-DN1080) 
by Goose66 (W. Randy King) kingwrandy@gmail.com
"""
import sys
import re
import sonyapi
import polyinterface

_ISY_PERCENT_UOM = 51 # Percentage from 0 to 100
_ISY_INDEX_UOM = 25 # Index UOM for custom states (must match editor/NLS values in profile)
_ISY_BOOL_UOM = 2 # Used for reporting status values for Controller node

# A list of source input URIs in order of the corresponding Source (GV0) driver values
_SOURCE_URIS = [
    "extInput:source",      # IX_ZON_SRC-0 = Main
    "extInput:bd-dvd",      # IX_ZON_SRC-1 = BD-DVD
    "extInput:btAudio",     # IX_ZON_SRC-2 = Bluetooth
    "extInput:game",        # IX_ZON_SRC-3 = Game
    "extInput:hdmi",        # IX_ZON_SRC-4 = Front Panel HDMI
    "extInput:line",        # IX_ZON_SRC-5 = Audio Line Input
    "extInput:sacd-cd",     # IX_ZON_SRC-6 = SACD-CD
    "extInput:sat-catv",    # IX_ZON_SRC-7 = SAT-CATV
    "extInput:tv",          # IX_ZON_SRC-8 = TV
    "extInput:video",       # IX_ZON_SRC-9 = Video
    "dlna:music",           # IX_ZON_SRC-10 = DLNA
    "storage:usb1",         # IX_ZON_SRC-11 = USB
    "radio:fm"              # IX_ZON_SRC-12 = Radio
]

_IX_AVR_ST_OFF = 0 
_IX_AVR_ST_STANDBY = 1
_IX_AVR_ST_ON = 2

_IX_ZON_ST_ACTIVE = 1
_IX_ZON_ST_INACTIVE = 0

_LOGGER = polyinterface.LOGGER

# Node for an audio zone (Main, Zone 2, Zone 3, HDMI Zone, etc.)
class Zone(polyinterface.Node):

    id = "ZONE"
    hint = [0x01, 0x06, 0x01, 0x00] # Residential/Audio Visual/AV Control Point
    _zoneURI = ""
    minVol = 0
    maxVol = 100

    def __init__(self, controller, primary, addr, name, uri=None):
        super(Zone, self).__init__(controller, primary, addr, name)
    
        # override the parent node with the receiver (defaults to controller)
        self.parent = self.controller.nodes[self.primary]

        if uri is None:

            # retrieve uri from polyglot custom data
            self._zoneURI = controller.getCustomData(addr)

        else:
            self._zoneURI = uri

            # store instance variables in polyglot custom data
            controller.addCustomData(addr, self._zoneURI)

    # Activate zone (turn on)
    def cmd_don(self, command):

        # Place the zone in active status
        if  self.parent.interface.setActiveTerminal(self._zoneURI, "active"):
            self.setDriver("ST", _IX_ZON_ST_ACTIVE, True)
        else:
            _LOGGER.warning("Call to setActiveTerminal() failed in DON command handler.")

    # Deactivate zone (turn off)
    def cmd_dof(self, command):

        # Place the zone in inactive status
        if self.parent.interface.setActiveTerminal(self._zoneURI, "inactive"):
            self.setDriver("ST", _IX_ZON_ST_INACTIVE, True)
        else:
            _LOGGER.warning("Call to setActiveTerminal() failed in DOF command handler.")

    # Change source for zone
    def cmd_set_source(self, command):

        # retrieve the integer index for the command
        value = int(command.get("value"))

        # Set the source for zone
        if self.parent.interface.setPlayContent(self._zoneURI, _SOURCE_URIS[value]):
            self.setDriver("GV0", value, True)
        else:
            _LOGGER.warning("Call to setPlayContent() failed in SET_SRC command handler.")

    # Change volume for zone
    def cmd_set_volume(self, command):

        # retrieve the integer value (%) for the command
        value = int(command.get("value"))

        # compute the volume value as a percentage of volume range
        vol = int((value / 100 * (self.maxVol - self.minVol)) + self.minVol)

        # Set the volume for zone
        if self.parent.interface.setAudioVolume(self._zoneURI, str(vol)):
            self.setDriver("SVOL", value, True)
        else:
            _LOGGER.warning("Call to setAudioVolume() failed in SET_VOL command handler.")

    # Mute zone audio
    def cmd_mute(self, command):

        # Mute the zone
        if self.parent.interface.setAudioMute(self._zoneURI, "on"):
            self.setDriver("GV1", int(True), True)
        else:
            _LOGGER.warning("Call to setAudioMute() failed in MUTE command handler.")

    # Unmute zone audio
    def cmd_unmute(self, command):

        # Unmute the zone
        if self.parent.interface.setAudioMute(self._zoneURI, "off"):
            self.setDriver("GV1", int(False), True)
        else:
            _LOGGER.warning("Call to setAudioMute() failed in UNMUTE command handler.")

    # Toggle mute for zone
    def cmd_toggle_mute(self, command):

        # Toggle mute status for the zone
        if self.parent.interface.setAudioMute(self._zoneURI, "toggle"):
            
            # Update the mute status for the zone - this is not working.
            # Receiver reports previous value. Maybe delay needed.
            # Gets picked up in next shortPoll
            volInfo = self.parent.interface.getVolumeInformation(self._zoneURI)
            if volInfo:
                self.setDriver("GV1", int(volInfo[0]["mute"] == "on"), True)
        else:
            _LOGGER.warning("Call to setAudioMute() failed in TOGGLE_MUTE command handler.")

    drivers = [
        {"driver": "ST", "value": _IX_ZON_ST_INACTIVE, "uom": _ISY_INDEX_UOM},
        {"driver": "GV0", "value": 0, "uom": _ISY_INDEX_UOM},
        {"driver": "SVOL", "value": 0, "uom": _ISY_PERCENT_UOM},
        {"driver": "GV1", "value": 0, "uom": _ISY_BOOL_UOM}
    ]
    commands = {
        "DON": cmd_don,
        "DOF": cmd_dof,
        "SET_SRC": cmd_set_source,
        "SET_VOL": cmd_set_volume,
        "MUTE": cmd_mute,
        "UNMUTE": cmd_unmute,
        "TOGGLE_MUTE": cmd_toggle_mute,
    }

    # static method to format address for Zone nodes
    @staticmethod
    def formatAddr(receiverID, uri):
        return  receiverID + "_" + uri[uri.find("zone?")+5:].replace("=", "_")

# Node for audio device (AVR)
class Receiver(polyinterface.Node):

    id = "RECEIVER"
    hint = [0x01, 0x06, 0x01, 0x00] # Residential/Audio Visual/AV Control Point
    interface = None
    _apiURL = ""
    _apiVer = ""

    def __init__(self, controller, primary, addr, name, apiURL=None, apiVer=None):
        super(Receiver, self).__init__(controller, addr, addr, name) # send its own address as primary

        # make the receiver a primary node
        self.isPrimary = True

        if apiURL is None:
    
            # retrieve instance variables from polyglot custom data
            cData = controller.getCustomData(addr).split(";")
            self._apiURL = cData[0]
            self._apiVer = cData[1]

        else:
            self._apiURL = apiURL
            self._apiVer = apiVer

            # store instance variables in polyglot custom data
            cData = ";".join([self._apiURL, self._apiVer])
            controller.addCustomData(addr, cData)
        
        # create an instance of the API object for the device at the specified based address
        self.interface = sonyapi.deviceAPI(self._apiURL, self._apiVer, _LOGGER)          

    # Mute all zones
    def cmd_mute_all(self, command):

        # Mute all outputs
        if self.interface.setAudioMute("", "on"):
            self.update_node_states()
        else:
            _LOGGER.warning("Call to setAudioMute() failed in MUTE command handler.")

    # Unmute all zones
    def cmd_unmute_all(self, command):

        # Unmute all outputs
        if self.interface.setAudioMute("", "off"):
            self.update_node_states()
        else:
            _LOGGER.warning("Call to setAudioMute() failed in UNMUTE command handler.")

    # Update node states for this and child nodes
    def cmd_query(self, command):

        _LOGGER.debug("Updating node states in cmd_query()...")

        # Update the node states and force report of all driver values
        self.update_node_states(True)

     # update the state of all zones from the AVR
    def update_node_states(self, forceReport=False):
        
        # retrieve the power status of the AVR from the API
        powerInfo = self.interface.getPowerStatus()
        
        # If False returned, then timeout occurred (or some other error). Set the state to off/unknown
        # No need to continue if device is not responding
        if not powerInfo:
            self.setDriver("ST", _IX_AVR_ST_OFF, True, forceReport)
        
        else:

            # Set GV0 driver value based on return returned state
            state = powerInfo["status"] 

            if state == "active" or state == "activating":
                self.setDriver("ST", _IX_AVR_ST_ON, True, forceReport)
            elif state == "standby":
                self.setDriver("ST", _IX_AVR_ST_STANDBY, True, forceReport)
            else:
                self.setDriver("ST", _IX_AVR_ST_OFF, True, forceReport)
        
            # get the terminal (zone) list for the device from the API
            terminals = self.interface.getCurrentExternalTerminalsStatus()

            # get the volume info and source info for all outputs
            volumeInfo = self.interface.getVolumeInformation()
            sourceInfo = self.interface.getPlayingContentInfo()

            # check that data was retrieved for all calls
            if terminals and volumeInfo and sourceInfo:

                # iterate through the terminals that are zones and
                # update the corresponding zone node
                for terminal in terminals:
                    if terminal["meta"] == "meta:zone:output":

                        uri = terminal["uri"]
                        addr = Zone.formatAddr(self.address, uri)

                        # make sure a zone node exists for the terminal (may have been deleted by user)
                        if addr in self.controller.nodes:

                            # retrieve the zone node for the terminal
                            zone = self.controller.nodes[addr]

                            # retrieve the volume and source information for the terminal
                            source = next(item for item in sourceInfo if item["output"] == uri)
                            volume  = next(item for item in volumeInfo if item["output"] == uri)

                            # parse the state info and set the driver volumes
                            zone.setDriver("ST", (_IX_ZON_ST_ACTIVE if terminal["active"] == "active" else _IX_ZON_ST_INACTIVE), True, forceReport)
                            zone.setDriver("GV0", _SOURCE_URIS.index(source["uri"]), True, forceReport)
                            zone.minVol = volume["minVolume"]
                            zone.maxVol = volume["maxVolume"]
                            vol = volume["volume"]
                            zone.setDriver("SVOL", int((vol - zone.minVol) / (zone.maxVol - zone.minVol) * 100), True, forceReport)
                            zone.setDriver("GV1", int(volume["mute"] == "on"), True, forceReport)

    drivers = [
        {"driver": "ST", "value": 0, "uom": _ISY_INDEX_UOM}
    ]
    commands = {
        "MUTE_ALL": cmd_mute_all,
        "UNMUTE_ALL": cmd_unmute_all,
        "QUERY_ALL": cmd_query
    }

# Controller class (nodeserver only)
class Controller(polyinterface.Controller):

    id = "CONTROLLER"
    _customData = {}

    def __init__(self, poly):
        super(Controller, self).__init__(poly)
        self.name = "SonyAVR NodeServer"
 
    # Start the nodeserver
    def start(self):

        _LOGGER.info("Started SonyAVR NodeServer...")

        # remove all existing notices for the nodeserver
        self.removeNoticesAll()

        # load custom data from polyglot
        self._customData = self.polyConfig["customData"]

        # load nodes previously saved to the polyglot database
        for addr in self._nodes:
            
            # ignore controller node
            if addr != self.address:
                
                node = self._nodes[addr]
                _LOGGER.debug("Adding previously saved node - addr: %s, name: %s, type: %s", addr, node["name"], node["node_def_id"])
        
                # add receiver nodes
                if node["node_def_id"] == "RECEIVER":
                    self.addNode(Receiver(self, addr, addr, node["name"]))

                # add zone nodes
                elif node["node_def_id"] == "ZONE":
                    self.addNode(Zone(self, node["primary"], addr, node["name"]))

        # Update the nodeserver status flag
        self.setDriver("ST", 1, True, True)
                
        # Update the node states for all receivr nodes and force report of all driver values
        for addr in self.nodes:
            node = self.nodes[addr]
            if node.id == "RECEIVER":
                node.update_node_states(True)

    # Run discovery for Sony devices
    def cmd_discover(self, command):

        _LOGGER.debug("Discovering devices in cmd_discover()...")
        
        self.discover()

    # Update the profile on the ISY
    def cmd_update_profile(self, command):

        _LOGGER.debug("Installing profile in cmd_update_profile()...")
        
        self.poly.installprofile()
        
    # called every longPoll seconds (default 60)
    def longPoll(self):

        pass

    # called every shortPoll seconds (default 20)
    def shortPoll(self):

        # iterate through the receiver nodes and update the node states
        for addr in self.nodes:

            node = self.nodes[addr]
            if node.id == "RECEIVER":
                node.update_node_states(False)

    # helper method for storing custom data
    def addCustomData(self, key, data):

        # add specififed data to custom data for specified key
        self._customData.update({key: data})

    # helper method for retrieve custom data
    def getCustomData(self, key):

        # return data from custom data for key
        return self._customData[key]

    # discover audio devices and build nodes
    def discover(self):
 
        # Search for devices using SSDP
        devices = sonyapi.discover_devices(logger=_LOGGER)

        # if no devices were found, add a notice to Polyglot
        if not devices:
            self.addNotice("No Sony Audio devices found. Make sure devices to be discovered are On or in Network Standby.", "no_devices_notice")

        else:
            self.removeNotice("no_devices_notice")
 
            # iterate the return devices
            for dev in devices:

                _LOGGER.debug("Discovered device - addr: %s, name: %s", dev["id"], dev["name"])

                # check whether a node for the device already exists
                if dev["id"] not in self.nodes:

                    # add a device (Receiver) node for the device
                    receiver = Receiver(
                        self,
                        self.address,
                        dev["id"],
                        getValidNodeName(dev["name"]),
                        dev["apiURL"],
                        dev["apiVer"]
                    )
                    self.addNode(receiver)

                else:
                    receiver = self.nodes[dev["id"]]

                # use the interface for the receiver node to get a list of "terminals" (zones)
                terminals = receiver.interface.getCurrentExternalTerminalsStatus()
    
                if not terminals:
                    _LOGGER.error("getCurrentExternalTerminalsStatus() for %s returned no data.", dev["name"])

                else:

                    # iterate terminals and create zone nodes
                    for terminal in terminals:

                        if terminal["meta"] == "meta:zone:output":

                            uri = terminal["uri"]
                            addr = Zone.formatAddr(dev["id"], uri)
                            name = terminal["title"]
                            # active = terminal["active"]

                            _LOGGER.debug("Discovered zone - addr: %s, name: %s", addr, name)

                            # If no node already exists for the zone, then add a node for this zone
                            if addr not in self.nodes:
                            
                                zone = Zone(
                                    self,
                                    receiver.address,
                                    addr,
                                    getValidNodeName(dev["model"] + " - " + name),
                                    uri
                                )
                                self.addNode(zone)

                    receiver.update_node_states(True)

            # send custom data added by nodes to polyglot
            self.saveCustomData(self._customData)

    drivers = [
        {"driver": "ST", "value": 0, "uom": _ISY_BOOL_UOM}
    ]
    commands = {
        "DISCOVER": cmd_discover,
        "UPDATE_PROFILE" : cmd_update_profile
    }

# Removes invalid charaters and lowercase ISY Node address
def getValidNodeAddress(s):

    # remove <>`~!@#$%^&*(){}[]?/\;:"' characters
    addr = re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", s)

    # return lowercase address
    return addr[:14].lower()

# Removes invalid charaters for ISY Node description
def getValidNodeName(s):

    # remove <>`~!@#$%^&*(){}[]?/\;:"' characters from names
    return re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", s)

# Main function to establish Polyglot connection
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface()
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        _LOGGER.warning("Received interrupt or exit...")
        polyglot.stop()
    except Exception as err:
        _LOGGER.error('Excption: {0}'.format(err), exc_info=True)
        sys.exit(0)
