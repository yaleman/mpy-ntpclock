# mpy-ntpclock

Shows a "Local" and "Remote" time. You can specify any realistic UTC offset in hours. I don't respect DST, fiddle with your own clocks if you do want it.

This was written for a TTGO with Loboris py from here: https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo

You need to create a config.py with:

```
WIFI_SSID = "yournetworkhere"
WIFI_PASWORD = "yourpasswordhere"

NTP_SERVER = "something here"

UTC_OFFSET_HOURS_LOCAL = 10
UTC_OFFSET_HOURS_REMOTE = -5
```

You don't have to specify NTP server, it'll revert to `0.pool.ntp.org` if you don't.
