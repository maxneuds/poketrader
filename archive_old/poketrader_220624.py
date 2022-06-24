from os import lseek, _exit as exit
from tkinter.tix import Tree
from ppadb.client import Client as AdbClient
from PIL import Image
import pytesseract as tes
import cv2
import numpy as np
import re
import sys
from datetime import datetime as dt
from time import sleep
from multiprocessing import Process
import subprocess as syscall
import remi.gui as gui
from remi import start, App

# PIP
# pip install opencv-python-headless numpy pytesseract pure-python-adb remi
#

##
## Global Vars
##

count_traded = 0


##
## Utility Functions
##


def logger(dev_name, msg):
  dt_now = dt.now().strftime("%H:%M:%S")
  print(f'{dev_name}, {dt_now}: {msg}')


def get_devdata(dev_con):
  serialno = re.findall(
      pattern=r": \[(.+)\]",
      string=dev_con.shell("getprop | grep ro.serialno")
  )[0]
  # check if device is connected by usb
  if not serialno.startswith("0123456789"):
    name = re.findall(
        pattern=r": \[(.+)\]",
        string=dev_con.shell("getprop | grep ro.product.device")
    )[0]
    devdata = {"dev": dev_con, "name": name, "serialno": serialno}
  else:
    devdata = False
  return(devdata)

##
## UI Functions
##


def action_tap(device, pos):
  cmd = f'input tap {pos[0]} {pos[1]}'
  device.shell(cmd)


def action_back(device):
  cmd = f'input keyevent 4'
  device.shell(cmd)


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
## Bot Functions
##


def screen_character(device, device_name):
  ocr_target = 'TRADE'
  target_found = False
  inv = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device, inv=inv)
    inv = not inv
    target_found = ocr_target in text_string
    if target_found:
      logger(device_name, 'Character screen found!')
      words = ocr['text']
      for idx, word in enumerate(words):
        if word == 'TRADE':
          # tap trade button
          pos_x = int(ocr['left'][idx] + 10)
          pos_y = int(ocr['top'][idx] - 10)
          pos = (pos_x, pos_y)
          action_tap(device, pos)
          # move on to pokemon selection
          sleep(2)
          screen_pokemon_select(device, device_name)
    else:
      logger(device_name, 'Character screen not found!')
      sleep(0.5)


def screen_pokemon_select(device, device_name):
  ocr_target = 'autotrade'
  target_found = False
  limit = 200
  inv = True
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device, limit=limit, inv=inv)
    inv = not inv
    limit = limit - 5
    text_string = text_string.lower()
    target_found = ocr_target in text_string
    if target_found:
      logger(device_name, 'Pokemon selection screen found!')
      sleep(0.33)
      # tap first Pokemon
      words = ocr['text']
      words = [word.lower() for word in words]
      for idx, word in enumerate(words):
        if 'autotrade' in word:
          idx_target = idx
          break
      pos_x = int(ocr['left'][idx_target] - 100)
      pos_y = int(ocr['top'][idx_target])
      # make sure it's not detected too early
      if pos_y > 500:
        logger(device_name, 'Pokemon selection screen detected too early! Re-run.')
        target_found = False
        sleep(2)
        continue
      pos_y += 400
      pos = (pos_x, pos_y)
      action_tap(device, pos)
      sleep(1)
      # confirm pokemon selected
      # get ocr and screencap
      text_string, ocr = get_screen_text(device)
      text_string = text_string.lower()
      target_found = ocr_target in text_string
      if not target_found:
        # move on to pokemon confirmation 1 (next)
        logger(device_name, 'move on to pokemon confirmation 1 (next)')
        screen_pokemon_confirmation_1(device, device_name)
        break
      else:
        target_found = False
    else:
      # reset limit after a while
      if limit < 160:
        limit = 200
      logger(device_name, 'Pokemon selection screen not found!')
      sleep(0.5)


def screen_pokemon_confirmation_1(device, device_name):
  ocr_target = 'next'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device)
    text_string = text_string.lower()
    target_found = ocr_target in text_string
    if target_found:
      # tap "NEXT" button
      words = ocr['text']
      words = [word.lower() for word in words]
      for idx, word in enumerate(words):
        if word == 'next':
          idx_target = idx
          pos_x = int(ocr['left'][idx_target] + 10)
          pos_y = int(ocr['top'][idx_target] + 10)
          pos = (pos_x, pos_y)
          logger(device_name, f'Tap NEXT button: {pos}')
          action_tap(device, pos)
          # move on to pokemon confirmation 2 (confirm)
          sleep(1)
          screen_pokemon_confirmation_2(device, device_name)
    else:
      sleep(0.2)


