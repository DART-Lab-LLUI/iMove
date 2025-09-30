import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import "."

Page {
    id: root

    property bool closed: false  
    
    property real minWidth: Units.gu(3)
    property int pad: Units.gu(0.76)
    property var projectManager: Context.projectManager
    

    Connections {
        target: appSettings
        function onIsMobileChanged() {
            if(appSettings.isMobile) {
                closed = true
            } else {
                closed = false
            }
        }
    }
    function close() {
        closed = true
    }
    function open() {
        closed = false
    }
    width: closed ? minWidth : implicitWidth
    Behavior on width {
        NumberAnimation {
            easing.type: Easing.InOutQuad
        }
    }

    // The expandible list at the top
    header: Pane {
        id: expandibleList
        padding: 0
        width: parent.width
        Material.elevation: 3
        Column {
            width: parent.width
            ItemDelegate {
                width: parent.width
                contentItem: Row {
                    spacing: Units.gu(1)
                    anchors.fill: parent
                    anchors.verticalCenter: parent.verticalCenter
                    leftPadding: root.pad
                    IconLabel {
                        id: fileTreeExpandIcon
                        anchors.verticalCenter: parent.verticalCenter
                        icon.name: "expand-all"
                        icon.width: Units.gu(1.2)
                    }
                    IconLabel {
                        anchors.verticalCenter: parent.verticalCenter
                        icon.name: "system-switch-user"
                        alignment: Qt.AlignLeft
                        text: {
                            if(projectManager.selectedSession != null){
                                return "sub-" + projectManager.selectedSubject + "\n" + 'ses-' + projectManager.selectedSession
                            } else{
                                return "Select session"
                            }
                        }
                    }
                }
                onClicked: {
                    if(fileTree.expanded) {
                        fileTree.expanded = false
                        fileTreeExpandIcon.icon.name = "expand-all"
                    } else {
                        fileTree.expanded = true
                        fileTreeExpandIcon.icon.name = "collapse-all"
                    }
                }
            }
            TreeView {
                id: fileTree
                implicitHeight: 0.3 * root.height
                implicitWidth: parent.width
                property bool expanded: false
                property int lastIndex: -1
                visible: height > 0
                height: expanded ? implicitHeight : 0
                Behavior on height {
                    NumberAnimation {
                        easing.type: Easing.InOutQuad
                    }
                }
                clip: true
                model: projectManager.fileSystemModel
                rootIndex: projectManager.projectIndex
                selectionModel: ItemSelectionModel {}
                boundsBehavior: Flickable.StopAtBounds
                boundsMovement: Flickable.StopAtBounds
                delegate: TreeViewDelegate {
                    id: treeDelegate
                    implicitHeight: label.implicitHeight * 2.5
                    implicitWidth: root.width

                    // provided by model
                    required property int index
                    required property url filePath
                    required property string fileName
                    padding: root.pad
                    
                    Component.onCompleted: {
                        if(treeDelegate.fileName.startsWith("sub-") && hasChildren){
                            fileTree.toggleExpanded(row)
                        } else if(treeDelegate.fileName.startsWith("ses-")) {
                            var ses_id = treeDelegate.filePath.toString().match("/ses-([a-zA-Z0-9_]+)")[1]
                            var sub_id = treeDelegate.filePath.toString().match("/sub-([a-zA-Z0-9_]+)")[1]
                            if(projectManager.selectedSession == ses_id && projectManager.selectedSubject == sub_id)
                                fileTree.lastIndex = index
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
                        text: "  " + treeDelegate.fileName
                        icon.name: treeDelegate.fileName.startsWith("sub-") ? "im-user" : treeDelegate.fileName.startsWith("ses-") ? "labplot-edithlayout" : ""
                    }

                    background: Pane {
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
                                projectManager.selectSession(sub_id, ses_id)
                            } else if(treeDelegate.fileName.startsWith("sub-")) {
                                var sub_id = treeDelegate.filePath.toString().match("/sub-([a-zA-Z0-9_]+)")[1]
                                projectManager.selectSubject(sub_id)
                            }
                        }
                    }
                }
                ScrollIndicator.vertical: ScrollIndicator { }
            }
        }
    }
    
    // All the entries in the sidebar
    ColumnLayout {
        id: sideBarColumnLayout
        anchors.fill: parent
        ListView {
            id: sideBarNavList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: ListModel {
                ListElement { title: "Sensors"; iconName: "network-wireless-hotspot" }
                ListElement { title: "Cameras"; iconName: "camera-photo" }
                ListElement { title: "Calibration"; iconName: "autocorrection" }
                ListElement { title: "Recording"; iconName: "media-record" }
                ListElement { title: "Results"; iconName: "labplot-xy-plot-two-axes" }
            }
            delegate: ItemDelegate {
                id: sideBarItem
                leftPadding: root.pad
                width: parent.width
                text: model.title
                icon.name: model.iconName
                highlighted: ListView.isCurrentItem
                onClicked: {
                    if (sideBarNavList.currentIndex != index) {
                        sideBarNavList.currentIndex = index
                        mainContentStack.currentIndex = index
                    }
                }
            }
            ScrollIndicator.vertical: ScrollIndicator { }
        }
        ToolSeparator {
            orientation: Qt.Horizontal
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.margins: 10
            contentItem: Rectangle {
                implicitHeight: 1
                color: parent.palette.mid
            }
        }
        ItemDelegate {
            Layout.fillWidth: true
            text: "Settings"
            icon.name: "configure"
            onClicked: {
                settingsPopup.open()
            }
        }
        ItemDelegate {
            Layout.fillWidth: true
            text: "Help"
            icon.name: "help-about"
            onClicked: {
                helpPopup.open()
            }
        }
    }
}