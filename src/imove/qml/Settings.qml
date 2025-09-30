import QtQuick
import QtQuick.Controls.Material
import "."

Item {
    id: root

    // readonly property bool isMobile: ( Qt.platform.os === "ios") || ( Qt.platform.os === "android")
    readonly property bool isMobile: appWindow.width <= Units.gu(35)
    readonly property int gridDelegateSize: Units.gu(12)
    readonly property real disabledOpacity: 0.3

    readonly property QtObject colors: QtObject {

        readonly property real barBackgroundScale: 1.02
        readonly property real subBarBackgroundScale: 1.05
        readonly property real statusBarBackgroundScale: 1.05
        readonly property real sideBackgroundScale: 1.08

        readonly property color barBackground: (Material.theme == Material.Dark) ? Qt.lighter(Material.background, barBackgroundScale) : Qt.darker(Material.background, barBackgroundScale)
        readonly property color subBarBackground: (Material.theme == Material.Dark) ? Qt.lighter(Material.background, subBarBackgroundScale) : Qt.darker(Material.background, subBarBackgroundScale)
        readonly property color statusBarBackground: (Material.theme == Material.Dark) ? Qt.lighter(Material.accent, statusBarBackgroundScale) : Qt.darker(Material.accent, statusBarBackgroundScale)
        readonly property color sideBackground: (Material.theme == Material.Dark) ? Qt.lighter(Material.background, sideBackgroundScale) : Qt.darker(Material.background, sideBackgroundScale)
        

        readonly property real selectionScale: 1.08
        readonly property color selection: (Material.theme == Material.Dark) ? Qt.lighter(Material.accent, selectionScale) : Qt.darker(Material.accent, selectionScale)

        readonly property real highlightScale: 1.5
        readonly property color highlight: (Material.theme == Material.Dark) ? Qt.lighter(Material.background, highlightScale) : Qt.darker(Material.background, highlightScale)

        readonly property color accentHighlight: (Material.theme == Material.Dark) ? Qt.lighter(Material.accent, highlightScale) : Qt.darker(Material.accent, highlightScale)
    }
}