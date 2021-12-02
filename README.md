# mpy-ntpclock

Shows a "Left" and "Right" time. You can specify any realistic UTC offset in hours. I don't respect DST, fiddle with your own clocks if you do want it.

This was written for a TTGO with Loboris py from here: https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo

You need to create a config.py with:

```
WIFI_SSID = "yournetworkhere"
WIFI_PASWORD = "yourpasswordhere"

NTP_SERVER = "something here"

LEFT_TITLE = "UTC"
LEFT_UTC_OFFSET_HOURS = 0

RIGHT_TITLE = "USA"
RIGHT_UTC_OFFSET_HOURS = -4
```

You don't have to specify NTP server, it'll revert to `0.pool.ntp.org` if you don't.

# Changelog

2021-12-02 - Updated to rename "local" to "left" and "usa" to "right" and add configurable titles.