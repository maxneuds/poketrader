from os import lseek
from ppadb.client import Client as AdbClient
from PIL import Image
import pytesseract as tes
import cv2
import numpy as np
from time import sleep
# from multiprocessing import Pool, Process
import threading

###
# parameters
###

ss_def = '!legendary&!mythical&!shiny&!4*&!☆&!⓪&!①&!②&'
# account 1
ip_acc1 = '192.168.1.30:5555'
ss_acc1 = f'{ss_def}'
# account 2
ip_acc2 = '192.168.1.103:5555'
ss_acc2 = f'{ss_def}chansey'

###
# main
###

def get_screen_text(device):
  # get screen from device
    im_byte_array = device.screencap()
    im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
    gray = get_grayscale(im_sc)
    thresh = thresholding(gray)
    ocr = tes.image_to_data(thresh, output_type=tes.Output.DICT)
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
  targets = np.where(targets >= 0.90)
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

#thresholding
def thresholding(image):
  # return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
  return cv2.threshold(image, 230, 255, cv2.THRESH_BINARY)[1]


def screen_character(device):
  # wait until screen matches
  s_target = 'SENDGIFTBATTLETRADE'
  ocr = scan_text(device, s_target)
  # tap trade button
  words = ocr['text']
  for idx, word in enumerate(words):
    if word == 'GIFT' and words[idx+1] == 'BATTLE' and words[idx+2] == 'TRADE':
      idx_target = idx +2
      pos_x = int(ocr['left'][idx_target] + 10)
      pos_y = int(ocr['top'][idx_target] -10)
      pos = (pos_x, pos_y)
      action_tap(device, pos)
  # move on to pokemon selection
  screen_pokemon_select(device)

def screen_pokemon_select(device):
  s_target = 'POKEMONQ('
  ocr = scan_text(device, s_target)
  # tap first target pokemon
  path_target = 'res/pogo_target_healthbar.png'
  im_target = cv2.imread(path_target)
  target_pos = get_im_pos(device, im_target)
  # tap pokeman
  action_tap(device, target_pos)
  # move on to pokemon confirmation 1
  screen_pokemon_confirmation_1(device)

def screen_pokemon_confirmation_1(device):
  # find "NEXT" button
  path_target = 'res/pogo_target_next.png'
  im_target = cv2.imread(path_target)
  target_pos = scan_im(device, im_target)
  # press "NEXT" button
  action_tap(device, target_pos)
  # move on to pokemon confirmation 2
  screen_pokemon_confirmation_2(device)

def screen_pokemon_confirmation_2(device):
  # find "CONFIRM" button
  path_target = 'res/pogo_target_confirm.png'
  im_target = cv2.imread(path_target)
  target_pos = scan_im(device, im_target)
  # press "CONFIRM" button
  action_tap(device, target_pos)
  # move on to pokemon received screen
  screen_pokemon_received(device)


def screen_pokemon_received(device):
  s_target = 'STARDUSTS'
  ocr = scan_text(device, s_target)
  # find "X" button
  path_target = 'res/pogo_target_x.png'
  im_target = cv2.imread(path_target)
  target_pos = get_im_pos(device, im_target)
  # press "X" button
  action_tap(device, target_pos)
  # move on to character screen
  screen_character(device)

def get_im_pos(device, im_target):
  # get screen from device
  im_byte_array = device.screencap()
  im_sc = cv2.imdecode(np.frombuffer(bytes(im_byte_array), np.uint8), cv2.IMREAD_COLOR)
  # search for target on screen
  target_shape = im_target.shape
  targets = cv2.matchTemplate(im_sc, im_target, cv2.TM_CCOEFF_NORMED)
  targets = np.where(targets >= 0.90)
  # target is the first rectangle
  target_pos_x = int(targets[1][0] + 0.5*target_shape[1])
  target_pos_y = int(targets[0][0] + 0.5*target_shape[0])
  target_pos = (target_pos_x, target_pos_y)
  return(target_pos)

def bot_trader(device, dict_targets):
  # text targets
  s_target_character_screen = dict_targets['t_cs']
  s_target_pokemon_select = dict_targets['t_ps']
  s_target_pokemon_received = dict_targets['t_pr']
  # image targets
  im_target_next = dict_targets['t_n']
  im_target_confirm = dict_targets['t_c']
  # iterate over screens
  while True:
    # get ocr and screencap
    text_string, _ = get_screen_text(device)
    im_sc = get_screencap(device)
    if s_target_character_screen in text_string:
      screen_character(device)
    elif s_target_pokemon_select in text_string:
      screen_pokemon_select(device)
    elif len(get_screen_targets(im_sc, im_target_next)[0]) > 0:
      screen_pokemon_confirmation_1(device)
    elif len(get_screen_targets(im_sc, im_target_confirm)[0]) > 0:
      screen_pokemon_confirmation_2(device)
    elif s_target_pokemon_received in text_string:
      screen_pokemon_received(device)
    else:
      sleep(0.1)

def main(client):
  # get devices
  devices = client.devices()
  # verify only two phones connected
  if len(devices) == 2:
    print('2 devices found!')
    dev_acc1 = client.device(ip_acc1)
    dev_acc2 = client.device(ip_acc2)

    # text targets
    s_target_character_screen = 'SENDGIFTBATTLETRADE'
    s_target_pokemon_select = 'POKEMONQ('
    s_target_pokemon_received = 'STARDUSTS'
    # image targets
    path_target_next = 'res/pogo_target_next.png'
    im_target_next = cv2.imread(path_target_next)
    path_target_confirm = 'res/pogo_target_confirm.png'
    im_target_confirm = cv2.imread(path_target_confirm)
    # combine targets
    dict_targets = {
      't_cs': s_target_character_screen,
      't_ps': s_target_pokemon_select,
      't_pr': s_target_pokemon_received,
      't_n': im_target_next,
      't_c': im_target_confirm,
    }
  # run bot
    bot_trader(dev_acc1, dict_targets)
  elif len(devices) < 2:
    print('Less than 2 devices found!')
  else:
    print('More than 2 devices found!')

def action_tap(device, pos):
  cmd = f'input tap {pos[0]} {pos[1]}'
  device.shell(cmd)

if __name__ == '__main__':
  # adb defaults
  client = AdbClient(host="127.0.0.1", port=5037)
  main(client)
