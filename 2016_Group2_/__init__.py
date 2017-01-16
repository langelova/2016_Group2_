# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EvaQ8
                                 A QGIS plugin
 SDSS system helping police officers evacuate buildings.
                             -------------------
        begin                : 2016-12-13
        copyright            : (C) 2016 by Lilia Angelova
        email                : urb.lili.an@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load EvaQ8 class from file EvaQ8.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .EvaQ8 import EvaQ8
    return EvaQ8(iface)
