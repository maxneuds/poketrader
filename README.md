# poketrader
Auto trade Pokemon on two android phones

# Usage

0. Add all Pokemon which you want to trade into a tag which starts with `autotrade`.
1. Start a normal trade, select the tag and trade one Pokemon.
2. Be in character screen (with the trade button). This is the starting screen.
3. Press `Refresh Device`.
4. Start the trader on the device by clicking the corresponding button.

# Prerequirements

- `ADB`: [Windows](https://androiddatahost.com/uq6us)
- [Python 3.9+](https://www.python.org/downloads/)
- [Tesseract](https://tesseract-ocr.github.io/tessdoc/Downloads.html)

# Installation

Especially on windows, make sure that `adb`, `tesseract` (with English language support) and python are setup in `PATH`.

First clone this repository.

```bash
git clone https://github.com/maxneuds/poketrader.git
```

Then, create a new python `venv` in the app directory of `poketrader`.

```bash
python -m venv env
```

After that, activate the environment and install all required packages from the requirements file `req.txt`.

```bash
source env/bin/activate
pip install -r req.txt
```

# Runner

## Linux

```bash
#!/bin/bash
dir_poketrader=/path/to/dir
activate_script=env/bin/activate.fish
cd $dir_poketrader
source $activate_script
python poketrader.py
```

Also nice to bind the script to an alias.

```bash
alias poketrade 'bash /path/to/runner.sh'
```

## Windows

```powershell
cd C:\path_to_poketrader
. .\env\Scripts\activate.ps1
python poketrader.py
```

# Command Archive

## PIP

```bash
pip freeze > req.txt
```

## ADB

connect device A

```
adb -d tcpip 5555
adb connect 192.168.42.69
```

connect device B

```
adb -d tcpip 5555
adb connect 192.168.42.69
```

screenshot

```bash
adb -s 8820d65c shell screencap -p > screenx.png
adb -s 192.168.42.69 exec-out screencap -p > screenx.png
```
