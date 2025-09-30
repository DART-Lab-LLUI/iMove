import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import "."

Page {
    id: root

    property bool closed: false  
    
    function close() {
        closed = true
    }
    function open() {
        closed = false
    }
    height: closed ? 0 : implicitHeight
    Behavior on height {
        NumberAnimation {
            easing.type: Easing.InOutQuad
        }
    }

    header: TabBar {
        id: tabBar
        TabButton {
            text: "Processes"
        }
    }
    
    StackLayout {
        anchors.fill: parent
        currentIndex: tabBar.currentIndex
        
        ProcessesPage {
            id: processes
        }
    }
}