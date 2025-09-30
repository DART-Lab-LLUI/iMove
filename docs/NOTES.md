# How to run
- Install uv.
- Install external dependencies like ffmpeg
```
uv run python -m imove
```

# Generate RC files
```shell
uv run pyside6-rcc  --no-zstd resources.qrc -o resources.py
```
    
# Tests
## Virtual Cameras
You can use `v4l2loopback` to load multiple video files as virtual cameras. First make sure v4l2loopback module is installed.

```
 sudo modprobe v4l2loopback video_nr=3,4,5 card_label="pose_camera1","pose_camera2","pose_camera3"
```
Then run the following (this is for fish shell):
```
for i in (seq 1 3); python file2webcam.py /home/arashsm79/Playground/llui_idrink/tests/test_files/calibration/ca
m$i.mp4  --device /dev/video(math $i+2) &; end;
```

```
 kill -9 (seq 1 3 | sed 's/^/%/')

```

## Bluetooth
To get the bluetooth working on Linux inside a distrobox Ubuntu env
1) First `enter` the box with the `--root` option.
2) Start the dbus daemon:
```
sudo dbus-daemon --system --nofork --nopidfile --syslog --print-address
```
3) Symlink the system dbus socket to the one local to your conda env:
```
ln -s /var/run/dbus/system_bus_socket /home/arashsm79/.miniforge3/envs/idrink/var/run/dbus/system_bus_socket 
```
4) Start the bluetooth daemon:
```
sudo bluetoothd &
```
5) Check and make sure the connection is working:
```
dbus-send --system \
        --dest=org.bluez \
        --print-reply \
        / \
        org.freedesktop.DBus.ObjectManager.GetManagedObjects
```

Packages that might be necessary:
```
sudo apt install libbluetooth-dev libbluetooth3 libdbus1.0-cil-dev bluez bluez-tools dbus
```

Make sure set the cap_net_admin capabilities for the python interpreter in linux:
```
sudo setcap 'CAP_NET_ADMIN+eip' (which (readlink (which python)))
```

## OpenCV
Considering a 60 FPS camera
- normal reads (without the grab+retrive) mechanism is around 16 ms
- grab takes 8 ms if it is immedietly followed by a retrieve.
- if multiple grabs happen without a retrieve in between then the grab after the first grab would take 16 ms

- Writing the frame to shared memory in reader is negligible.

## TODO:
### Calibration:
- reprojection error for each camera
- a list of previous calibration files with the id of the session, patient and date
- a calibrate button to use the recording
- tell the user if the current session doesnt have calibration recording
- show charuku cornes in the previw of recording page if task is calibration
- 3d scene of camera positions

