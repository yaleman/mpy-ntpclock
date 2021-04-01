#!/bin/bash

DEVICE="tty.usbserial-0154E20F"
mpfshell  -c 'put main.py; put config.py; exit;' -n --nocache -o "${DEVICE}" && \
    mpfshell --reset -n --nocache  -o "${DEVICE}"
    #mpfshell  -c 'put config.py; exit;' -n --nocache -o "${DEVICE}" && \