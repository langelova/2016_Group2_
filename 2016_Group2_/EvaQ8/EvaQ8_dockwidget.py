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
    updateAttribute = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Constructor."""
        super(EvaQ8DockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)


        #report
        self.Send_report.clicked.connect(self.sendReport)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


    # Report functions

    def sendReport(self):
        path = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)')
        if path.strip() != "":
            with open(unicode(path), 'wb') as report:
                # write header
                writer = csv.DictWriter(report, fieldnames=["Total People","Evacuated People","Injured People","Ambulances","Policemen"])
                writer.writeheader()
                # write data
                totalpeople = self.lineEdit_T_People.text()
                evacuated = self.lineEdit_Evacuated.text()
                injured = self.lineEdit_Injured.text()
                ambulances = self.lineEdit_Ambulances.text()
                policemen = self.lineEdit_Policemen.text()
                writer.writerow({"Total People": str(totalpeople),"Evacuated People": str(evacuated),"Injured People": str(injured),"Ambulances": str(ambulances),"Policemen": str(policemen)})


