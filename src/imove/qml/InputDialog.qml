import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import "."

Dialog {
    id: inputDialog
    property alias dialogTitle: dialogLabel.text
    property alias dialogTitleIconName: dialogLabel.icon.name
    property alias placeholderText: textField.placeholderText
    property alias enteredText: textField.text
    property alias enteredTextValidator: textField.validator
    property string acceptText: "Apply"
    
    modal: false

    contentItem: Page {
        anchors.fill: parent
        padding: Units.largeSpacing
        header: Pane {
            Material.background: appSettings.colors.subBarBackground
            Material.foreground: appWindow.Material.foreground
            IconLabel {
                id: dialogLabel
            }
        }
        TextField {
            id: textField
            width: parent.width
        }
        footer: Row{
            layoutDirection: Qt.RightToLeft	
            ToolButton {
                text: "Cancel"
                onClicked: inputDialog.reject()
                flat: true
            }
            ToolButton {
                text: inputDialog.acceptText
                onClicked: inputDialog.accept()
                flat: true
            }
        }    
    }
}