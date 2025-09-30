import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import "."
import qml

Page {
    id: sensorPage
    
    property var sensorManager: Context.sensorManager

    padding: Units.smallSpacing

    header: DynToolBar { 
        padding: 5
        Material.background: appSettings.colors.subBarBackground
        Material.foreground: appWindow.Material.foreground
        Label {
            text: "Sensors"
        }
        ToolButton {
            id: startScanButton
            icon.name: "network-wireless-on"
            text: "Start Scan"
            enabled: !sensorManager.scanning
            onClicked: sensorManager.scanStarted()
        }
        ToolButton {
            id: stopScanButton
            icon.name: "network-wireless-off"
            text: "Stop Scan"
            enabled: sensorManager.scanning
            onClicked: sensorManager.scanStopped()
        }
        ToolButton {
            id: refreshButton
            icon.name: "view-refresh"
            text: "Refresh"
            onClicked: sensorManager.refreshStarted()
        }
    }
    GridView {
        id: sensorGrid
        anchors.fill: parent
        model: sensorManager.devices
        cellWidth: appSettings.gridDelegateSize
        cellHeight: cellWidth
        delegate: ItemDelegate {
                id: sensorItem
                width: GridView.view.cellWidth
                height: width
                InputDialog {
                    id: renameDialog
                    dialogTitle: "Rename Sensor Tag"
                    dialogTitleIconName: "text-field-framed"
                    placeholderText: modelData.tag
                    enteredTextValidator: RegularExpressionValidator { regularExpression: /[\w.\-]{1,16}/ }
                    anchors.centerIn: parent
                    width: parent.width - Units.veryLargeSpacing
                    height: parent.height - Units.veryLargeSpacing
                    onAccepted: {
                        modelData.tagRenameRequested(renameDialog.enteredText)
                    }
                }
                contentItem: Page {
                padding: Units.smallSpacing
                Material.elevation: 3
                anchors.fill: parent
                anchors.margins: Units.smallSpacing
                header: Image {
                    id: sensorItemImage
                    height: (1/3) * parent.width
                    source: "qrc:/icons/llui/dot.png"
                    fillMode: Image.PreserveAspectFit
                } 
                ColumnLayout {
                    anchors.fill: parent
                    RowLayout {
                        Layout.maximumWidth: parent.width
                        Label {
                            id: itemName
                            text: modelData.name
                            font.bold: true
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            text: modelData.tag
                            Layout.maximumWidth: parent.width - itemName.width - Units.largeSpacing
                            clip: true
                        }
                    }
                    RowLayout {
                        Layout.maximumWidth: parent.width
                        Label {
                            id: itemAddress
                            text: modelData.address
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            text: modelData.firmwareVersion
                            Layout.maximumWidth: parent.width - itemAddress.width - Units.largeSpacing
                            clip: true
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                    RowLayout {
                        Layout.maximumWidth: parent.width
                        IconLabel {
                            text: modelData.batteryLevel + "%"
                            icon.name: "battery-100"
                            font.pixelSize: Units.gu(0.7)
                            opacity: modelData.connected ? 1 : appSettings.disabledOpacity
                            Layout.maximumWidth: parent.width/3
                            clip: true
                        }
                        IconLabel {
                            text: modelData.signalStrength + "dBm"
                            icon.name: "network-wireless-bluetooth"
                            font.pixelSize: Units.gu(0.7)
                            opacity: modelData.connected ? 1 : appSettings.disabledOpacity
                            Layout.maximumWidth: parent.width/3
                            clip: true
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Switch {
                            checked: modelData.connected
                            onClicked: {
                                if(checked) {
                                    sensorManager.scanStopped()
                                    modelData.connectToSensor()
                                } else {
                                    modelData.disconnectRequested()
                                }
                            }
                        }
                    }
                }
                footer: DynToolBar { 
                    Material.background: appSettings.colors.subBarBackground
                    Material.foreground: appWindow.Material.foreground
                    ToolButton {
                        id: sensorIdentifyButton
                        icon.name: "crosshairs"
                        text: "Identify"
                        enabled: modelData.connected
                        onClicked: {
                            modelData.identifyRequested() 
                        }
                    }
                    ToolButton {
                        id: sensorRenameButton
                        icon.name: "text-field-framed"
                        text: "Rename"
                        enabled: modelData.connected
                        onClicked: {
                            renameDialog.open()
                        }
                    }
                    ToolButton {
                        id: sensorPowerOffButton
                        icon.name: "system-shutdown"
                        text: "Power Off"
                        enabled: modelData.connected
                        onClicked: {
                            modelData.shutdownRequested() 
                        }
                    }
                }
            }
        }
    }
}
