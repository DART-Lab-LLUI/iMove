import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtMultimedia

import "."
import qml

Page {
    id: cameraPage

    property var cameraManager: Context.cameraManager
    
    property bool preview: cameraManager.preview

    padding: Units.smallSpacing

    header: DynToolBar { 
        padding: 5
        Material.background: appSettings.colors.subBarBackground
        Material.foreground: appWindow.Material.foreground
        Label {
            text: "Cameras"
        }
        ToolButton {
            id: refreshCamerasButton
            icon.name: "view-refresh"
            text: "Refresh"
            onClicked: {
                cameraManager.scanCameras()
            }
        }
        Switch {
            id: previewToggle
            text: "Preview"
            icon.name: "preview-render-on"
            checked: cameraManager.preview
            onClicked: {
                if(cameraManager.recording) {
                    checked = false
                } else {
                    if(checked) {
                        cameraManager.preview = true
                    } else {
                        cameraManager.preview = false
                    }
                }
            }
        }
        ToolSeparator {}
    }
    GridView {
        id: cameraGrid
        anchors.fill: parent
        model: cameraManager.devices
        cellWidth: appSettings.gridDelegateSize*1.5
        cellHeight: cellWidth
        delegate: ItemDelegate {
                id: cameraItem
                width: GridView.view.cellWidth
                height: width
                property var delegateModel: modelData
                contentItem: Page {
                    padding: Units.smallSpacing
                    Material.elevation: 3
                    anchors.fill: parent
                    anchors.margins: Units.smallSpacing
                    Connections {
                        target: cameraManager
                        function onPreviewChanged() {
                            if(cameraManager.preview) {
                                modelData.videoSink = cameraItemVideoOutput
                            } else {
                                modelData.videoSink = null
                            }
                        }
                    }
                    header: ImageView {
                        id: cameraItemVideoOutput
                        height: (1/2) * parent.width
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
                                text: modelData.fps + ' fps'
                                Layout.maximumWidth: parent.width - itemName.width - Units.largeSpacing
                                clip: true
                            }
                        }
                        RowLayout {
                            Label {
                                id: itemIdx
                                text: "ID: " + modelData.idx
                            }
                            Label {
                                id: itemId
                                text: ' @ ' + modelData.id
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            Label {
                                text: modelData.width + ' x ' + modelData.height + ' ' + modelData.pixelFormat
                                Layout.maximumWidth: parent.width - itemId.width - Units.largeSpacing
                                clip: true
                            }
                        }
                        RowLayout {
                            ComboBox {
                                id: formatComboBox
                                Layout.preferredWidth: parent.width * 2/3
                                Layout.preferredHeight: connectSwitch.height
                                model: modelData.cameraFormatsString
                                onActivated: {
                                    modelData.cameraFormat = modelData.cameraFormats[currentIndex]
                                }
                                Component.onCompleted: {
                                    modelData.cameraFormat = modelData.cameraFormats[currentIndex]
                                }
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            Switch {
                                id: connectSwitch
                                checked: modelData.connected
                                onClicked: {
                                    if(checked)
                                        modelData.connected = true
                                    else
                                        modelData.connected = false
                                }
                            }
                        }
                    }
                    footer: DynToolBar { 
                        Material.background: appSettings.colors.subBarBackground
                        Material.foreground: appWindow.Material.foreground
                        ToolButton {
                            id: cameraIdButton
                            icon.name: "input-num-on"
                            text: "ID"
                            enabled: modelData.connected
                            onClicked: {
                                idDialog.open()
                            }
                        }
                        ToolButton {
                            id: cameraRenameButton
                            icon.name: "chronometer"
                            text: "FPS"
                            enabled: modelData.connected
                            onClicked: {
                                console.log("FPS")
                            }
                        }
                        ToolButton {
                            id: cameraConfigure
                            icon.name: "adjustlevels"
                            text: "Configure"
                            enabled: modelData.connected
                            onClicked: {
                                console.log("Configure")
                            }
                        }
                    }
            }
            Dialog {
                id: idDialog
                anchors.centerIn: parent
                width: cameraItem.width - Units.smallSpacing
                height: cameraItem.height - Units.smallSpacing
                modal: false
                ButtonGroup {
                    id: idButtonGroup
                }
                contentItem: Page {
                    anchors.fill: parent
                    Material.background: appSettings.colors.subBarBackground
                    Material.foreground: appWindow.Material.foreground
                    padding: 0
                    GridView {
                        id: idGrid
                        anchors.fill: parent
                        model: {
                            return [...Array(9)].map((_, i) => 1 + i)
                        }
                        cellWidth: idDialog.width / 3
                        cellHeight: idDialog.height / 3
                        delegate: ItemDelegate {
                                id: cameraIdItem
                                width: GridView.view.cellWidth
                                height: width
                                contentItem: ToolButton {
                                    id: idToolButton
                                    anchors.fill: parent
                                    flat: true
                                    enabled: delegateModel.idx != modelData
                                    highlighted: {
                                        return cameraManager.cameraIDs.includes(modelData)
                                    }
                                    text: modelData
                                    font.pointSize: 20
                                    onClicked: {
                                        delegateModel.idx = modelData
                                        idDialog.accept()
                                    }
                                }
                        }
                    }
                }
            }
        }
    }
}
