#!/usr/bin/env python3

"""
https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/blob/fff2e193d064effe36a7d456050faa78fe6280a8/MicroPython_BUILD/components/micropython/docs/library/utime.rst

"""

# import socket
# import struct
import sys

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


DAY_ARRAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri","Sat", ]

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
    timedata = utime.localtime(rtc_secs+offset_secs)

    hour = str(timedata[3])
    minute = zfl(timedata[4],2)
    #print("hour: {}".format(hour))
    #print("minute: {}".format(minute))
    retstr = "{}:{}".format(hour, minute)
    print("time_string({})".format(retstr))
    return retstr

def date_string(rtc_object, offset_hours):
    offset_secs = offset_hours * 3600
    rtc_secs = int(utime.mktime(rtc_object.now()))
    timedata = utime.localtime(rtc_secs+offset_secs)

    dow = DAY_ARRAY[timedata[6]-1]
    dom = zfl(timedata[2],2)
    return "{} {}".format(dow, dom)


def do_connect(rtc_object):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected():
            utime.sleep(0.1)
    ip_address, ip_netmask, gateway, dns_server = sta_if.ifconfig()
    print('network config: address={} netmask={} gateway={} dns_server={}'.format(
        ip_address, ip_netmask, gateway, dns_server
    ))
    del ip_address, ip_netmask, gateway, dns_server

    print("Starting NTP sync with {}".format(NTP_HOST))
    rtc_object.ntp_sync(server=NTP_HOST, tz=RTC_TZ)
    while not rtc_object.synced():
        print("NTP Not Synchronised, attempting to contact {}".format(NTP_HOST))
        utime.sleep(1)
    print("Time synced, is currently {}".format(time_string(rtc_object, UTC_OFFSET_HOURS_LOCAL)))

def get_text_x(x, text):
    return int(x + (BLOCK_WIDTH/2)) - int(tft.textWidth(text)/2)

def display_error(error_text: str):
    """ blanks the screen and shows an error """

    if isinstance(error_text, TypeError):
        error_text = (" ".join(error_text.args))
    try:
        tft.set_bg(BLACK)
        tft.set_fg(RED)
        tft.clear()
        tft.font(tft.FONT_DefaultSmall, color=RED)
        # try and split long messages up
        txtlen = 30
        print(error_text)
        for i in range(len(error_text)/txtlen):
            output_text = error_text[i*txtlen:(i*txtlen)+txtlen]
            tft.text(0,i*10, output_text, color=RED)
    except Exception as error_message:
        print("")
        print("")
        print("Well you seriously broke it this time.")
        print("While trying to display an error message")
        print("on the LCD, you managed to make THAT")
        print("fail too?")
        print("New error message:")

        if isinstance(error_message, TypeError):
            error_message = (" ".join(error_message.args))
        print(error_message)
        print("Original error:")
        print(str(error_text))


def do_block(tft, x, y, title, date_text, time_text, prev_time_text, prev_date_text):
    """ x/y are the coordinates of the top left of the block
        title is printed at 1/3
        time_text is printed at 1/2
        date_text is printed somewhere below that
    """

    tft.rect(int(x),
             int(y),
             BLOCK_WIDTH,
             BLOCK_HEIGHT,
             WHITE
             )
    tft.font(TITLE_FONT, color=WHITE)
    block_height_divided = int(BLOCK_HEIGHT/5)

    # display the location
    title_x = int(x + (BLOCK_WIDTH/2)) - int(tft.textWidth(title)/2)
    title_y = int(y + block_height_divided)-int(tft.fontSize()[1]/2)
    tft.text(int(title_x),
             int(title_y),
             title,
             TITLE_COLOUR,
             )

    # # display the date
    date_str_x = int(x + (BLOCK_WIDTH/2)) - int(tft.textWidth(date_text)/2)
    date_str_y = int(y + block_height_divided*4)-int(tft.fontSize()[1]/2)
    # # clear the date
    # tft.textClear(get_text_x(date_str_x, prev_date_text), date_str_y, prev_date_text)
    # # print the date
    tft.text(int(date_str_x),
             int(date_str_y),
             date_text,
             WHITE,
             )


    # display the time
    tft.font(TIME_FONT,
             width=TIME_FONT_THICKNESS, # thickness of the bars
             color=WHITE,
            )

    time_y = int(BLOCK_HEIGHT/2)-int(tft.fontSize()[1]/2)
    # clear the old text
    tft.text(get_text_x(x, prev_time_text),
             time_y,
             prev_time_text,
             BLACK,
             )

    #tft.textClear(get_text_x(x, prev_time_text),
    #              time_y,
    #              prev_time_text)
    time_x = get_text_x(x, time_text)
    tft.text(time_x,
             time_y,
             time_text,
             TITLE_COLOUR,
             )

try:
    rtc = machine.RTC()
    do_connect(rtc)

    tft = display.TFT()
    RED = 0xFFFFFF - tft.RED
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
    check_timer = 0
    prev_local = ""
    prev_usa = ""
    prev_date_local = ""
    prev_date_usa = ""

    while True:
        time_local = time_string(rtc, UTC_OFFSET_HOURS_LOCAL)
        time_usa = time_string(rtc, UTC_OFFSET_HOURS_USA)

        date_local = date_string(rtc, UTC_OFFSET_HOURS_LOCAL)
        date_usa = date_string(rtc, UTC_OFFSET_HOURS_USA)

        if (prev_local != time_local) or (prev_usa != time_usa):

            if SCREEN_ROTATION == tft.PORTRAIT:
                x1 = y1 = x2 = 0
                y2 = int(SCREEN_HEIGHT/2)
            else:
                x1 = y1 = y2 = 0
                x2 = int(SCREEN_WIDTH/2)
            #x, y, title, date_text, time_text, prev_time_text, prev_date_text
            do_block(tft, x1, y1, title="Local", time_text=time_local, prev_time_text=prev_local,
                    date_text=date_local,
                    prev_date_text=prev_date_local,
                    )
            do_block(tft, x2, y2, title="USA", time_text=time_usa, prev_time_text=prev_usa,
                    date_text=date_usa,
                    prev_date_text=prev_date_usa,
                    )
            prev_local = time_local
            prev_usa = time_usa


            prev_date_local = date_local
            prev_date_usa = date_usa

        utime.sleep(2)
        check_timer += 1
        if check_timer > 300:
            print("Synchronizing with NTP")
            rtc.ntp_sync(server=NTP_HOST, tz=RTC_TZ)
            check_timer = 0
except Exception as error_message:
    display_error(error_message)
    sys.exit()
