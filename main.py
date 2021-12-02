#!/usr/bin/env python3

"""
https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/blob/fff2e193d064effe36a7d456050faa78fe6280a8/MicroPython_BUILD/components/micropython/docs/library/utime.rst

"""

# import socket
# import struct
# import builtins
import json
import sys

#pylint: disable=import-error
import utime
#pylint: disable=import-error
import machine
#pylint: disable=import-error
import network
#pylint: disable=import-error
import display

# Time zone file
#
# https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/blob/fff2e193d064effe36a7d456050faa78fe6280a8/MicroPython_BUILD/components/micropython/docs/zones.csv

# pylint: disable=line-too-long
from config import WIFI_SSID, WIFI_PASSWORD, LEFT_TITLE, LEFT_UTC_OFFSET_HOURS, RIGHT_TITLE, RIGHT_UTC_OFFSET_HOURS
try:
    from config import NTP_HOST
except ImportError:
    NTP_HOST = "0.pool.ntp.org"
print("Using NTP server {}".format(NTP_HOST))


DAY_ARRAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri","Sat", ]
DEBUG = False
TIME_FONT_THICKNESS = 2

RTC_TZ = "GMT+0"
# NTP_DELTA = 3155673600
# UTIME_DELTA = 946684800


SCREEN_X = 240
SCREEN_Y = 135

def zfl(s, width):
    """ Pads the provided string with leading 0's to suit the specified 'chrs' length
    # Force # characters, fill with leading 0's """
    return '{:0>{w}}'.format(s, w=width)

def time_string(rtc_object, offset_hours: int):
    """ generates a string of the time given an offset in hours """
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
    """ generates a string of the date given an offset in hours """
    offset_secs = offset_hours * 3600
    rtc_secs = int(utime.mktime(rtc_object.now()))
    timedata = utime.localtime(rtc_secs+offset_secs)

    dow = DAY_ARRAY[timedata[6]-1]
    dom = zfl(timedata[2],2)
    return "{} {}".format(dow, dom)


def do_connect(rtc_object):
    """ does the wifi connection thing """
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
    print("Time synced, is currently {} in {}".format(
        time_string(rtc_object, LEFT_UTC_OFFSET_HOURS),
        LEFT_TITLE,
        )
    )

def get_text_x(x, text, config):
    """ returns the x coord of the text """
    return int(x + (config.get('block_width')/2)) - int(config.get('tft').textWidth(text)/2)

def display_error(error_text: str, config: dict):
    """ blanks the screen and shows an error """

    if isinstance(error_text, TypeError):
        error_text = (" ".join(error_text.args))
    try:
        tft = config.get('tft')
        if tft:
            tft.set_bg(config.get('colours').get('black'))
            tft.set_fg(config.get('colours').get('red'))
            tft.clear()
            tft.font(tft.FONT_DefaultSmall, color=config.get('colours').get('red'))
        # try and split long messages up
        txtlen = 30
        print(error_text)
        for i in range(len(error_text)/txtlen):
            output_text = error_text[i*txtlen:(i*txtlen)+txtlen]
            tft.text(0,i*10, output_text, color=config.get('colours').get('red'))

    # pylint: disable=broad-except
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


# pylint: disable=too-many-arguments
def do_block(config, x, y, title, date_text, time_text, prev_time_text):
    """ x/y are the coordinates of the top left of the block
        title is printed at 1/3
        time_text is printed at 1/2
        date_text is printed somewhere below that
    """
    tft = config.get('tft')

    tft.rect(int(x),
             int(y),
             config.get('block_width'),
             config.get('block_height'),
             config.get('colours').get('white')
             )
    tft.font(config.get('title_font'), color=config.get('colours').get('white'))
    block_height_divided = int(config.get('block_height')/5)

    # display the location
    title_x = int(x + (config.get('block_width')/2)) - int(tft.textWidth(title)/2)
    title_y = int(y + block_height_divided)-int(tft.fontSize()[1]/2)
    tft.text(int(title_x),
             int(title_y),
             title,
             config.get('title_colour'),
             )

    # # display the date
    date_str_x = int(x + (config.get('block_width')/2)) - int(tft.textWidth(date_text)/2)
    date_str_y = int(y + block_height_divided*4)-int(tft.fontSize()[1]/2)
    # # clear the date
    tft.text(int(date_str_x),
             int(date_str_y),
             date_text,
             config.get('colours').get('white'),
             )

    if DEBUG:
        print("setting time font")

    # display the time
    tft.font(config.get('time_font'),
             width=TIME_FONT_THICKNESS, # thickness of the bars
             color=config.get('colours').get('white'),
            )
    if DEBUG:
        print("getting time y")

    time_y = int(config.get('block_height')/2)-int(tft.fontSize()[1]/2)
    # clear the old text
    if DEBUG:
        print("clearing old text")
    config.get('tft').text(get_text_x(x, prev_time_text, config),
                           time_y,
                           prev_time_text,
             config.get('colours').get('black'),
             )

    if DEBUG:
        print("getting text x")
    time_x = get_text_x(x, time_text, config)

    if DEBUG:
        print("Displaying time")
    config.get('tft').text(time_x,
             time_y,
             time_text,
             config.get('title_colour'),
             )

