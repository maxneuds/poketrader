from datetime import datetime as dt
from multiprocessing import Process
import remi.gui as gui
from remi import start, App
from funs.styles import *
from funs.ui_automation import *
import asyncio

# PIP
# pip install opencv-python-headless numpy pytesseract pure-python-adb aiofiles remi
#


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
# Remi UI
##


class PoketraderGUI(App):
  def __init__(self, *args):
    # Init Variables
    self.p_traders = {}
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
  # Actions
  ##

  def action_trader(self, widget):
    active = widget.kwargs["active"]
    dev = widget.kwargs["dev"]
    name = widget.kwargs["name"]
    serialno = widget.kwargs["serialno"]
    if not active:
      # create process for action
      p_trader = Process(target=bot_trader, args=(dev, name, ))
      p_trader.daemon = True
      self.p_traders[serialno] = p_trader
      p_trader.start()
      logger_dev(name, "Start Trading!")
      widget.set_style(style_button_green)
      widget.kwargs["active"] = True
    else:
      p_trader = self.p_traders[serialno]
      p_trader.terminate()
      p_trader.join()
      logger_dev(name, "Stop Trading!")
      widget.set_style(style_button_red)
      widget.kwargs["active"] = False

  def action_refresh_devices(self, widget):
    devices = asyncio.run(refresh_devices())
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
      self.p_traders = {}
    for dev in devices:
      # parse device data
      devdata = asyncio.run(get_devdata(dev))
      name = devdata["name"]
      serialno = devdata["serialno"]
      # add everything to an action button for execution
      hbox = gui.HBox(width=300, height=80, style={"background-color": "#282a36"})
      btn = gui.Button(f"{name} [{serialno}]", dev=dev, name=name, serialno=serialno, active=False)
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
# Execution Block
##

if __name__ == '__main__':
  start(
      PoketraderGUI,
      address='127.0.0.1',
      port=42069,
      multiple_instance=False,
      enable_file_cache=True,
      update_interval=0.1,
      start_browser=True
  )
