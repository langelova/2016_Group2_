# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EvaQ8DockWidget
                                 A QGIS plugin
 SDSS system helping police officers evacuate buildings.
                             -------------------
        begin                : 2016-12-13
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Lilia Angelova
        email                : urb.lili.an@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import csv

from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtCore import pyqtSignal
from qgis.core import *
from qgis.networkanalysis import *
from qgis.gui import *
from utility_functions import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'EvaQ8_dockwidget_base.ui'))


class EvaQ8DockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()


    def __init__(self, iface, parent=None):
        """Constructor."""
        super(EvaQ8DockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.Police.clicked.connect(self.getPolice)
        self.Ambulance.clicked.connect(self.getAmbulance)

        # define globals
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)
        self.LoadLayers()
        self.getAttributes()
        self.Send_Location.clicked.connect(self.sendLocation)

        #self.Navigation.clicked.connect(self.startnavigation)
        self.graph = QgsGraph()
        self.tied_points = []
        self.roads_layer = getLegendLayerByName(self.iface, 'ROADS')
        self.current_location = None

        # report
        self.createCSV()
        self.Send_report.clicked.connect(self.sendReport)

    def getPolice(self):
        # self.textEdit.setTextColor(QtGui.QColor.setblue(255))
        self.textEdit.setText('Police are on their way!')

        current_text = self.lineEdit_Policemen.text()
        if current_text == '':
            current_count = 0
        else:
            current_count = int(current_text)
        self.lineEdit_Policemen.setText(str(current_count + 1))


    def getAmbulance(self):
        # self.textEdit.setTextColor(QtGui.QColor.setred(255))
        self.textEdit.setText('An ambulance is on its way!')

        current_text = self.lineEdit_Ambulances.text()
        if current_text == '':
            current_count = 0
        else:
            current_count = int(current_text)
        self.lineEdit_Ambulances.setText(str(current_count + 1))


    def sendLocation(self):
        try:
            current_row = self.Main_table.currentRow()
            self.current_location = current_row
            update_item = self.Main_table.item(current_row, 2)
            current_count = int(update_item.text())
            update_item.setText(str(current_count + 1))
            self.Main_table.setItem(current_row, 2, update_item)
        except:
            pass

    def LoadLayers(self,filename=""):
        scenario_open = False
        scenario_file = self.plugin_dir+'/FINAL_DATA/EvaQ8_project.qgs'
        # check if file exists
        if os.path.isfile(scenario_file):
            self.iface.addProject(scenario_file)
            scenario_open = True
        else:
            last_dir = getLastDir("SDSS")
            new_file = QtGui.QFileDialog.getOpenFileName(self, "", last_dir, "(*.qgs)")
            if new_file:
                self.iface.addProject(unicode(new_file))
                scenario_open = True


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


    def clearTable(self):
        self.Main_table.clear()


    def getAttributes(self):
        layer = getCanvasLayerByName(self.iface, "Buildings")
        table = []
        for feature in layer.getFeatures():
            #get feature attributes
            coord = feature['X'], feature['Y']
            priority = feature['priority']
            table.append((coord, priority))
        self.clearTable()
        self.updateTable(table)


    def updateTable(self,values):
        self.Main_table.setHorizontalHeaderLabels(["Location","Priority","Officer at place"])
        self.Main_table.setRowCount(len(values))
        for i, item in enumerate(values):
            self.Main_table.setItem(i, 0, QtGui.QTableWidgetItem(str(item[0])))
            self.Main_table.setItem(i, 1, QtGui.QTableWidgetItem(str(item[1])))
            self.Main_table.setItem(i, 2, QtGui.QTableWidgetItem(str(0)))
        self.Main_table.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.Main_table.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.Main_table.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        #hide grid
        self.Main_table.setShowGrid(True)
        #set background color of selected row
        self.Main_table.setStyleSheet("QTableView {selection-background-color: red;}")
        self.Main_table.resizeRowsToContents()
        self.Main_table.itemSelectionChanged.connect(self.getAdditionalInfo)
        self.Main_table.itemSelectionChanged.connect(self.createReport)


    def getAdditionalInfo(self):
        items = self.Main_table.selectedItems()[0].text()
        next = items[1:-1]
        attr = next.split(",")
        coord = float(attr[0])
        # search in the layer for this feature
        layer = getCanvasLayerByName(self.iface, "Buildings")
        feature = getFeaturesByExpression(layer, '"X"=%s'%coord)
        # get all attributes of the feature
        l = feature.values()
        # puting the ones needed in Additional info tab
        self.Population_floor.setText(str(l[0][5]))
        self.Population_total.setText(str(l[0][4]))
        self.Building_type.setText(str(l[0][6]))
        self.Floors.setText(str(l[0][3]))
        # zoom to the selected feature
        layer.setSelectedFeatures(feature.keys())
        if layer.selectedFeatureCount() > 0:
            self.iface.mapCanvas().setCurrentLayer(layer)
            self.iface.mapCanvas().zoomToSelected()
            # self.iface.mapCanvas().zoomOut()


    # Report functions

    def createReport(self):
        items = self.Main_table.selectedItems()[0].text()
        next = items[1:-1]
        attr = next.split(",")
        coord = float(attr[0])
        # search in the layer for this feature
        layer = getCanvasLayerByName(self.iface, "Buildings")
        feature = getFeaturesByExpression(layer, '"X"=%s'%coord)
        # get all attributes of the feature
        l = feature.values()
        # puting the ones needed in Additional info tab
        self.lineEdit_T_People.setText(str(l[0][4]))
        policemen = self.Main_table.selectedItems()[2].text()
        self.lineEdit_Policemen.setText(str(policemen))


    def createCSV(self):
        with open(self.plugin_dir + '//SENT_REPORT//sentreport.csv', 'w') as report:
            writer = csv.DictWriter(report,fieldnames=["Location","Total People","Evacuated People","Injured People","Ambulances","Policemen"])
            writer.writeheader()


    def sendReport(self):
        csvfile = self.plugin_dir + '//SENT_REPORT//sentreport.csv'
        with open(csvfile, 'a') as report:
            writer = csv.writer(report)
            # write data
            location = self.Main_table.selectedItems()[0].text()
            totalpeople = self.lineEdit_T_People.text()
            evacuated = self.lineEdit_Evacuated.text()
            injured = self.lineEdit_Injured.text()
            ambulances = self.lineEdit_Ambulances.text()
            policemen = self.lineEdit_Policemen.text()
            writer.writerow([str(location),str(totalpeople),str(evacuated),str(injured), str(ambulances), str(policemen)])