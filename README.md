# poketrader
Auto trade pokemon on two android phones

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
$path_app=/path/to/poketrader
source $path_app/env/bin/activate
python $path_app/poketrader.py
```

Also nice to bind the script to an alias.

```bash
alias poketrade 'bash /path/to/runner.sh'
```

## Windows

Soon.

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
