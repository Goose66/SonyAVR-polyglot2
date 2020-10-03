# SonyAVR-polyglotv2
A NodeServer for the Polyglot v2 that interfaces with Sony AVRs (STR-DN1070, STR-DN1080, possibly others) locally to allow the ISY 994i to control the power status, source per zone, and volume/mute. May work with other devices supporting the Sony Audio Control API. See https://developer.sony.com/develop/audio-control-api/ for more information.

Instructions for local Polyglot-V2 installation:

1. Install the SonyAVR nodeserver from the Polyglot Nodeserver Store, or do a Git from the repository to the folder ~/.polyglot/nodeservers/SonyAVR in your Polyglot v2 installation.
2. Log into the Polyglot Version 2 Dashboard (https://<Polyglot IP address>:3000)
3. Add the SonyAVR nodeserver as a Local (Co-Resident with Polyglot) nodeserver type.
4. Add the following optional Custom Configuration Parameters:
```
    "shortPoll" = polling interval for status from receiver(s) - defaults to 20 (longPoll is not used)
```
5. Once the SonyAVR NodeServer node appears in ISY994i Adminstative Console, click "Discover Devices" to dicover devices on your LAN compatible with the Sony Audio Control API. Make sure the devices are on or in "Network Standby" before you click "Discover Devices."

Current Notes:

1. If a zone doesn't have an associated amp, like HDMI Zone, then "Mute," "Unmute," and "Toggle Mute" commands and setting the volume throw an error which is ignored. The values for these states will not update and do not really reflect a valid state anyway.
2. In order for a Sony device to be added in device discovery, it must not only support the Sony Audio Control API, but must support all of the "system," "audio," and "avContent" services of the API.

For more information regarding this Polyglot Nodeserver, see https://forum.universal-devices.com/topic/28462-polyglot-sonyavr-nodeserver/ .