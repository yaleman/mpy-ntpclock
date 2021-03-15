#!/usr/bin/env python3

"""
https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/blob/fff2e193d064effe36a7d456050faa78fe6280a8/MicroPython_BUILD/components/micropython/docs/library/utime.rst

"""

import socket
import struct
import utime
import machine
import network
import display

# Time zone file
#
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/blob/fff2e193d064effe36a7d456050faa78fe6280a8/MicroPython_BUILD/components/micropython/docs/zones.csv

from config import WIFI_SSID, WIFI_PASSWORD, UTC_OFFSET_HOURS_LOCAL, UTC_OFFSET_HOURS_USA
try:
    from config import NTP_HOST
except ImportError:
    NTP_HOST = "0.pool.ntp.org"
print("Using NTP server {}".format(NTP_HOST))


TIME_FONT_THICKNESS = 2

RTC_TZ = "GMT+0"
# NTP_DELTA = 3155673600
# UTIME_DELTA = 946684800

def zfl(s, width):
    # Pads the provided string with leading 0's to suit the specified 'chrs' length
    # Force # characters, fill with leading 0's
    return '{:0>{w}}'.format(s, w=width)

def time_string(rtc_object, offset_hours):
    offset_secs = offset_hours * 3600
    rtc_secs = int(utime.mktime(rtc_object.now()))
    #print(rtc_secs)
    timedata = utime.localtime(rtc_secs+offset_secs)
    #print(timedata)

    hour = str(timedata[3])
    minute = zfl(timedata[4],2)

    return "{}:{}".format(hour, minute)
    #return "{0:02d}:{0:02d}".format(hour, minute)

def do_connect(rtc_object):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected():
            utime.sleep(0.1)
    print('network config:', sta_if.ifconfig())
    print("Doing time")
    rtc_object.ntp_sync(server=NTP_HOST, tz=RTC_TZ)
    while not rtc_object.synced():
        print("NTP Not Synchronised")
        utime.sleep(1)
    print("Time synced, is currently {}".format(time_string(rtc_object, UTC_OFFSET_HOURS_LOCAL)))

def get_text_x(x, text):
    return int(x + (BLOCK_WIDTH/2)) - int(tft.textWidth(text)/2)

def do_block(x, y, title, time_text, prev_time_text):
    """ x/y are the coordinates of the top left of the block
        title is printed at 1/3
        time_text is printed at 2/3
    """
    tft.font(TITLE_FONT, color=WHITE)
    title_x = int(x + (BLOCK_WIDTH/2)) - int(tft.textWidth(title)/2)
    title_y = int(y + (BLOCK_HEIGHT/3))-int(tft.fontSize()[1]/2)
    tft.text(int(title_x),
             int(title_y),
             title,
             TITLE_COLOUR,
             )

    tft.font(TIME_FONT,
             width=TIME_FONT_THICKNESS, # thickness of the bars
             color=WHITE,
            )

    time_y = int(y + BLOCK_HEIGHT*(2/3))-int(tft.fontSize()[1]/2)
    tft.textClear(get_text_x(x, prev_time_text), time_y, prev_time_text)
    time_x = get_text_x(x, time_text)
    tft.text(time_x, time_y, time_text, TITLE_COLOUR)
    tft.rect(int(x),
             int(y),
             BLOCK_WIDTH,
             BLOCK_HEIGHT,
             WHITE
             )
    # print(x, y)

rtc = machine.RTC()
do_connect(rtc)

tft = display.TFT()
BLACK = 0xFFFFFF - tft.BLACK
WHITE = 0xFFFFFF - tft.WHITE
SCREEN_ROTATION = tft.LANDSCAPE

SCREEN_X = 240
SCREEN_Y = 135

if SCREEN_ROTATION == tft.PORTRAIT:
    SCREEN_WIDTH = SCREEN_Y
    SCREEN_HEIGHT = SCREEN_X

    BLOCK_WIDTH = int(SCREEN_WIDTH)
    BLOCK_HEIGHT = int(SCREEN_HEIGHT / 2)
elif SCREEN_ROTATION == tft.LANDSCAPE:
    SCREEN_WIDTH = SCREEN_X
    SCREEN_HEIGHT = SCREEN_Y

    BLOCK_WIDTH = int(SCREEN_WIDTH / 2)
    BLOCK_HEIGHT = int(SCREEN_HEIGHT)


tft.init(tft.ST7789,bgr=False,
         rot=SCREEN_ROTATION,
         miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18,
         cs=5, dc=16,
         )
tft.setwin(40,52,320,240)
tft.set_bg(BLACK)


tft.set_fg(WHITE)
tft.clear()

TITLE_FONT = tft.FONT_DejaVu18
TIME_FONT = tft.FONT_7seg

TITLE_COLOUR = WHITE
TIME_COLOUR = WHITE

time_usa = ""
time_local = ""
tft.clear()
check_timer = 0
prev_local = ""
prev_usa = ""
while True:
    time_local = time_string(rtc, UTC_OFFSET_HOURS_LOCAL)
    time_usa = time_string(rtc, UTC_OFFSET_HOURS_USA)

    if prev_local != time_local or prev_usa != time_usa:

        if SCREEN_ROTATION == tft.PORTRAIT:
            x1 = y1 = x2 = 0
            y2 = int(SCREEN_HEIGHT/2)
        else:
            x1 = y1 = y2 = 0
            x2 = int(SCREEN_WIDTH/2)

        do_block(x1, y1, "Local", time_local, prev_local)
        do_block(x2, y2, "USA", time_usa, prev_usa)
        prev_local = time_local
        prev_usa = time_usa
    utime.sleep(2)
    check_timer += 1
    if check_timer > 300:
        print("Synchronizing with NTP")
        rtc.ntp_sync(server=NTP_HOST, tz=RTC_TZ)
        check_timer = 0
        tft.clear()

