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
ip_acc1 = '192.168.1.30:5555'
ss_acc1 = f'{ss_def}'
# account 2
ip_acc2 = '192.168.1.31:5555'
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


def screen_character(device, ocr):
  # tap trade button
  words = ocr['text']
  for idx, word in enumerate(words):
    if word == 'GIFT' and words[idx + 1] == 'BATTLE' and words[idx + 2] == 'TRADE':
      idx_target = idx + 2
      pos_x = int(ocr['left'][idx_target] + 10)
      pos_y = int(ocr['top'][idx_target] - 10)
      pos = (pos_x, pos_y)
      action_tap(device, pos)


def screen_pokemon_select(device, ocr):

  def tap_pokemon(words, ocr, regex_pattern):
    target_found = False
    for idx, word in enumerate(words):
      if bool(regex_pattern.match(word)):
        target_found = True
        idx_target = idx
        pos_x = int(ocr['left'][idx_target])
        pos_y = int(ocr['top'][idx_target])
        pos = (pos_x + 4, pos_y + 32)
        action_tap(device, pos)
        sleep(0.75)
    return(target_found)

  regex_pattern = re.compile(r'^c(e|p)p?\d{0,4}?', re.IGNORECASE)

  # tap first Pokemon
  words = ocr['text']
  words = [word.lower() for word in words]
  target_found = tap_pokemon(words, ocr, regex_pattern)
  if target_found is False:
    _, ocr = get_screen_text(device, inv=False)
    words = ocr['text']
    words = [word.lower() for word in words]
    target_found = tap_pokemon(words, ocr, regex_pattern)


def screen_pokemon_confirmation_1(device, ocr):
  # tap "NEXT" button
  words = ocr['text']
  words = [word.lower() for word in words]
  for idx, word in enumerate(words):
    if word == 'next':
      idx_target = idx
      pos_x = int(ocr['left'][idx_target])
      pos_y = int(ocr['top'][idx_target])
      pos = (pos_x, pos_y)
      action_tap(device, pos)
      sleep(3)


def screen_pokemon_confirmation_2(device, ocr):
  # tap "CONFIRM" button
  words = ocr['text']
  words = [word.lower() for word in words]
  for idx, word in enumerate(words):
    if word == 'confirm':
      idx_target = idx
      pos_x = int(ocr['left'][idx_target])
      pos_y = int(ocr['top'][idx_target])
      pos = (pos_x, pos_y)
      action_tap(device, pos)
      # prevent confirm - cancel loop
      sleep(5)


def screen_pokemon_received(device):
  # press back to exit
  print('Send Back Key')
  action_back(device)


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


def bot_trader(device, dict_targets):
  # text targets
  s_target_character_screen = dict_targets['t_cs']
  b_target_pokemon_select = dict_targets['t_ps']
  s_target_pokemon_received = dict_targets['t_pr']
  s_target_next = dict_targets['t_n']
  s_target_confirm = dict_targets['t_c']
  # cheap unstuck count
  count_unstuck = 0
  # iterate over screens
  while True:
    # get ocr and screencap
    text_string, ocr = get_screen_text(device)
    if s_target_character_screen in text_string:
      print('Character selection screen detected!')
      try:
        screen_character(device, ocr)
        count_unstuck = 0
      except IndexError:
        pass
    elif bool(re.search(b_target_pokemon_select, text_string)):
      print('Pokemon selection screen detected!')
      try:
        screen_pokemon_select(device, ocr)
        count_unstuck = 0
      except IndexError:
        pass
    elif s_target_next in text_string:
      print('NEXT screen detected!')
      try:
        screen_pokemon_confirmation_1(device, ocr)
        count_unstuck = 0
      except IndexError:
        pass
    elif s_target_confirm in text_string:
      print('CONFIRM screen detected!')
      try:
        screen_pokemon_confirmation_2(device, ocr)
        count_unstuck = 0
      except IndexError:
        pass
    elif s_target_pokemon_received in text_string:
      print('Pokemon view screen detected!')
      try:
        screen_pokemon_received(device)
        count_unstuck = 0
      except IndexError:
        pass
    else:
      text_string, ocr = get_screen_text(device, inv=False)
      if s_target_pokemon_received in text_string:
        try:
          screen_pokemon_received(device)
          count_unstuck = 0
        except IndexError:
          pass
      count_unstuck = count_unstuck + 1
      if count_unstuck > 20:
        print('Stuck? Press Back.')
        action_back(device)
        sleep(0.5)
        count_unstuck = 0
      sleep(0.1)


def main(client):
  # get devices
  devices = client.devices()
  # verify only two phones connected
  if len(devices) >= 2:
    print('2 devices found!')
    dev_acc1 = client.device(ip_acc1)
    dev_acc2 = client.device(ip_acc2)

    # targets
    s_target_character_screen = 'SENDGIFTBATTLETRADE'
    b_target_pokemon_select = r'POKEMON.{0,9}Q'
    s_target_pokemon_received = 'STARDUST'
    s_target_next = 'NEXT'
    # path_target_next = 'res/pogo_target_next.png'
    # im_target_next = cv2.imread(path_target_next)
    s_target_confirm = 'CONFIRM'
    # combine targets
    dict_targets = {
        't_cs': s_target_character_screen,
        't_ps': b_target_pokemon_select,
        't_pr': s_target_pokemon_received,
        't_n': s_target_next,
        't_c': s_target_confirm,
    }
    # run bots
    p_acc1 = Process(target=bot_trader, args=(dev_acc1, dict_targets,))
    p_acc2 = Process(target=bot_trader, args=(dev_acc2, dict_targets,))
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
