import QtQuick
import QtCore
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs

import "."
import qml

ApplicationWindow {
    id: appWindow
    visible: true
    width: Screen.width
    height: Screen.height
    title: "iMove"
    
    property var projectManager: Context.projectManager
    property var cameraManager: Context.cameraManager
    
    header: DynToolBar {
        Material.background: appSettings.colors.barBackground
        Material.foreground: appWindow.Material.foreground
        Material.elevation: 2
        ToolButton {
            icon.name: "application-menu"
            visible: appSettings.isMobile
            onClicked: {
                if(sideBarNav.closed)
                    sideBarNav.open()
                else
                    sideBarNav.close()
            }
        }
        ToolButton {
            icon.name: "document-new"
            text: "New Project"
            onClicked: {
                newProjectFilePicker.open()
            }
        }
        ToolButton {
            icon.name: "document-open-folder"
            text: "Open Project"
            onClicked: {
                openProjectFilePicker.open()
            }
        }
        ToolSeparator {}
        ToolButton {
            icon.name: "list-add-user"
            text: "Add Subject"
            onClicked: {
                addSubjectDialog.open()
            }
        }
        ToolButton {
            icon.name: "mail-message-new-list"
            text: "Add Session"
            onClicked: {
                addSessionDialog.open()
            }
        }
        ToolSeparator {}
        // ToolButton {
        //     icon.name: "gnumeric-object-combo"
        //     text: "Processes"
        // }
        // ToolButton {
        //     icon.name: "view-list-tree"
        //     text: "File View"
        //     onClicked: Qt.callLater(Qt.quit)
        // }
        ToolButton {
            Material.foreground: Material.Red
            icon.name: "application-exit"
            text: "Exit"
            onClicked: Qt.callLater(Qt.quit)
        }
    } 
    
    SideBar {
        id: sideBarNav
        Material.background: appSettings.colors.sideBackground
        implicitWidth: appSettings.isMobile ? (1/2) * parent.width : (1/5) * parent.width
        implicitHeight: parent.height
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }
    
    StackLayout {
        id: mainContentStack
        anchors.left: sideBarNav.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        
        SensorsPage {
            id: sensorPage
        }
        CamerasPage {
            id: cameraPage
        }
        CalibrationPage {
            id: calibrationPage
        }
        RecordingPage {
            id: recordingPage
        }
        ResultsPage {
            id: resultsPage
        }
    }
    
    SettingsPage {
        id: settingsPopup
        anchors.centerIn: Overlay.overlay
        width: 2/3 * parent.width
        height: 2/3 * parent.height
    }
    HelpPage {
        id: helpPopup
        anchors.centerIn: Overlay.overlay
        width: 2/3 * parent.width
        height: 2/3 * parent.height
    }
    
    Settings {
        id: appSettings
    }
    
    FolderDialog {
        id: newProjectFilePicker
        currentFolder: StandardPaths.standardLocations(StandardPaths.HomeLocation)[0]
        onAccepted: projectManager.createProject(selectedFolder.toString().replace(/^(file:\/{2})/,""))
    }

    FolderDialog {
        id: openProjectFilePicker
        currentFolder: StandardPaths.standardLocations(StandardPaths.HomeLocation)[0]
        onAccepted: projectManager.openProject(selectedFolder.toString().replace(/^(file:\/{2})/,""))
    }

    InputDialog {
        id: addSubjectDialog
        dialogTitle: "Add Subject"
        dialogTitleIconName: "list-add-user"
        acceptText: "Add"
        anchors.centerIn: parent
        modal: true
        width: parent.width * 1/3
        height: parent.height * 1/3
        onAccepted: {
            projectManager.addSubject(enteredText)
        }
    }

    InputDialog {
        id: addSessionDialog
        dialogTitle: "Add Session"
        dialogTitleIconName: "mail-message-new-list"
        acceptText: "Add"
        anchors.centerIn: parent
        modal: true
        width: parent.width * 1/3
        height: parent.height * 1/3
        onAccepted: {
            projectManager.addSession(enteredText)
        }
    }
    
    footer: StatusBar {
        id: statusBar
        Material.background: appSettings.colors.statusBarBackground
        Material.foreground: appWindow.Material.foreground
        height: Units.gu(0.8)
        Connections {
            target: cameraManager
            function onRecordingChanged() {
                if(cameraManager.recording) {
                    statusBar.Material.background = Material.Red
                } else {
                    statusBar.Material.background = appSettings.colors.statusBarBackground
                }
            }
            function onRecordingTrialChanged() {
                if(cameraManager.recordingTrial) {
                    statusBar.Material.background = Material.Yellow
                } else {
                    statusBar.Material.background = Material.Red
                }
            }
        }
    }
}
