pragma Singleton

import QtQuick

Item {
    id: units
    readonly property int gridUnit: fontMetrics.height
    readonly property int smallSpacing: gridUnit/4
    readonly property int mediumSpacing: gridUnit/2
    readonly property int largeSpacing: gridUnit
    readonly property int veryLargeSpacing: gridUnit*2
    readonly property real devicePixelRatio: fontMetrics.font.pixelSize / (fontMetrics.font.pointSize * 1.33)
    readonly property int longDuration: 250
    readonly property int shortDuration: 150

    function gu(x) {
        return Math.round(x * gridUnit);
    }

    TextMetrics {
        id: fontMetrics
        text: "M"
    }
}