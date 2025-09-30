import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtMultimedia
import QtCharts

import "."
import qml

Page {
    id: recordingPage
    
    property var sensorManager: Context.sensorManager
    property var cameraManager: Context.cameraManager
    property var projectManager: Context.projectManager
     
    padding: Units.smallSpacing
    
    header: DynToolBar { 
        padding: 5
        Material.background: appSettings.colors.subBarBackground
        Material.foreground: appWindow.Material.foreground
        Label {
            id: pageLabel
            text: "Recording"
        }
        Item {
            width: Units.largeSpacing
        }
        ToolSeparator {}
        ComboBox {
            id: taskComboBox
            height: pageLabel.height + Units.largeSpacing
            implicitContentWidthPolicy: ComboBox.WidestText
            implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset, implicitContentWidth + leftPadding + rightPadding) + 10
            model: projectManager.sessionTaskNames()
            displayText: "Task: " + currentText
            onActivated: {
                projectManager.selectedTask = currentValue
            }
        }
        ToolButton {
            id: estimateButton
            text: "Synchronize"
            icon.name: "media-random-albums-amarok"
            onClicked: {
                cameraManager.synchronize()
            }
            enabled: !cameraManager.synchronizing
        }
        BusyIndicator {
            height: estimateButton.implicitHeight
            running: cameraManager.synchronizing
        }
    }
    
    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical
        Page {
            id: cameraPreview
            SplitView.fillWidth: true
            SplitView.preferredHeight: parent.height * 3/7
            GridView {
                id: cameraGrid
                anchors.fill: parent
                model: cameraManager.connectedDevices
                cellWidth: appSettings.gridDelegateSize*1.5
                cellHeight: cellWidth
                delegate: ItemDelegate {
                        id: cameraItem
                        width: GridView.view.cellWidth
                        height: width
                        contentItem: Page {
                        padding: Units.smallSpacing
                        Material.elevation: 3
                        anchors.fill: parent
                        anchors.margins: Units.smallSpacing
                        Connections {
                            target: cameraManager
                            function onRecordingChanged() {
                                if(cameraManager.recording) {
                                    modelData.videoSink = cameraItemVideoOutput
                                } else {
                                    modelData.videoSink = null
                                }
                            }
                        }
                        header: ImageView {
                            id: cameraItemVideoOutput
                            height: (4/5) * parent.width
                        } 
                        ColumnLayout {
                            anchors.fill: parent
                            RowLayout {
                                Label {
                                    text: modelData.name
                                    font.bold: true
                                }
                                Item {
                                    Layout.fillWidth: true
                                }
                            }
                            RowLayout {
                                Label {
                                    text: modelData.id
                                }
                                Item {
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
        Page {
            id: sensorPreview
            SplitView.fillWidth: true
            SplitView.preferredHeight: parent.height * 3/7
            ButtonGroup {
                id: gyAcButtonGroup
            }
            ButtonGroup {
                id: axisButtonGroup
                exclusive: false
            }
            header: DynToolBar {
                id: sensorPreviewControls
                padding: 5
                Material.background: appSettings.colors.subBarBackground
                Material.foreground: appWindow.Material.foreground
                ToolButton {
                    id: gyroButton
                    text: "G"
                    checkable : true
                    checked: true
                    ButtonGroup.group: gyAcButtonGroup
                    onClicked: {
                        if(checked) {
                            sensorChart.clearData()
                            yAxis.min = -190
                            yAxis.max = 190
                        }
                    }
                }
                ToolButton {
                    id: accelButton
                    text: "A"
                    checkable : true
                    checked: false
                    ButtonGroup.group: gyAcButtonGroup
                    onClicked: {
                        if(checked) {
                            sensorChart.clearData()
                            yAxis.min = -20
                            yAxis.max = 20
                        }
                    }
                }
                ToolSeparator {}
                ToolButton {
                    id: xButton
                    text: "X"
                    checkable : true
                    checked: true
                    ButtonGroup.group: axisButtonGroup
                    onClicked: {
                        if(!checked)
                            orientXLine.clear()
                    }
                }
                ToolButton {
                    id: yButton
                    text: "Y"
                    checkable : true
                    checked: true
                    ButtonGroup.group: axisButtonGroup
                    onClicked: {
                        if(!checked)
                            orientYLine.clear()
                    }
                }
                ToolButton {
                    id: zButton
                    text: "Z"
                    checkable : true
                    checked: true
                    ButtonGroup.group: axisButtonGroup
                    onClicked: {
                        if(!checked)
                            orientZLine.clear()
                    }
                }
                ToolSeparator {}
                ComboBox {
                    id: sensorComboBox
                    property var previousValue: null
                    height: gyroButton.height - 5 
                    implicitContentWidthPolicy: ComboBox.WidestText
                    model: sensorManager.connectedDevices
                    textRole: "name"
                    onActivated: {
                        if(previousValue != null) {
                            previousValue.measurementChanged.diconnect(sensorChart.appendData)
                        }
                        sensorChart.clearData()
                        previousValue = currentValue
                        currentValue.measurementChanged.connect(sensorChart.appendData)
                    }
                    Component.onCompleted: {
                        if (currentValue != null && currentValue.trim().length > 0) {
                            if(previousValue != null) {
                                previousValue.measurementChanged.diconnect(sensorChart.appendData)
                                sensorChart.clearData()
                            }
                            previousValue = currentValue
                            currentValue.measurementChanged.connect(sensorChart.appendData)
                        }
                    }
                }
            }
            ChartView {
                id: sensorChart

                property real xAxisWindow: 1000
                property var firstTimestamp: null
                property var secondTimestamp: null

                title: "Sensor"
                anchors.fill: parent
                antialiasing: true
                axes: [
                    ValueAxis{
                        id: xAxis
                        min: 0
                        max: 10
                    },
                    ValueAxis{
                        id: yAxis
                        min: -190
                        max: 190
                    }
                ]
                LineSeries {
                    id: orientXLine
                    name: gyroButton.checked ? "Orientation X" : "Acceleration X"
                    axisX: xAxis
                    axisY: yAxis
                }
                LineSeries {
                    id: orientYLine
                    name: gyroButton.checked ? "Orientation Y" : "Acceleration Y"
                    axisX: xAxis
                    axisY: yAxis
                }
                LineSeries {
                    id: orientZLine
                    name: gyroButton.checked ? "Orientation Z" : "Acceleration Z"
                    axisX: xAxis
                    axisY: yAxis
                }
                function appendData(sensor_data) {
                    let vec_3d = [0, 0, 0]
                    if(gyroButton.checked)
                        vec_3d = [sensor_data.eulerX, sensor_data.eulerY, sensor_data.eulerZ]
                    else if(accelButton.checked)
                        vec_3d = [sensor_data.accelX, sensor_data.accelY, sensor_data.accelZ]
                        
                    
                    // x axis bounds
                    if(sensorChart.firstTimestamp === null)
                        sensorChart.firstTimestamp = sensor_data.timestamp
                    else if(sensorChart.secondTimestamp === null) {
                        sensorChart.secondTimestamp = sensor_data.timestamp
                        sensorChart.xAxisWindow = (sensorChart.secondTimestamp - sensorChart.firstTimestamp) * 400
                    }
                    if (sensor_data.timestamp > xAxis.max) {
                        xAxis.max = sensor_data.timestamp
                    }
                    xAxis.min = xAxis.max - sensorChart.xAxisWindow

                    if(xButton.checked) {
                        orientXLine.append(sensor_data.timestamp, vec_3d[0]);
                        removeOldData(orientXLine)
                    }
                    if(yButton.checked) {
                        orientYLine.append(sensor_data.timestamp, vec_3d[1]);
                        removeOldData(orientYLine)
                    }
                    if(zButton.checked) {
                        orientZLine.append(sensor_data.timestamp, vec_3d[2]);
                        removeOldData(orientZLine)
                    }
                } 
                function removeOldData(lineSeries) {
                    while (lineSeries.count > 0 && lineSeries.at(0).x < xAxis.min) {
                        lineSeries.remove(0)
                    }
                }
                function clearData() {
                    orientXLine.clear()
                    orientYLine.clear()
                    orientZLine.clear()
                    sensorChart.firstTimestamp = null
                    sensorChart.secondTimestamp = null
                }
            }
        }
        Page {
            id: timeline
            SplitView.fillWidth: true
            SplitView.preferredHeight: parent.height * 1/7
            header: ToolBar { 
                padding: 5
                Material.background: appSettings.colors.subBarBackground
                Material.foreground: appWindow.Material.foreground
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    // ToolButton {
                    //     id: pauseRecordButton
                    //     icon.name: "media-playback-pause"
                    //     enabled: cameraManager.recordingState == CameraManager.RecordingState.Started || cameraManager.recordingState == CameraManager.RecordingState.Resumed
                    //     onClicked: {
                    //         cameraManager.recordingState = CameraManager.RecordingState.Paused
                    //     }
                    // }
                    // ToolButton {
                    //     id: resumeRecordButton
                    //     icon.name: "media-playback-start"
                    //     enabled: cameraManager.recordingState == CameraManager.RecordingState.Paused
                    //     onClicked: {
                    //         cameraManager.recordingState = CameraManager.RecordingState.Resumed
                    //     }
                    // }
                    ToolButton {
                        id: stopRecordButton
                        icon.name: "media-playback-stop"
                        enabled: cameraManager.recordingState != CameraManager.RecordingState.Stopped
                        onClicked: {
                            cameraManager.recordingState = CameraManager.RecordingState.Stopped
                            sensorManager.recordingState = CameraManager.RecordingState.Stopped
                        }
                    }
                    ToolButton {
                        Material.foreground: Material.Red
                        id: startRecordButton
                        icon.name: "media-record"
                        enabled: cameraManager.recordingState == CameraManager.RecordingState.Stopped
                        onClicked: {
                            cameraManager.recordingState = CameraManager.RecordingState.Started
                            sensorManager.recordingState = CameraManager.RecordingState.Started
                        }
                    }
                    ToolSeparator {}
                    ToolButton {
                        id: startTrialButton
                        enabled: (cameraManager.recordingState == CameraManager.RecordingState.Started || cameraManager.recordingState == CameraManager.RecordingState.Resumed) && cameraManager.trialState == CameraManager.RecordingState.Stopped
                        icon.name: "keyframe-record"
                        onClicked: {
                            cameraManager.trialState = CameraManager.RecordingState.Started
                        }
                    }
                    ToolButton {
                        id: stopTrialButton
                        enabled: (cameraManager.recordingState == CameraManager.RecordingState.Started || cameraManager.recordingState == CameraManager.RecordingState.Resumed) && cameraManager.trialState == CameraManager.RecordingState.Started
                        icon.name: "keyframe-disable"
                        onClicked: {
                            cameraManager.trialState = CameraManager.RecordingState.Stopped
                        }
                    }
                }
            }

            ListView {
                id: trialList
                anchors.fill: parent
                model: cameraManager.trials
                delegate: ItemDelegate {
                    id: trialItem
                    width: parent.width
                    text: 'Trial ' + modelData.id.toString().padStart(4, ' ') + '          |' + modelData.durationSec.toString().padStart(10, ' ')
                    icon.name: "media-optical-video"
                }
                ScrollIndicator.vertical: ScrollIndicator { }
            }
        }
    }
}
