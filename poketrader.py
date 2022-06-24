from os import lseek, _exit as exit
from ppadb.client_async import ClientAsync as AdbClient
import pytesseract as tes
import cv2
import numpy as np
import re
import sys
from datetime import datetime as dt
from time import sleep
from multiprocessing import Process
import remi.gui as gui
from remi import start, App
from funs.styles import *
from funs.ui_automation import bot_trader
import asyncio

# PIP
# pip install opencv-python-headless numpy pytesseract pure-python-adb aiofiles remi
#


##
## Utility Functions
##


def logger(msg):
  dt_now = dt.now().strftime("%H:%M:%S")
  print(f"[{dt_now}] {msg}")


def logger_dev(dev_name, msg):
  dt_now = dt.now().strftime("%H:%M:%S")
  print(f"[{dt_now}] [{dev_name}] {msg}")


async def syscall(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    logger("Connecting to adb...")
    if stdout:
        print(f'{stdout.decode()}')
    if stderr:
        print("Error! Couldn't connect to ADB!")


async def get_devdata(device):
  str_prop = await device.shell("getprop | grep ro.serialno")
  serialno = re.findall(
      pattern=r": \[(.+)\]",
      string=str_prop
  )[0]
  # check if device is connected by usb
  if not serialno.startswith("0123456789"):
    str_prop = await device.shell("getprop | grep ro.product.device")
    name = re.findall(
        pattern=r": \[(.+)\]",
        string=str_prop
    )[0]
    devdata = {"dev": device, "name": name, "serialno": serialno}
  else:
    devdata = False
  return(devdata)

##
## ADB UI Functions
##


async def get_devices():
  client = AdbClient(host="127.0.0.1", port=5037)
  devices = await client.devices()
  return(devices)


def refresh_devices():
  # make sure adb is running
  cmd = "adb devices"
  asyncio.run(syscall(cmd))
  # get all connected devices
  devices = asyncio.run(get_devices())
  return(devices)


async def action_tap(device, pos):
  cmd = f"input tap {pos[0]} {pos[1]}"
  await device.shell(cmd)


async def action_back(device):
  cmd = f"input keyevent 4"
  await device.shell(cmd)


##
## OCR Functions
##


def get_screen_text(device, limit=200, inv=True):
  # get screen from device
  im_byte_array = device.screencap()
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  gray = get_grayscale(im_sc)
  thresh = thresholding(gray, limit, inv)
  ocr = tes.image_to_data(thresh, output_type=tes.Output.DICT, lang='eng', config='--psm 6')
  text_list = ocr['text']
  text_string = ''.join(text_list)
  return(text_string, ocr)


def get_grayscale(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image, limit=200, inv=True):
  if inv:
    return cv2.threshold(image, limit, 255, cv2.THRESH_BINARY_INV)[1]
  else:
    return cv2.threshold(image, limit, 255, cv2.THRESH_BINARY)[1]


def get_screencap(device):
  # get screen from device
  im_byte_array = device.screencap()
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  return(im_sc)


def get_screen_targets(im_sc, im_target):
  # search for target on screen
  targets = cv2.matchTemplate(im_sc, im_target, cv2.TM_CCOEFF_NORMED)
  targets = np.where(targets >= 0.80)
  return(targets)


def scan_im(device, im_target):
  targets = [[]]
  while len(targets[0]) == 0:
    im_sc = get_screencap(device)
    targets = get_screen_targets(im_sc, im_target)
  # target is the first rectangle
  target_shape = im_target.shape
  target_pos_x = int(targets[1][0] + 0.5*target_shape[1])
  target_pos_y = int(targets[0][0] + 0.5*target_shape[0])
  target_pos = (target_pos_x, target_pos_y)
  return(target_pos)

##
## Remi UI
##


class PoketraderGUI(App):
  def __init__(self, *args):
    # Init Variables
    self.p_traders = []
    # Init GUI
    super(PoketraderGUI, self).__init__(*args)

  def main(self):
    body = gui.BODY(style={"background-color": "#282a36"})
    self.container_body = gui.VBox(width=400, height=200, style={"background-color": "#282a36"})

    self.lbl_title = gui.Label("Poketrader", style={"color": "#ff79c6"})
    self.lbl_title.style["font-size"] = "16px"
    self.lbl_title.style["font-weight"] = "bold"

    # Fixed Buttons
    self.container_fixed_buttons = gui.HBox(width=300, height=80, style={"background-color": "#282a36"})
    btn_refresh = gui.Button("Refresh Devices")
    btn_refresh.set_style(style_button_default)
    btn_refresh.onclick.do(self.action_refresh_devices)
    self.container_fixed_buttons.append(btn_refresh)

    # Variable Buttons
    self.container_btns_devices = gui.VBox(width=300, height=80, style={"background-color": "#282a36"})

    # return body
    self.container_body.append([self.lbl_title, self.container_fixed_buttons, self.container_btns_devices])
    body.append(self.container_body)
    return(body)

  ##
  ## Actions
  ##

  def action_trader(self, widget):
    active = widget.kwargs["active"]
    p_trader = widget.kwargs["p_trader"]
    name = widget.kwargs["name"]
    if not active:
      p_trader.start()
      logger_dev(name, "Start Trading!")
      widget.set_style(style_button_green)
      widget.kwargs["active"] = True
    else:
      p_trader.terminate()
      p_trader.join()
      widget.set_style(style_button_red)
      widget.kwargs["active"] = False

  def action_refresh_devices(self, widget):
    devices = refresh_devices()
    self.add_devices_to_gui(devices)

  def add_devices_to_gui(self, devices):
    self.container_btns_devices.empty()
    # if processes are running, terminate these
    # Todo: Could most likely be coded in a way
    #       such that devices can be added and removed
    #       without affecting running processes
    try:
      if len(self.p_traders) > 0:
        for p in self.p_traders:
          p.terminate()
          p.join()
    except Exception as e:
      self.p_traders = []
    for dev in devices:
      # parse device data
      devdata = asyncio.run(get_devdata(dev))
      name = devdata["name"]
      serialno = devdata["serialno"]
      # create process for action
      p_trader = Process(target=bot_trader, args=(dev, name, ))
      p_trader.daemon = True
      self.p_traders.append(p_trader)
      # add everything to an action button for execution
      hbox = gui.HBox(width=300, height=80, style={"background-color": "#282a36"})
      btn = gui.Button(f"{name} [{serialno}]", p_trader=p_trader, name=name, active=False)
      btn.onclick.do(self.action_trader)
      btn.set_style(style_button_red)
      btn.set_size(150, 70)
      lbl = gui.Label("Traded: ", width=100, height=80, style=label_left_center)
      hbox.append([btn, lbl])
      # add button to container
      self.container_btns_devices.append(hbox)
    # update button container
    self.container_btns_devices.set_size(400, len(devices) * 80)
    self.container_body.set_size(400, len(devices) * 80 + 120)
    self.container_body.redraw()


##
## Execution Block
##

if __name__ == '__main__':
  start(
      PoketraderGUI,
      address='127.0.0.1',
      port=42069,
      multiple_instance=False,
      enable_file_cache=True,
      update_interval=0.1,
      start_browser=False
  )
