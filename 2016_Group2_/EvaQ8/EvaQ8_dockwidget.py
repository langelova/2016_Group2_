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
        self.Send_Location.clicked.connect(self.policemen_send_location)

        self.Main_table.itemSelectionChanged.connect(self.startNavigationOn)
        self.Navigation.setDisabled(True)
        self.Navigation.clicked.connect(self.startnavigation)
        self.graph = QgsGraph()
        self.tied_points = []
        self.roads_layer = getLegendLayerByName(self.iface, 'ROAD_NETWORK')
        self.current_location = None

        # report
        self.createCSV()
        self.Send_report.clicked.connect(self.sendReport)
        self.Send_report.clicked.connect(self.clear)
        self.Send_report.clicked.connect(self.evacuated_building)

        #disabled buttons if nothing selected
        self.Send_Location.setDisabled(True)
        self.Send_report.setDisabled(True)
        self.Police.setDisabled(True)
        self.Ambulance.setDisabled(True)

        #enable if selection
        self.Main_table.itemSelectionChanged.connect(self.Enable_buttons)

    def startnavigation(self):
        building_layer = getLegendLayerByName(self.iface, "Buildings")
        police_stations_layer = getLegendLayerByName(self.iface, "POLICE_STATIONS")
        routes_layer = getLegendLayerByName(self.iface, "Routes")
        if routes_layer:
            routes_layer.startEditing()
            features = routes_layer.getFeatures()
            ids = [feature.id() for feature in features]
            routes_layer.deleteFeatures(ids)
            routes_layer.commitChanges()
        else:
            routes_layer = createTempLayer('Routes', 'LINESTRING', building_layer.crs().postgisSrid(), ['id'], [QtCore.QVariant.Int])
            routes_layer.loadNamedStyle("%s/FINAL_DATA/routes.qml" % self.plugin_dir)
            loadTempLayer(routes_layer)

        # get the building point, and the corresponding police station point
        # destination is currently selected building:
        building_id = self.Main_table.item(self.Main_table.currentRow(), 0).text()
        # select building feature with these coordinates.(extracting only the floats)
        building_coords = building_id[1:-1].split(',')
        target_point = QgsPoint(float(building_coords[0]), float(building_coords[1]))
        # origin is the current location or the police station
        if self.current_location:
            # get id of the currently selected building
            origin_id = self.Main_table.item(self.current_location, 0).text()
            origin_coords = origin_id[1:-1].split(',')
            origin_point = QgsPoint(float(origin_coords[0]), float(origin_coords[1]))
        else:
            # select police station name from target building feature
            origin_attribs = self.getFeaturesWithValues(building_layer, 'X', [float(building_coords[0])])
            origin_id = origin_attribs.values()[0][9]
            # select police station with that id
            request = QgsFeatureRequest().setFilterExpression("\"name\" = '%s'" % origin_id)
            iterator = police_stations_layer.getFeatures(request)
            for feature in iterator:
                origin_point = QgsPoint(feature.attribute('X'), feature.attribute('Y'))
                break

        # add these points to a list
        new_points = [origin_point, target_point]
        # build the graph, which returns the tied points. this is a list of points that are used to calculate routes.
        self.graph, self.tied_points = makeUndirectedGraph(self.roads_layer, new_points)

        # this next part calculates the route
        origin = 0  # the first point in the new_points list
        destination = 1  # the other point
        path = calculateRouteDijkstra(self.graph, self.tied_points, origin, destination)
        # store the route results in temporary layer called "Routes", with an id column
        if path and routes_layer:
            provider = routes_layer.dataProvider()
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromPolyline(path))
            provider.addFeatures([fet])
            provider.updateExtents()
        self.canvas.refresh()
        # keep this location as next origin
        self.current_location = self.Main_table.currentRow()
        self.canvas.setExtent(routes_layer.extent())
        self.canvas.zoomOut()
        self.canvas.refresh()

    def getFeaturesWithValues(self, layer, name, values=list):
        features = {}
        if layer:
            if fieldExists(layer, name):
                iterator = layer.getFeatures()
                for feature in iterator:
                    att = feature.attribute(name)
                    if att in values:
                        features[feature.id()] = feature.attributes()
        return features

    def startNavigationOn(self):
        self.Navigation.setDisabled(False)


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
            self.Send_Location.setDisabled(True)
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
        self.Main_table.sortItems(1)
        self.Main_table.itemSelectionChanged.connect(self.Additional_info)
        self.Main_table.itemSelectionChanged.connect(self.createReport)

    def Additional_info(self):
        #get from the selected building it's x coordinate
        v = self.Main_table.selectedItems()[0].text()
        next = v[1:-1]
        t = next.split(",")
        coord = float(t[0])
        #search in the layer for this feature
        layer = getCanvasLayerByName(self.iface, "Buildings")
        feature = getFeaturesByExpression(layer,'"X"=%s'%coord)
        #get all attributes of the feature
        l = feature.values()
        #puting the ones needed in Additional info tab
        self.Population_floor.setText(str(l[0][5]))
        self.Population_total.setText(str(l[0][4]))
        self.Building_type.setText(str(l[0][6]))
        self.Floors.setText(str(l[0][3]))
        #zoom to the selected feature
        layer.setSelectedFeatures(feature.keys())
        if layer.selectedFeatureCount() > 0:
            self.iface.mapCanvas().setCurrentLayer(layer)
            self.iface.mapCanvas().zoomToSelected()
            self.canvas.zoomScale(1000.0)


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



    def createCSV(self):
        with open(self.plugin_dir + '//SEND_REPORT//sentreport.csv', 'w') as report:
            writer = csv.DictWriter(report,fieldnames=["Location","Total People","Evacuated People","Injured People","Ambulances","Policemen"])
            writer.writeheader()


    def sendReport(self):
        csvfile = self.plugin_dir + '//SEND_REPORT//sentreport.csv'
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
            self.textEdit.setText('Report has been sent!')
            self.Send_report.setDisabled(True)


    def evacuated_building(self):
        row = self.Main_table.currentRow()
        for i in range(0,3):
            v = self.Main_table.item(row, i)
            v.setBackground(QtGui.QColor(0, 255, 0))

    def clear(self):
        evacuated = self.lineEdit_Evacuated.setText("")
        injured = self.lineEdit_Injured.setText("")
        ambulances = self.lineEdit_Ambulances.setText("")
        policemen = self.lineEdit_Policemen.setText("")

    def policemen_send_location(self):
        current_text = self.lineEdit_Policemen.text()
        if current_text == '':
            current_count = 0
        else:
            current_count = int(current_text)

        self.lineEdit_Policemen.setText(str(current_count + 1))

    def Enable_buttons(self):
        self.Send_Location.setDisabled(False)
        self.Send_report.setDisabled(False)
        self.Police.setDisabled(False)
        self.Ambulance.setDisabled(False)





