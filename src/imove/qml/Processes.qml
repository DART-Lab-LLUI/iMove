import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

Page {
    id: processesPage

    GridView {
        id: sensorList
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        model: ListModel {
            ListElement { title: "Xsens-01"; iconName: "network-modem" }
            ListElement { title: "Xsens-02"; iconName: "network-modem" }
            ListElement { title: "Xsens-03"; iconName: "network-modem" }
            ListElement { title: "Xsens-04"; iconName: "network-modem" }
        }
        delegate: ColumnLayout {
            id: sensorItem
            Image {
                id: sensorItemImage
                source: "qrc:/icons/llui/dot.png"
                Layout.preferredWidth: 25
                Layout.preferredHeight: 25
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            } 
            Label {
                text: model.title
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            }
            Switch {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            }
        }
        ScrollIndicator.vertical: ScrollIndicator { }
    }
}