def screen_pokemon_confirmation_2(device, device_name):
  ocr_target = 'confirm'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device)
    text_string = text_string.lower()
    target_found = ocr_target in text_string
    if target_found:
      # tap "CONFIRM" button
      words = ocr['text']
      words = [word.lower() for word in words]
      for idx, word in enumerate(words):
        if word == 'confirm':
          idx_target = idx
          pos_x = int(ocr['left'][idx_target] + 10)
          pos_y = int(ocr['top'][idx_target] + 10)
          pos = (pos_x, pos_y)
          logger(device_name, f'Tap CONFIRM button: {pos}')
          action_tap(device, pos)
          # move on to pokemon received
          sleep(9)
          screen_pokemon_received(device, device_name)
    else:
      sleep(0.2)


def screen_pokemon_received(device, device_name):
  ocr_target_1 = 'candy'
  ocr_target_2 = 'trainer'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, _ = get_screen_text(device)
    text_string = text_string.lower()
    target_found = ocr_target_1 in text_string or ocr_target_2 in text_string
    if target_found:
      logger(device_name, 'Pokemon received screen detected!')
      # press back to exit
      # logger(device_name, 'Send Back Key')
      action_back(device)
      # move on to character screen (return with main loop)
    else:
      sleep(0.2)


def bot_trader(device, device_name):
  global count_traded
  while True:
    try:
      screen_character(device, device_name)
      count_traded += 1
      logger(device_name, f'### ### ###\n\nTraded: {count_traded}\n\n### ### ###')
    except IndexError:
      pass
    except KeyboardInterrupt:
      sys.exit(0)
    sleep(0.2)

##
## Remi UI
##


style_button_default = {
    "background-color": "#ffb86c",  # dracula orange
    "border": "none",
    "color": "#282a36",  # dracula background
    "padding": "15px 32px",
    "text-align": "center",
    "text-decoration": "none",
    "display": "inline-block",
    "font-size": "16px",
    "box-shadow": "none",
}

style_button_green = {
    "background-color": "#50fa7b",  # dracula green
    "border": "none",
    "color": "#282a36",  # dracula background
    "padding": "15px 32px",
    "text-align": "center",
    "text-decoration": "none",
    "display": "inline-block",
    "font-size": "16px",
    "box-shadow": "none",
}

style_button_red = {
    "background-color": "#ff5555",  # dracula red
    "border": "none",
    "color": "#282a36",  # dracula background
    "padding": "15px 32px",
    "text-align": "center",
    "text-decoration": "none",
    "display": "inline-block",
    "font-size": "16px",
    "box-shadow": "none",
}


class PoketraderGUI(App):
  def __init__(self, *args):
    ###
    # Device Setup
    ###

    # make sure adb is running
    cmd = "adb devices"
    out = syscall.call(cmd, shell=True)

    # get all connected adb devices
    self.client = AdbClient(host="127.0.0.1", port=5037)
    devices = self.client.devices()
    self.devices = []
    for dev in devices:
      devdata = get_devdata(dev)
      if devdata is not False:
        self.devices.append(devdata)

    # init GUI
    super(PoketraderGUI, self).__init__(*args)

  def main(self):
    body = gui.BODY(style={"background-color": "#282a36"})
    container = gui.VBox(width=300, height=200, style={"background-color": "#282a36"})

    self.lbl_title = gui.Label("Poketrader", style={"color": "#f8f8f2"})
    self.lbl_title.style["font-size"] = "16px"
    self.lbl_title.style["font-weight"] = "bold"

    self.btn_start = gui.Button("Start Trader")
    self.btn_start.set_style(style_button_green)

    self.btn_start = gui.Button("Start Trader")
    self.btn_start.set_style(style_button_green)

    self.checkboxes = {}
    for dev in self.devices:
      self.checkboxes[dev["serialno"]] = gui.CheckBoxLabel(
          f"{dev['name']} ({dev['serialno']})",
          style={"background-color": "#282a36", "color": "#f8f8f2"},  # comment color: #6272a4
          checked=True)

    # setting the listener for the onclick event of the button
    self.btn_start.onclick.do(self.on_button_pressed)

    # appending a widget to another, the first argument is a string key
    container.append(self.lbl_title)
    for key in self.checkboxes:
      container.append(self.checkboxes[key])
    container.append(self.btn_start)

    # returning the root widget
    body.append(container)
    return body

  # listener function
  def on_button_pressed(self, widget):
    self.run_trades()

  def run_trades(self):
    # start traders
    for dev in self.devices:
      if self.checkboxes[dev["serialno"]].get_value() == True:
        dev_name = f"{dev['name']} ({dev['serialno']})"
        p_acc = Process(target=bot_trader, args=(dev["dev"], dev_name, ))
        p_acc.daemon = True
        p_acc.start()
        logger(dev_name, "Start Trading!")


##
## Execution Block
##

if __name__ == '__main__':
  start(
      PoketraderGUI,
      address='127.0.0.1',
      port=8420,
      multiple_instance=False,
      enable_file_cache=True,
      update_interval=0.1,
      start_browser=True
  )
