import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

Pane {
    id: toolBarLayout
    width: parent.width
    height: toolBarRow.implicitHeight
    property bool center: false
    property int numVisibleButtons: toolBarRow.children.length
    // property alias spacing: toolBarRow.spacing
    signal actionTriggered(int index)
    default property alias toolButtons: toolBarRow.children
    padding: 0

    Row {
        id: toolBarRow
        anchors.fill: parent
        spacing: 10
        
        onWidthChanged: {
            updateToolButtonVisibility()
        }
    }

    ToolButton {
        id: moreButton
        icon.name: "overflow-menu"
        visible: false
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        Menu {
            id: overflowMenu
            Repeater {
                model: {return toolBarRow.children.slice(toolBarLayout.numVisibleButtons, toolBarRow.children.length).filter(element => element instanceof ToolButton);}
                delegate: MenuItem {
                    text: modelData.text
                    icon.name: modelData.icon.name
                    onTriggered: modelData.clicked()
                }
            }
        }
        onClicked: overflowMenu.open()
    }

    function updateToolButtonVisibility() {
        let totalWidth = 0
        let maxVisibleButtons = 0
        let shouldBeVisible = false
        for (let i = 0; i < toolBarRow.children.length; i++) {
            let button = toolBarRow.children[i]
            totalWidth += button.width + toolBarRow.spacing
            shouldBeVisible = totalWidth <= toolBarLayout.width
            if (shouldBeVisible) {
                maxVisibleButtons++
            }
            toolBarRow.children[i].visible = shouldBeVisible
        }
        moreButton.visible = maxVisibleButtons < toolBarRow.children.length
        toolBarLayout.numVisibleButtons = maxVisibleButtons
    }

    Component.onCompleted: {
        updateToolButtonVisibility()
        // make sure all the items are aligned
        toolBarRow.children.forEach((value, index, arr) => {arr[index].anchors.verticalCenter = toolBarRow.verticalCenter})
    }

    onWidthChanged: {
        updateToolButtonVisibility()
    }
}