def build_init_config(tft) -> dict:
    """ builds an initial config dict """
    config = {
        'tft' : tft,
        'colours' : {
            'black' : (0xFFFFFF - tft.BLACK),
            'red' : 0xFFFFFF - tft.RED,
            'white' : 0xFFFFFF - tft.WHITE
        },

        'title_font' : tft.FONT_DejaVu18,
        'time_font' : tft.FONT_7seg,
    }

    config['title_colour'] = config.get('colours').get('white')
    config['time_colour'] = config.get('colours').get('white')
    return config

def check_sync_ntp(checktimer, rtcobject):
    """ synchronises NTP """
    checktimer += 1
    if checktimer > 300:
        print("Synchronizing with NTP")
        rtcobject.ntp_sync(NTP_HOST, tz=RTC_TZ)
        checktimer = 0
    return checktimer

def init_tft(tft, config):
    """ does the setup things for the screen """
    tft.init(tft.ST7789,bgr=False,
            rot=config["SCREEN_ROTATION"],
            miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18,
            cs=5, dc=16,
            )
    tft.setwin(40,52,320,240)
    tft.set_bg(config.get('colours').get('black'))
    tft.set_fg(config.get('colours').get('white'))
    tft.clear()


def main():
    """ main function """
    try:
        rtc = machine.RTC()
        do_connect(rtc)

        tft = display.TFT()
        config = build_init_config(tft)

        # RED = 0xFFFFFF - tft.RED
        # BLACK = 0xFFFFFF - tft.BLACK
        config["SCREEN_ROTATION"] = tft.LANDSCAPE

        if config["SCREEN_ROTATION"] == tft.PORTRAIT:

            config['block_width'] = int(SCREEN_Y)
            config['block_height'] = int(SCREEN_X / 2)
        elif config["SCREEN_ROTATION"] == tft.LANDSCAPE:

            config['block_width'] = int(SCREEN_X / 2)
            config['block_height'] = int(SCREEN_Y)

        print("dumping config\n{}".format(json.dumps(config)))


        init_tft(tft, config)

        # initial setup things
        time_right = ""
        time_left = ""
        check_timer = 0
        prev_left = ""
        prev_right = ""
        # prev_date_left = ""
        # prev_date_right = ""

        while True:
            time_left = time_string(rtc, LEFT_UTC_OFFSET_HOURS)
            time_right = time_string(rtc, RIGHT_UTC_OFFSET_HOURS)

            date_left = date_string(rtc, LEFT_UTC_OFFSET_HOURS)
            date_right = date_string(rtc, RIGHT_UTC_OFFSET_HOURS)

            if (prev_left != time_left) or (prev_right != time_right):

                if config["SCREEN_ROTATION"] == tft.PORTRAIT:
                    x1 = y1 = x2 = 0
                    y2 = int(SCREEN_Y/2)
                else:
                    x1 = y1 = y2 = 0
                    x2 = int(SCREEN_X/2)
                #x, y, title, date_text, time_text, prev_time_text, prev_date_text
                do_block(config, x1, y1,
                        title=LEFT_TITLE,
                        time_text=time_left,
                        prev_time_text=prev_left,
                        date_text=date_left,
                        )
                do_block(config, x2, y2,
                        title=RIGHT_TITLE,
                        time_text=time_right,
                        prev_time_text=prev_right,
                        date_text=date_right,
                        )
                prev_left = time_left
                prev_right = time_right

                # prev_date_left = date_left
                # prev_date_right = date_right

            utime.sleep(2)
            check_timer = check_sync_ntp(check_timer, rtc)

    # pylint: disable=broad-except
    except Exception as error_message:
        display_error(error_message, config)
        sys.exit()

main()
