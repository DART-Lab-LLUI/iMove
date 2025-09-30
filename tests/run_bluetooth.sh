#!/usr/bin/bash
sudo dbus-daemon --system --nofork --nopidfile --syslog --print-address > /dev/null 2>&1 &
sudo bluetoothd > /dev/null 2>&1 &
