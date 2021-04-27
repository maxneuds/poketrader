# Commanda

## Connection

connect device A

```
adb -d tcpip 5555
adb connect 192.168.1.30
```

connect device B

```
adb -d tcpip 5555
adb connect 192.168.1.31
```

## Get Screenshot

adb -s 192.168.1.30:5555 exec-out screencap -p > pogo_trade_00.png
