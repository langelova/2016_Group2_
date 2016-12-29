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

from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtCore import pyqtSignal
from qgis.core import *
from qgis.networkanalysis import *
from qgis.gui import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'EvaQ8_dockwidget_base.ui'))


class EvaQ8DockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(EvaQ8DockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def clearTable(self):
        self.main_table.clear()

    def updateTable(self,values):
        self.main_table.setColumnCount(3)
        self.main_table.setHorizontalHeaderLabels(["Location","Priority","Officers at incident"])
        self.main_table.setRowCont(len(values))
        for i, item in enumerate(values):
            self.main_table.setItem(i, 0, QtGui.QTableWidgetItem(str(item[0])))
            self.main_table.setItem(i, 1, QtGui.QTableWidgetItem(str(item[1])))
        self.main_table.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.main_table.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        #hide grid
        #self.Main_table.setShowGrid(False)
        #set background color of selected row
        #self.Main_table.setStyleSheet("QTableView {selection-background-color: red;}")
        self.main_table.resizeRowsToContents()

    def getLegendLayerByName(iface, name):
        layer = None
        for i in iface.legendInterface().layers():
            if i.name() == name:
                layer = i
        return layer

    def getAttributes(self,iface):
        layer = getLegendLayerByName(self.iface,"Buildings")
        table = []
        for feature in layer.getFeatures():
            #get feature attributes
            attr = feature.attributes()
            coord = attr[1], attr[2]
            priority = attr[7]
            ref_attr = coord, priority
            table.append(ref_attr)
        self.clearTable()
        self.updateTable(table)







