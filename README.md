# poketrader
Auto trade pokemon on two android phones

# Prerequirements

- [Tesseract](https://tesseract-ocr.github.io/tessdoc/Downloads.html)
- [Python (Miniconda)](https://docs.conda.io/en/latest/miniconda.html)

Suggested setup:

```bash
conda create --name pokemon python=3.9
```

# Installation

```bash
conda activate pokemon
pip install -r req.txt
```

# Runner

## Linux

Make sure to call the script with the correct python interpreter from the right `conda` or `pipenv` environment.

```bash
#!/bin/bash
runner=/path/to/python
script=/path/to/poketrader/pogo_trader.py
adb devices
sleep 1
$runner $script
```

Also nice to bind the script to an alias.

```bash
alias poketrade 'bash /home/max/.scripts/poketrade.sh'
```

## Windows

Soon.

# Command Archive

## PIP

```bash
pip list --format=freeze > req.txt
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
