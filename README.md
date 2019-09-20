# SonyAVR-polyglotv2
A NodeServer for the Polyglot v2 that interfaces with Sony AVRs (STR-DN1070 and STR-DN1080) locally to allow the ISY 994i to control the power status, source per zone, and volume/mute. May work with other devices supporting the Sony Audio Control API. See https://developer.sony.com/develop/audio-control-api/ for more information.

Instructions for local Polyglot-V2 installation:

1. Install the SonyAVR nodeserver from the Polyglot Nodeserver Store, or do a Git from the repository to the folder ~/.polyglot/nodeservers/SonyAVR in your Polyglot v2 installation.
2. Log into the Polyglot Version 2 Dashboard (https://<Polyglot IP address>:3000)
3. Add the SonyAVR nodeserver as a Local nodeserver type.
4. Add the following optional Custom Configuration Parameters:
```
    "shortPoll" = polling interval for status from receiver(s) - defaults to 20 (longPoll is not used)
```
6. Once the SonyAVR Nodeserver node appears in ISY994i Adminstative Console, click "Discover Devices" to dicover devices on your LAN compatible with the Sony Audio Control API. Make sure the devices are on or in "Network Standby" before you click "Discover Devices."

Here are the currently known anomalies:

1. If a zone doesn't have an associated amp, like HDMI Zone, then "Mute," "Unmute," and "Toggle Mute" commands and setting the volume throw an error which is ignored. The values for these states will not update and do not really reflect a valid state anyway.
2. If you use the "Toggle Mute" command on a zone, it works but it takes the API a little bit to return the new value. So the value shown right after the command will still reflect the old mute status, and you have to wait for the next short poll for mute status to update to the correct value
3. The code will filter any invalid characters from the device name (like [ ] ( ) < > \ / * ! & ? ; " ') before adding the Node to the ISY. You can rename the nodes in the ISY as you like.

For more information regarding this Polyglot Nodeserver, see https://forum.universal-devices.com/topic/????-polyglot-SonyAVR-nodeserver/.