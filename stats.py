#!/usr/bin/env python3
# Created by: Michael Klements & Wesley de Vree (Macley(kun))
# For Raspberry Pi Desktop Case with OLED Stats Display
# Base on Adafruit CircuitPython & SSD1306 Libraries
# Installation & Setup Instructions - https://www.the-diy-life.com/add-an-oled-stats-display-to-raspberry-pi-os-bullseye/
from board import I2C, D4
from digitalio import DigitalInOut
from adafruit_ssd1306 import SSD1306_I2C
from subprocess import check_output
from time import sleep
from PIL import Image, ImageDraw, ImageFont
from os import environ
from datetime import datetime
from logging import info as logInfo, INFO, basicConfig
from sys import exit
from signal import signal, SIGTERM, SIGINT

basicConfig(
    format="%(asctime)s %(levelname)-4s %(message)s",
    level=INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logInfo("Starting the OLED Stats Display")


def terminate(signal, frame):
    logInfo("Stopping the OLED Stats Display")
    oled.fill(0)
    oled.show()

    logInfo("finished")
    exit(0)


signal(SIGTERM, terminate)
signal(SIGINT, terminate)


# Display Parameters
width = 128
height = 64

# Font size
font_sz = 16

start = int(environ.get("start") or 8)
end = int(environ.get("end") or 23)
current = int(datetime.now().time().strftime("%H"))

logInfo("The display will be on between %s:00 and %s:00", start, end)

# Method to control the display with oled func
oled = SSD1306_I2C(width, height, I2C(), addr=0x3C, reset=DigitalInOut(D4))

# Clear display.
oled.fill(0)
oled.show()

# Create a blank image for drawing in 1-bit color
image = Image.new("1", (oled.width, oled.height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Import custom fonts
font = ImageFont.truetype("PixelOperator.ttf", font_sz)
icon_font = ImageFont.truetype("lineawesome-webfont.ttf", font_sz)


def draw_icons():
    # Icon wifi, chr num comes from unicode &#xf1eb; to decimal 61931 (Use: https://www.binaryhexconverter.com/hex-to-decimal-converter)
    draw.text(
        (1, 0), chr(61931), font=icon_font, fill=255
    )  # Offset the icon on the x-as a little and divide the y-as in steps of 16

    # Icon cpu
    draw.text((1, 16), chr(62171), font=icon_font, fill=255)

    # Icon temp right
    draw.text(
        (111, 16), chr(62153), font=icon_font, fill=255
    )  # Offset the icon from the left to the farthest right

    # Icon memory
    draw.text((1, 32), chr(62776), font=icon_font, fill=255)

    # Icon disk
    draw.text((1, 48), chr(63426), font=icon_font, fill=255)

    # Icon time right
    draw.text((111, 48), chr(62034), font=icon_font, fill=255)


def getOutput(cmd: str) -> str:
    return check_output(
        cmd,
        shell=True,
        encoding="utf-8",
    )


# The total memory is constant, so we can fetch it only once
MemTotal = getOutput(
    "cat /proc/meminfo | head -n 1 | awk -v CONVFMT='%.0f' '{printf $2/1000000}'"
)


while True:
    while start < current < end:
        current = int(datetime.now().time().strftime("%H"))

        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, oled.width, oled.height), fill=0)

        IP = getOutput(
            "ip addr | awk '/inet / { print $2 }' | sed -n '2{p;q}' | cut -d '/' -f1"
        )

        # Takes a second to fetch for accurate cpu usage in %
        CPU = getOutput(
            "vmstat 4 2 | tail -1 | awk '{print 100-$15}' | tr -d '\n'",
        )

        MemUse = getOutput(
            "free -m | awk 'NR==2{printf $3}'| awk '{printf $1/1000}'",
        )

        # MemUsePercent = getOutput(
        #     "free -m | awk -v CONVFMT='%.1f' 'NR==2{printf $3*100/$2}'"
        # )
        MemUsePercent = format((float(MemUse) * 100) / float(MemTotal), ".1f")

        # TODO: disk is also something we don't need to fetch every time
        Disk = getOutput('df -h | awk \'$NF=="/"{printf "%s", $5}\'')

        # TODO: update can be done every minute
        uptime = getOutput("uptime | awk '{print $3,$4}' | cut -f1 -d','")

        temperature = getOutput(
            "cat /sys/class/thermal/thermal_zone*/temp | awk -v CONVFMT='%.1f' '{printf $1/1000}'"
        )

        draw_icons()

        # Pi Stats Display, printed from left to right each line
        # x y followed by the content to be printed on the display followed by how it should be printed
        draw.text((22, 0), IP, font=font, fill=255)
        draw.text((22, 16), CPU + "%", font=font, fill=255)

        # anchor basically refers to printing right to left: https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html#specifying-an-anchor
        draw.text(
            (107, 16),
            temperature + "°C",
            font=font,
            fill=255,
            anchor="ra",
        )
        draw.text((22, 32), MemUsePercent + "%", font=font, fill=255)
        draw.text(
            (125, 32),
            MemUse + "/" + MemTotal + "G",
            font=font,
            fill=255,
            anchor="ra",
        )
        draw.text((22, 48), Disk, font=font, fill=255)
        draw.text((107, 48), uptime, font=font, fill=255, anchor="ra")

        # Display image
        oled.image(image)
        oled.show()
        sleep(2)
    else:
        oled.fill(0)
        oled.show()
        sleep(60)
        current = int(datetime.now().time().strftime("%H"))
