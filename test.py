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

    cv2.imwrite('cv_out.png', thresh)

    ocr = tes.image_to_data(thresh, output_type=tes.Output.DICT)
    text_list = ocr['text']
    text_string = ''.join(text_list)
    return(text_string, ocr)

# get grayscale image
def get_grayscale(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#thresholding
def thresholding(image):
  # return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
  return cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)[1]


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
    get_screen_text(dev_acc1)

def action_tap(device, pos):
  cmd = f'input tap {pos[0]} {pos[1]}'
  device.shell(cmd)

if __name__ == '__main__':
  # adb defaults
  client = AdbClient(host="127.0.0.1", port=5037)
  main(client)
