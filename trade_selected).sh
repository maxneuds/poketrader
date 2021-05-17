#!/bin/bash

while :
do
  # tap trade button
  adb -s 192.168.1.142:5555 shell input swipe 540 1180 540 1500 500
  sleep 0.75
  adb -s 192.168.1.142:5555 shell input tap 934 1634
  sleep 0.3
  adb -s 192.168.1.142:5555 shell input swipe 540 1660 540 500 750
  sleep 0.75
  adb -s 192.168.1.142:5555 shell input tap 934 2275
  sleep 0.5
  adb -s 192.168.1.142:5555 shell input swipe 540 700 540 1000 500
  sleep 4
  
  # tap search bar away
  adb -s 192.168.1.142:5555 shell input tap 30 120
  sleep 0.2
  adb -s 192.168.1.142:5555 shell input tap 30 1300
  sleep 1
  
  # tap pokemon
  adb -s 192.168.1.142:5555 shell input tap 186 700
  sleep 1
  adb -s 192.168.1.142:5555 shell input tap 186 1830
  sleep 2
  
  # tap next button
  adb -s 192.168.1.142:5555 shell input tap 540 960
  sleep 1
  adb -s 192.168.1.142:5555 shell input tap 540 2075
  sleep 2
  
  # tap ok button
  adb -s 192.168.1.142:5555 shell input tap 40 645
  sleep 1
  adb -s 192.168.1.142:5555 shell input tap 40 1760
  sleep 21
  
  # tap x button
  adb -s 192.168.1.142:5555 shell input tap 540 1090
  sleep 0.75
  adb -s 192.168.1.142:5555 shell input tap 540 2205
  sleep 1.5
done
