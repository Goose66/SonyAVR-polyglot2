#!/usr/bin/env python
"""
Python wrapper class for Sony Audio Control API using JSON-RPC over HTTP
by Goose66 (W. Randy King) kingwrandy@gmail.com
"""

import sys
import logging
import requests
import json
import ssdp
import xml.etree.ElementTree as ET

# Pickup the root logger, and add a handler for module testing if none exists
_LOGGER = logging.getLogger()
if not _LOGGER.hasHandlers():
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)

# Timeout durations for HTTP calls - defined here for easy tweaking
_HTTP_POST_TIMEOUT = 3.05

# API Spec
_SSDP_SEARCH_TARGET = "urn:schemas-sony-com:service:ScalarWebAPI:1"
_API_ENDPOINT = "{baseURL}/{libspec}"
_API_DEVICE_ID = 50
_API_GET_SYSTEM_INFO = {
    "libspec": "system",
    "method": "getSystemInformation",
    "version": "1.4"
}
_API_GET_INTERFACE_INFO = {
    "libspec": "system",
    "method": "getInterfaceInformation",
    "version": "1.0"
}
_API_GET_POWER_STATUS = {
    "libspec": "system",
    "method": "getPowerStatus",
    "version": "1.1"
}
_API_GET_TERMINAL_STATUS = {
    "libspec": "avContent",
    "method": "getCurrentExternalTerminalsStatus",
    "version": "1.0"
}
_API_GET_PLAYING_CONTENT_INFO = {
    "libspec": "avContent",
    "method": "getPlayingContentInfo",
    "version": "1.2"
}
_API_GET_VOLUME_INFO = {
    "libspec": "audio",
    "method": "getVolumeInformation",
    "version": "1.1"
}
_API_SET_POWER_STATUS = {
    "libspec": "system",
    "method": "setPowerStatus",
    "version": "1.1"
}
_API_SET_ACTIVE_TERMINAL = {
    "libspec": "avContent",
    "method": "setActiveTerminal",
    "version": "1.0"
}
_API_SET_PLAY_CONTENT = {
    "libspec": "avContent",
    "method": "setPlayContent",
    "version": "1.2"
}
_API_SET_MUTE = {
    "libspec": "audio",
    "method": "setAudioMute",
    "version": "1.1"
}
_API_SET_VOLUME = {
    "libspec": "audio",
    "method": "setAudioVolume",
    "version": "1.1"
}

# interface class
class deviceAPI(object):

    # Primary constructor method
    def __init__(self, apiURL, apiVer, logger=_LOGGER):

        # Declare instance variables
        self._apiBase = apiURL
        self._apiVer = apiVer
         
        self._logger = logger

    # Call the specified API
    def _call_api(self, api, parms=[]):

        self._logger.debug("in _call_api() for method %s...", api["method"])

        payload = {
            "id": _API_DEVICE_ID,
            "method": api["method"],
            "params": parms,
            "version": api["version"]
        }

        # uncomment the next line(s) to dump POST data to log file for debugging
        self._logger.debug("HTTP POST URL: %s", _API_ENDPOINT.format(baseURL = self._apiBase, libspec = api["libspec"]))
        self._logger.debug("HTTP POST Data: %s", payload)

        try:
            response = requests.post(
                _API_ENDPOINT.format(
                    baseURL = self._apiBase,
                    libspec = api["libspec"]
                ),
                data=json.dumps(payload),
                timeout=_HTTP_POST_TIMEOUT
            )
            response.raise_for_status()    # Raise HTTP errors to be handled in exception handling

        # Allow timeout and connection errors to be ignored - log and return false
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            self._logger.warning("HTTP POST in _call_api() failed: %s", str(e))
            return False
        except:
            self._logger.error("Unexpected error occured: %s", sys.exc_info()[0])
            raise

        # parse response JSON
        respData = response.json()
       
        # uncomment the next line to dump response data to log file for debugging
        self._logger.debug("HTTP POST Response: %s", respData)

        # check for error in response
        if "error" in respData:
            self._logger.warning("API call returned error: %s - %s", respData["error"][0], respData["error"][1])
            return False

        # otherwise return result data
        if respData["result"]:
            return respData["result"][0]
        else:
            return True

    # Gets current power status of receiver
    def getSystemInformation(self):
        """Gets the MAC address of the device."""
        return self._call_api(_API_GET_SYSTEM_INFO)

    # Gets model name of the device
    def getInterfaceInformation(self):
        """Gets model name of the device."""
        return self._call_api(_API_GET_INTERFACE_INFO)

    # Gets current power status of receiver
    def getPowerStatus(self):
        """Gets the current power status of the device."""
        return self._call_api(_API_GET_POWER_STATUS)

    # Gets active status of each zone and input
    def getCurrentExternalTerminalsStatus(self):
        """Gets information about the current status of all external input and output terminal sources of the device."""
        return self._call_api(_API_GET_TERMINAL_STATUS)
        
    # Gets info of content (source) currently playing on zone
    def getPlayingContentInfo(self, output=""):
        """Gets information about the playing content or current selected input.

        Parameters:
        output -- The URI of the output. Use "" to return info for all outputs for the device. 
        """
        return self._call_api(_API_GET_PLAYING_CONTENT_INFO, [{"output":output}])

    # Gets current volume level for zone
    def getVolumeInformation(self, output=""):
        """Gets the current volume level and mute status.

        Parameters:
        output -- The URI of the output. Use "" to return info for all outputs for the device. 
        """
        return self._call_api(_API_GET_VOLUME_INFO, [{"output":output}])

    # Changes the power status of the receiver
    def setPowerStatus(self, status):
        """Sets the power status of the device.

        Parameters:
        status -- The power status to set ("active", "standby", or "off"). Use "" to simulate remote power key press. 
        """
        return self._call_api(_API_SET_POWER_STATUS, [{"status":status}])

    # Sets active status of each zone (and turns on the power)
    def setActiveTerminal(self, output, active):
        """Activates or deactivates an output terminal. Can change the power status of zone output.
        
        Parameters:
        output -- The URI of the output. 
        active -- Indicates whether to activate or deactivate the terminal ("active", "inactive")
        """
        return self._call_api(_API_SET_ACTIVE_TERMINAL, [{"uri":output, "active":active}])
    
    #  Sets the input (source) for a zone
    def setPlayContent(self, output, uri):
        """Changes the source input for a zone.
        
        Parameters:
        output -- The URI of the output. 
        uri -- The URI of the source input to set
        """
        return self._call_api(_API_SET_PLAY_CONTENT, [{"output":output, "uri":uri}])

    # Sets the volume for a zone
    def setAudioVolume (self, output, volume):
        """Sets the audio volume level.
        
        Parameters:
        output -- The URI of the output. Use "" to affect all outputs for the device. 
        volume -- The volume level to set (as a string)
        """
        return self._call_api(_API_SET_VOLUME, [{"output":output, "volume":volume}])

    # Mutes a zone
    def setAudioMute (self, output, mute):
        """Sets the audio mute status.
        
        Parameters:
        output -- The URI of the output. Use "" to affect all outputs for the device.  
        mute -- The mute status to set or adjustment to make ("off", "on", "toggle")
        """
        return self._call_api(_API_SET_MUTE, [{"output":output, "mute":mute}])

