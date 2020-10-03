## SonyAVR NodeServer Configuration
##### Advanced Configuration:
- key: shortPoll, value: polling interval for status from bridge(s) and devices - defaults to 20 seconds (optional)
- key: longPoll - not used

The SonyAVR nodeserver uses SSDP to discover Sony devices on the local network and then queries them for Sony Audio Control API support. Once the SonyAVR NodeServer node appears in ISY994i Adminstative Console, click "Discover Devices" to discover compatible devices on your LAN. Make sure the devices are on or in "Network Standby" before you click "Discover Devices."