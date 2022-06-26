import numpy as np
import cv2
import pytesseract as tes
import re
from datetime import datetime as dt
from asyncio import sleep, run, subprocess, create_subprocess_shell
from ppadb.client_async import ClientAsync as AdbClient

##
# Utility Functions
##


def logger(msg):
  dt_now = dt.now().strftime("%H:%M:%S")
  print(f"[{dt_now}] {msg}")


def logger_dev(dev_name, msg):
  dt_now = dt.now().strftime("%H:%M:%S")
  print(f"[{dt_now}] [{dev_name}] {msg}")

##
# ADB Functions
##


async def get_devices():
  client = AdbClient(host="127.0.0.1", port=5037)
  devices = await client.devices()
  return(devices)


async def refresh_devices():
  # make sure adb is running
  cmd = "adb devices"
  # call connect to ADB server
  proc = await create_subprocess_shell(
      cmd,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)
  stdout, stderr = await proc.communicate()
  logger("Connecting to adb...")
  if stdout:
    print(f'{stdout.decode()}')
  if stderr:
    print("Error! Couldn't connect to ADB!")
  # get all connected devices
  devices = await get_devices()
  return(devices)


async def action_tap(device, pos):
  cmd = f'input tap {pos[0]} {pos[1]}'
  await device.shell(cmd)


async def action_back(device):
  cmd = f'input keyevent 4'
  await device.shell(cmd)


async def get_screencap(device):
  # get screen from device
  im_byte_array = await device.screencap()
  # convert to cv2 image
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  return(im_sc)


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
# OCR Functions
##


def get_grayscale(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image, limit=200, inv=True):
  if inv:
    return cv2.threshold(image, limit, 255, cv2.THRESH_BINARY_INV)[1]
  else:
    return cv2.threshold(image, limit, 255, cv2.THRESH_BINARY)[1]


async def get_screen_text(device, limit=200, inv=True):
  # get screen from device
  im_sc = await get_screencap(device)
  # transform to simple bw image
  gray = get_grayscale(im_sc)
  thresh = thresholding(gray, limit, inv)
  # get screen text
  ocr = tes.image_to_data(thresh, output_type=tes.Output.DICT, lang='eng', config='--psm 6')
  text_list = ocr['text']
  text_string = ''.join(text_list)
  return(text_string, ocr)


async def scan_im(device, im_target):
  targets = [[]]
  while len(targets[0]) == 0:
    im_sc = await get_screencap(device)
    targets = get_screen_targets(im_sc, im_target)
  # target is the first rectangle
  target_shape = im_target.shape
  target_pos_x = int(targets[1][0] + 0.5*target_shape[1])
  target_pos_y = int(targets[0][0] + 0.5*target_shape[0])
  target_pos = (target_pos_x, target_pos_y)
  return(target_pos)


def get_screen_targets(im_sc, im_target):
  # search for target on screen
  targets = cv2.matchTemplate(im_sc, im_target, cv2.TM_CCOEFF_NORMED)
  targets = np.where(targets >= 0.80)
  return(targets)

##
# Bot Functions
##


async def screen_pokemon_received(device, device_name):
  ocr_target_1 = 'candy'
  ocr_target_2 = 'trainer'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, _ = await get_screen_text(device)
    text_string = text_string.lower()
    target_found = ocr_target_1 in text_string or ocr_target_2 in text_string
    if target_found:
      logger_dev(device_name, 'Pokemon received screen detected!')
      # press back to exit
      await action_back(device)
      # move on to character screen (return with main loop)
    else:
      await sleep(0.2)


async def screen_pokemon_confirmation_2(device, device_name):
  ocr_target = 'confirm'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = await get_screen_text(device)
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
          logger_dev(device_name, f'Tap CONFIRM button: {pos}')
          await action_tap(device, pos)
          # move on to pokemon received
          await sleep(9)
          await screen_pokemon_received(device, device_name)
    else:
      await sleep(0.2)


async def screen_pokemon_confirmation_1(device, device_name):
  ocr_target = 'next'
  target_found = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = await get_screen_text(device)
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
          logger_dev(device_name, f'Tap NEXT button: {pos}')
          await action_tap(device, pos)
          # move on to pokemon confirmation 2 (confirm)
          await sleep(1)
          await screen_pokemon_confirmation_2(device, device_name)
    else:
      await sleep(0.2)


async def screen_pokemon_select(device, device_name):
  ocr_target = 'autotrade'
  target_found = False
  limit = 200
  inv = True
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = await get_screen_text(device, limit=limit, inv=inv)
    inv = not inv
    limit = limit - 5
    text_string = text_string.lower()
    target_found = ocr_target in text_string
    if target_found:
      logger_dev(device_name, 'Pokemon selection screen found!')
      await sleep(0.33)
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
        logger_dev(device_name, 'Pokemon selection screen detected too early! Re-run.')
        target_found = False
        await sleep(2)
        continue
      pos_y += 400
      pos = (pos_x, pos_y)
      await action_tap(device, pos)
      await sleep(1)
      # confirm pokemon selected
      # get ocr and screencap
      text_string, ocr = await get_screen_text(device)
      text_string = text_string.lower()
      target_found = ocr_target in text_string
      if not target_found:
        # move on to pokemon confirmation 1 (next)
        logger_dev(device_name, 'move on to pokemon confirmation 1 (next)')
        await screen_pokemon_confirmation_1(device, device_name)
        break
      else:
        target_found = False
    else:
      # reset limit after a while
      if limit < 160:
        limit = 200
      logger_dev(device_name, 'Pokemon selection screen not found!')
      await sleep(0.5)


async def screen_character(device, device_name):
  ocr_target = 'TRADE'
  target_found = False
  inv = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = await get_screen_text(device, inv=inv)
    inv = not inv
    target_found = ocr_target in text_string
    if target_found:
      logger_dev(device_name, 'Character screen found!')
      words = ocr['text']
      for idx, word in enumerate(words):
        if word == 'TRADE':
          # tap trade button
          pos_x = int(ocr['left'][idx] + 10)
          pos_y = int(ocr['top'][idx] - 10)
          pos = (pos_x, pos_y)
          await action_tap(device, pos)
          # move on to pokemon selection
          await sleep(2)
          await screen_pokemon_select(device, device_name)
    else:
      logger_dev(device_name, 'Character screen not found!')
      await sleep(0.5)


async def bot_trader_loop(device, device_name):
  count_traded = 0
  while True:
    try:
      await screen_character(device, device_name)
      count_traded += 1
      logger_dev(device_name, f'### ### ###\n\nTraded: {count_traded}\n\n### ### ###')
    except IndexError:
      pass
    await sleep(0.2)


def bot_trader(device, device_name):
  run(bot_trader_loop(device, device_name))