# discover devices 
def discover_devices(timeout=5, logger=_LOGGER):
    """Discover devices supporting Sony Audio Control API using SSDP
        
    Parameters:
    timeout -- timeout for SSDP broadcast (defaults to 5)
    logger -- logger to use for errors (defaults to root logger)
    """
    
    devices = []

    # XML namespaces from the Sony STR-DN1070 device descriptor XML file
    # Note: hopefully all Sony devices use the same namespaces
    ns = {
        "upnp": "urn:schemas-upnp-org:device-1-0",
        "av": "urn:schemas-sony-com:av",
        "dlna": "urn:schemas-dlna-org:device-1-0",
        "pnpx": "http://schemas.microsoft.com/windows/pnpx/2005/11",
        "df": "http://schemas.microsoft.com/windows/2008/09/devicefoundation",
        "ms": "urn:schemas-microsoft-com:WMPNSS-1-0"
    } 

    # discover devices via the SSDP M-SEARCH method
    responses = ssdp.discover(_SSDP_SEARCH_TARGET, timeout=timeout)

    logger.debug("SSDP discovery returned %i devices.", len(responses))

    # iterate through the responses 
    for response in responses:

        # Retrieve the XML from the specified URL
        try:
            response = requests.get(response.location)   
    
            # uncomment the next line to dump response XML to log file for debugging
            logger.debug("XML Response from discoverd device: %s", response.text)
            
            # parse the XML from the response
            root = ET.fromstring(response.text)

        # If the device answered SSDP broadcast with the location, a properly formatted
        # XML page should be available at the location, so log and terminate on all errors
        except:
            logger.error("Unexpected error occurred retrieving device info: %s", sys.exc_info()[0])
            raise
        
        # extract the Sony Audio Control API DeviceInfo node from the XML
        apiNode = root.find(".//av:X_ScalarWebAPI_DeviceInfo", ns)

        # if the DeviceInfo node for the Sony Audio Control API was found, make sure
        # the device supports all of the required services
        if apiNode is not None:

            # extract the supported services from the DeviceInfo nodes
            services = []
            for serviceType in apiNode.find("av:X_ScalarWebAPI_ServiceList", ns).findall("av:X_ScalarWebAPI_ServiceType", ns):
                services.append(serviceType.text)

            # check for system, audio, and avContent service support
            if all(s in services for s in ("system", "audio", "avContent")):
            
                # extract the elements we need from the XML string
                id = root.find(".//upnp:UDN", ns).text[-6:] # the last 6 digits of the "node" from the uuid (hex)
                name = root.find(".//upnp:friendlyName", ns).text
                model = root.find(".//upnp:modelName", ns).text
                apiVer = apiNode.find("av:X_ScalarWebAPI_Version", ns).text
                apiURL = apiNode.find("av:X_ScalarWebAPI_BaseURL", ns).text
        
                logger.debug("Sony Audio Control API device found in discover - ID: %s, Name: %s, Model: %s", id, name, model)

                # append to device list
                devices.append({"id": id, "name": name, "model": model, "apiVer": apiVer, "apiURL": apiURL})

    return devices

    
