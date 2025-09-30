import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

Popup {
    id: root
    focus: true
    margins: 50
    contentItem: Column {
        spacing: 10
        Text {
            text: "Help"
            wrapMode: Text.Wrap
        }
    }
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
}