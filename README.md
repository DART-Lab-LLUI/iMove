
<div align="center">

# iMove - instrumented Movement analysis

  <img src = "https://github.com/user-attachments/assets/c5e3006e-18f3-41f6-9f53-9c1ad0b46d42" width = "256">
  
</div>

<div align="center">
  
  ![python](https://img.shields.io/badge/Python-98%25-blue)
  [![Feedback welcome](https://img.shields.io/badge/feedback-welcome-green)](https://github.com/DART-Lab-LLUI/iMove/discussions/2)
  
</div>

**iMove (intrumented Movement) is a free and open-source biomechanics and movement analysis tool using low-budget consumer-grade devices (webcams, IMUs, phones) for clinical use, scientific reasearch, and training.**


# Feedback and Suggestions
Please consider leaving your comments on [our discussion page](https://github.com/DART-Lab-LLUI/iMove/discussions/2). 


# Core features
iMove is written in Python and uses Qt6 QML for it's responsive, tablet friendly, and cross-platform user interface. iMove stands on the shoulders of giants and employs other fantastic open-source software like FFmpeg, OpenCV, Anipose, and more. 

## IMU Sensor
Detect and interface with IMU sensors (here [Movella DOT](https://www.movella.com/products/wearables/movella-dot)) using the bluetooth protocol. A plugin system to add support for other sensors is also underway.
<div align="center">
    <img src="https://github.com/user-attachments/assets/fb52a710-6d59-4e5b-8689-45432c3ec5b1" width="70%">
    <br>
    <sup>Scanning for nearby bluetooth sensors and connecting to them.</sup>
</div>

## Subject and Session Management
[Motion-BIDS](https://www.nature.com/articles/s41597-024-03559-8) data structure for storing the measurements.
<div align="center">
    <img src="https://github.com/user-attachments/assets/42f4fcea-3fcf-4f42-99c4-82dc915441fb" width="70%">
    <br>
    <sup>BIDS-based subject and session management.</sup>
</div>

## Multi Camera Setup
Easily setup a multi camera capture session by assigning proper IDs to cameras, setting the camera specific supported frame rate and resolution, and configuring auto fucos, exposure, and other camera parameters.
<div align="center">
    <img src="https://github.com/user-attachments/assets/921b6816-a2d6-4ef5-8f98-2ef9945b9a30" width="70%">
    <br>
    <sup>Auto detection of cameras, ID assignment, and configuration.</sup>
</div>

## Recording
### Recording Calibration
Record calibration videos and see a preview of your calibration board live.
<div align="center">
    <img src="https://github.com/user-attachments/assets/f65e070b-cff1-43fe-9c5c-3be231cb2f13" width="70%">
    <br>
    <sup>Recording calibration videos while receiving feedback on how much of the field of view of each camera has been covered.</sup>
</div>

### Recording Movement
Record the subject's movements across tirals and inspect the sensor movement in real time.
<div align="center">
    <img src="https://github.com/user-attachments/assets/9b951888-af4f-435c-9f72-edb21186f574" width="70%">
    <br>
    <sup>Recording a drinking task with live preview of the cameras and the IMU sensor.</sup>
</div>

## Calibration
Reuse calibration across sessions and get a preview of the cameras that were used for the calibration along with their IDs.
<div align="center">
    <img src="https://github.com/user-attachments/assets/be0684f3-a191-41de-b6c5-96c03bf9c6d7" width="70%">
    <br>
    <sup>Avoid recalibration by using the calibration data from previous sessions.</sup>
</div>

## Synchronization
Synchronize low-cost consumer-grade cameras to within 8ms of one another without any special hardware. 

<div align="center">
    <img src="https://github.com/user-attachments/assets/0b2f962c-bab4-4369-a7cb-79be181d6c4d" width="70%">
    <br>
    <sup>Measuring multicam software synchronization.</sup>
</div>

<div align="center">

https://github.com/user-attachments/assets/7c0ed8e0-5394-4b6b-85e1-4bf2e0631885

</div>

<div align="center">
    <img src="https://github.com/user-attachments/assets/ded8a0e5-f58d-4f67-87a9-a99f2b73a493" width="70%">
    <br>
    <sup>Example of video frames form multiple cameras across time.</sup>
</div>


## Movement Analysis
<div align="center">
    <img src="https://github.com/user-attachments/assets/78515ad6-eab4-4a6b-8281-74779d226015" width="70%">
    <br>
    <sup>Example of video frames form multiple cameras across time.</sup>
</div>

https://github.com/user-attachments/assets/e0ab4f91-250c-4514-bdc6-1adda804de4e

