#!/bin/bash

while :
do
  # tap trade button
  adb shell input tap 900 900
  sleep 0.5
  adb shell input tap 900 2000
  sleep 5

  # tap search bar away
  adb shell input tap 30 120
  sleep 0.2
  adb shell input tap 30 1300
  sleep 0.5

  # tap pokemon
  adb shell input tap 186 700
  sleep 1
  adb shell input tap 186 1830
  sleep 2

  # tap next button
  adb shell input tap 540 960
  sleep 1
  adb shell input tap 540 2075
  sleep 2

  # tap ok button
  adb shell input tap 40 645
  sleep 1
  adb shell input tap 40 1760
  sleep 21

  # tap x button
  adb shell input tap 540 1090
  sleep 0.75
  adb shell input tap 540 2205
  sleep 1.5
done
