from os import lseek
from ppadb.client import Client as AdbClient
from PIL import Image
import pytesseract as tes
import cv2
import numpy as np
import re
from time import sleep
from multiprocessing import Process
# import threading

###
# parameters
###

ss_def = '!legendary&!mythical&!shiny&!4*&!☆&!⓪&!①&!②&'
# account 1
ip_acc1 = '192.168.10.2:5555'
ss_acc1 = f'{ss_def}'
# account 2
ip_acc2 = '192.168.10.1:5555'
ss_acc2 = f'{ss_def}chansey'

###
# main
###


def get_screen_text(device, inv=True):
  # get screen from device
  im_byte_array = device.screencap()
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  gray = get_grayscale(im_sc)
  thresh = thresholding(gray, inv)
  ocr = tes.image_to_data(thresh, output_type=tes.Output.DICT, lang='eng', config='--psm 6')
  text_list = ocr['text']
  text_string = ''.join(text_list)
  return(text_string, ocr)


def scan_text(device, s_target):
  text_string = ''
  while s_target not in text_string:
    text_string, ocr = get_screen_text(device)
    # debug
    # print(text_string)
  return(ocr)


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

# get grayscale image


def get_grayscale(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# thresholding


def thresholding(image, inv=True):
  # return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
  if inv:
    return cv2.threshold(image, 200, 255, cv2.THRESH_BINARY_INV)[1]
  else:
    return cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)[1]


def screen_character(device):
  ocr_target = 'TRADE'
  target_found = False
  inv = False
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device, inv = inv)
    inv = not inv
    target_found = ocr_target in text_string
    if target_found:
      print('Character screen found!')
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
          screen_pokemon_select(device)
    else:
      print('Character screen not found!')


def screen_pokemon_select(device):
  ocr_target = 'qautotrade'
  target_found = False
  inv = True
  # iterate over screens
  while not target_found:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device, inv = inv)
    inv = not inv
    text_string = text_string.lower()
    target_found = ocr_target in text_string
    if target_found:
      print('Pokemon selection screen found!')
      sleep(0.33)
      # tap first Pokemon
      words = ocr['text']
      words = [word.lower() for word in words]
      for idx, word in enumerate(words):
        if word == 'q' and words[idx + 1].startswith('autotrade'):
          idx_target = idx
          pos_x = int(ocr['left'][idx_target] - 20)
          pos_y = int(ocr['top'][idx_target])
          # make sure it's not detected too early
          if pos_y > 500:
            print('Pokemon selection screen detected too early! Re-run.')
            target_found = False
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
        print('move on to pokemon confirmation 1 (next)')
        screen_pokemon_confirmation_1(device)
        break
      else:
        target_found = False
    else:
      print('Pokemon selection screen not found!')
      sleep(0.5)


def screen_pokemon_confirmation_1(device):
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
          action_tap(device, pos)
          # move on to pokemon confirmation 2 (confirm)
          sleep(1)
          screen_pokemon_confirmation_2(device)
    else:
      sleep(0.2)


def screen_pokemon_confirmation_2(device):
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
          action_tap(device, pos)
          # move on to pokemon received
          sleep(9)
          screen_pokemon_received(device)
    else:
      sleep(0.2)


def screen_pokemon_received(device):
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
      print('Pokemon received screen detected!')
      # press back to exit
      print('Send Back Key')
      action_back(device)
      # move on to character screen (return with main loop)
    else:
      sleep(0.2)


def get_im_pos(device, im_target):
  # get screen from device
  im_byte_array = device.screencap()
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  # search for target on screen
  target_shape = im_target.shape
  targets = cv2.matchTemplate(im_sc, im_target, cv2.TM_CCOEFF_NORMED)
  targets = np.where(targets >= 0.80)
  # target is the first rectangle
  target_pos_x = int(targets[1][0] + 0.5*target_shape[1])
  target_pos_y = int(targets[0][0] + 0.5*target_shape[0])
  target_pos = (target_pos_x, target_pos_y)
  return(target_pos)


def bot_trader(device):
  while True:
    try:
      screen_character(device)
    except IndexError:
      pass
    sleep(0.2)


def main(client):
  # get devices
  devices = client.devices()
  # verify only two phones connected
  if len(devices) >= 2:
    print('2 devices found!')
    dev_acc1 = client.device(ip_acc1)
    dev_acc2 = client.device(ip_acc2)
    # run bots
    p_acc1 = Process(target=bot_trader, args=(dev_acc1,))
    p_acc2 = Process(target=bot_trader, args=(dev_acc2,))
    p_acc1.start()
    p_acc2.start()
  else:
    print('Less than 2 devices found!')


def action_tap(device, pos):
  cmd = f'input tap {pos[0]} {pos[1]}'
  device.shell(cmd)


def action_back(device):
  cmd = f'input keyevent 4'
  device.shell(cmd)


if __name__ == '__main__':
  # adb defaults
  client = AdbClient(host="127.0.0.1", port=5037)
  main(client)
