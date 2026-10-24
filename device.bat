@echo off
echo Disconnecting old ADB connections...
adb disconnect

echo Setting device to TCP/IP mode on port 5555...
adb tcpip 5555

echo Waiting for device to initialize...
timeout /t 3 >nul

echo Getting device IP address...
FOR /F "tokens=2" %%G IN ('adb shell ip addr show wlan0 ^| find "inet "') DO set ipfull=%%G
FOR /F "tokens=1 delims=/" %%G IN ("%ipfull%") DO set ip=%%G

echo Connecting to device with IP %ip%...
adb connect %ip%

echo Restarting ADB server...
adb kill-server
adb start-server

echo Reconnecting to %ip% on port 5555...
adb connect %ip%:5555

echo Done.
