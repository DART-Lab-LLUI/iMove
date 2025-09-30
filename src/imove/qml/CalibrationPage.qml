import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtMultimedia
import QtCharts

import "."
import qml

Page {
    id: calibrationPage
    
    property var sensorManager: Context.sensorManager
    property var cameraManager: Context.cameraManager
    property var projectManager: Context.projectManager
    property var calibrationManager: Context.calibrationManager
     
    property var connectedCameras: cameraManager.devices.filter(camera => camera.connected)
    
    
    header: DynToolBar { 
        padding: 5
        Material.background: appSettings.colors.subBarBackground
        Material.foreground: appWindow.Material.foreground
        Label {
            id: pageLabel
            text: "Calibration"
        }
        Item {
            width: Units.largeSpacing
        }
        ToolButton {
            id: calibrateButton
            text: "Calibrate"
            icon.name: "autocorrection"
            onClicked: {
                calibrationManager.startCalibration()
            }
            enabled: !calibrationManager.isCalibrating
        }
        BusyIndicator {
            height: calibrateButton.implicitHeight
            running: calibrationManager.isCalibrating
        }
    }
    
    SplitView {
        padding: 0
        anchors.fill: parent
        orientation: Qt.Vertical
        Page {
            id: cameraInfo
            SplitView.fillWidth: true
            SplitView.preferredHeight: parent.height * 1/2
            padding: Units.smallSpacing
            GridView {
                id: cameraGrid
                anchors.fill: parent
                model: calibrationManager.calibratedCameras
                cellWidth: appSettings.gridDelegateSize*1.5
                cellHeight: cellWidth * 1.2
                delegate: ItemDelegate {
                        id: cameraItem
                        width: GridView.view.cellWidth
                        height: GridView.view.cellHeight
                        contentItem: Page {
                            padding: Units.smallSpacing
                            Material.elevation: 3
                            anchors.fill: parent
                            anchors.margins: Units.smallSpacing
                            header: ImageView {
                                id: cameraItemVideoOutput
                                height: (3/5) * parent.width
                                image: modelData.preview
                            } 
                            ColumnLayout {
                                anchors.fill: parent
                                Label {
                                    text: 'cam-' + modelData.idx
                                    font.bold: true
                                }
                                Label {
                                    text: "Error: " + modelData.error
                                    Layout.maximumWidth: parent.width
                                    wrapMode: Text.WrapAnywhere
                                }
                                Label {
                                    text: "R: " + modelData.rotation
                                    Layout.maximumWidth: parent.width
                                    wrapMode: Text.WrapAnywhere
                                }
                                Label {
                                    text: "D: " + modelData.distortions
                                    Layout.maximumWidth: parent.width
                                    wrapMode: Text.WrapAnywhere
                                }
                                Label {
                                    text: "T: " + modelData.translation
                                    Layout.maximumWidth: parent.width
                                    wrapMode: Text.WrapAnywhere
                                }
                                Label {
                                    text: "Mat: " + modelData.matrix
                                    Layout.maximumWidth: parent.width
                                    wrapMode: Text.WrapAnywhere
                                }
                            }
                        }
                }
            }
        }
        Page {
            Material.background: appSettings.colors.barBackground
            id: calibList
            SplitView.fillWidth: true
            SplitView.preferredHeight: parent.height * 1/2
            property int pad: Units.gu(0.76)
            header: ToolBar { 
                implicitWidth: parent.width
                padding: 5
                Material.background: appSettings.colors.subBarBackground
                Material.foreground: appWindow.Material.foreground
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Calibration File"
                }
            }
            
            TreeView {
                id: fileTree
                implicitHeight: parent.height
                implicitWidth: parent.width
                property bool expanded: false
                property int lastIndex: -1
                clip: true
                model: projectManager.fileSystemModel
                rootIndex: projectManager.projectIndex
                selectionModel: ItemSelectionModel {}
                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.StopAtBounds
                delegate: TreeViewDelegate {
                    id: treeDelegate
                    implicitHeight: label.implicitHeight * 2.5
                    implicitWidth: fileTree.width

                    // provided by model
                    required property int index
                    required property url filePath
                    required property string fileName
                    // required property var fileInfo
                    padding: calibList.pad
                    
                    Component.onCompleted: {
                        if(treeDelegate.fileName.startsWith("sub-") && hasChildren){
                            fileTree.toggleExpanded(row)
                        } else if(treeDelegate.fileName.startsWith("ses-")) {
                            var ses_id = treeDelegate.filePath.toString().match("/ses-([a-zA-Z0-9_]+)")[1]
                            var sub_id = treeDelegate.filePath.toString().match("/sub-([a-zA-Z0-9_]+)")[1]
                            if(projectManager.selectedSession == ses_id && projectManager.selectedSubject == sub_id)
                                fileTree.lastIndex = index
                                if(treeDelegate.fileName.startsWith("ses-")) {
                                    var ses_id = treeDelegate.filePath.toString().match("/ses-([a-zA-Z0-9_]+)")[1]
                                    var sub_id = treeDelegate.filePath.toString().match("/sub-([a-zA-Z0-9_]+)")[1]
                                    calibrationManager.selectCalibration(sub_id, ses_id)
                                }
                        }
                    }
                    
                    property Animation indicatorAnimation: NumberAnimation {
                        target: indicator
                        property: "rotation"
                        from: treeDelegate.expanded ? 0 : 90
                        to: treeDelegate.expanded ? 90 : 0
                        duration: 100
                        easing.type: Easing.OutQuart
                    }
                    onExpandedChanged: indicator.rotation = expanded ? 90 : 0
                    indicator: IconLabel {
                        property bool expandible: treeDelegate.fileName.startsWith("sub-") && hasChildren
                        id: indicator
                        x: padding + (depth * indentation)
                        anchors.verticalCenter: parent.verticalCenter
                        text: expandible ? "▶" : "    "
                        TapHandler {
                            onSingleTapped: {
                                if(expandible)
                                    fileTree.toggleExpanded(row)
                            }
                        }
                    }
                    contentItem: IconLabel {
                        id: label
                        alignment:  Qt.AlignLeft
                        anchors.verticalCenter: parent.verticalCenter
                        text: treeDelegate.fileName.startsWith("ses-") ? "  " + treeDelegate.fileName + " calibration" : "  " + treeDelegate.fileName
                        icon.name: treeDelegate.fileName.startsWith("sub-") ? "im-user" : treeDelegate.fileName.startsWith("ses-") ? "tool-measure" : ""
                    }

                    background: Pane {
                        Material.elevation: 3
                        background: Rectangle {
                            anchors.fill: parent
                            color: treeDelegate.index == fileTree.lastIndex ? appSettings.colors.selection : (hoverHandler.hovered ? appSettings.colors.highlight : "transparent")
                            opacity: (treeDelegate.index % 2 !== 0) ? 0.3 : 0.1
                        }
                    }
                    HoverHandler {
                        id: hoverHandler
                    }

                    TapHandler {
                        onSingleTapped: {
                            fileTree.lastIndex = index
                            if(treeDelegate.fileName.startsWith("ses-")) {
                                var ses_id = treeDelegate.filePath.toString().match("/ses-([a-zA-Z0-9_]+)")[1]
                                var sub_id = treeDelegate.filePath.toString().match("/sub-([a-zA-Z0-9_]+)")[1]
                                calibrationManager.selectCalibration(sub_id, ses_id)
                            }
                        }
                    }
                }
                ScrollIndicator.vertical: ScrollIndicator { }
            }
        }
    }
}
