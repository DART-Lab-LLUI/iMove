import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtMultimedia
import QtCharts

import "."
import qml

Page {
    id: resultPage
    
    property var poseManager: Context.poseManager
    
    header: DynToolBar { 
        padding: 5
        Material.background: appSettings.colors.subBarBackground
        Material.foreground: appWindow.Material.foreground
        Label {
            id: pageLabel
            text: "Results"
        }
        Item {
            width: Units.largeSpacing
        }
        ToolButton {
            id: estimateButton
            text: "Estimate"
            icon.name: "autocorrection"
            onClicked: {
                poseManager.startEstimation()
            }
            enabled: !poseManager.isEstimating
        }
        ToolButton {
            id: plotButton
            text: "Plot"
            icon.name: "labplot-xy-plot-two-axes"
            onClicked: {
                poseManager.plotMetrics()
            }
        }
        BusyIndicator {
            height: estimateButton.implicitHeight
            running: poseManager.isEstimating
        }
    }
    
    ScrollView {
        anchors.fill: parent
        padding: Units.smallSpacing
        Flow {
            width: resultPage.width
            spacing: Units.mediumSpacing
            Repeater {
                model: poseManager.plots
                delegate: Page {
                    Material.elevation: 3
                    id: plotItem
                    width: plotImage.width > 0 ? plotImage.width + Units.mediumSpacing : 600
                    height: plotImage.height > 0 ? plotImage.height + titleBar.height + Units.mediumSpacing : 300
                    header: ToolBar {
                        id: titleBar
                        padding: 5
                        width: parent.width
                        Material.background: appSettings.colors.subBarBackground
                        Material.foreground: appWindow.Material.foreground
                        RowLayout {
                            anchors.fill: parent
                            Label {
                                id: plotTitle
                                text: modelData.title
                                Layout.alignment: Qt.AlignVCenter
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            ComboBox {
                                id: subplotComboBox
                                property var previousValue: null
                                Layout.alignment: Qt.AlignVCenter
                                Layout.preferredHeight: plotTitle.height + Units.gu(1)
                                implicitContentWidthPolicy: ComboBox.WidestText
                                model: modelData.subplotNames
                                onActivated: {
                                    plotImage.source = modelData.getSubplot(currentValue)
                                }
                                Component.onCompleted: {
                                    if (currentValue && currentValue.trim().length > 0)
                                        plotImage.source = modelData.getSubplot(currentValue)
                                }
                            }
                        }
                    }
                    Image {
                        id: plotImage
                        width: implicitWidth * 0.6
                        height: implicitHeight * 0.6
                        source: ''
                        fillMode: Image.PreserveAspectFit
                    }
                }
            }
        }
    }
}