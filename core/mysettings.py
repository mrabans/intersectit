#-----------------------------------------------------------
#
# Intersect It is a QGIS plugin to place observations (distance or orientation)
# with their corresponding precision, intersect them using a least-squares solution
# and save dimensions in a dedicated layer to produce maps.
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------

from PyQt4.QtGui import QColor
from ..qgissettingmanager import *

pluginName = "intersectit"


class MySettings(SettingManager):
    def __init__(self):
        SettingManager.__init__(self, pluginName)
         
        # global settings
        self.addSetting("obsDistanceSnapping", "string", "global", "all")
        self.addSetting("obsDefaultPrecisionDistance", "double", "global", .025)
        self.addSetting("obsDefaultPrecisionOrientation", "double", "global", .5)
        self.addSetting("obsOrientationLength", "double", "global", 4)
        self.addSetting("selectTolerance", "double", "global", 7)
        self.addSetting("selectUnits", "string", "global", "pixels")
        self.addSetting("rubberColor", "Color", "global", QColor(0, 0, 255, 150), {"alpha": True})
        self.addSetting("rubberWidth", "double", "global", 2)
        self.addSetting("rubberSize", "integer", "global", 12)
        self.addSetting("rubberIcon", "integer", "global", 4)
        self.addSetting("advancedIntersecLSmaxIteration", "Integer", "global", 15)
        self.addSetting("advancedIntersecLSconvergeThreshold", "double", "global", .0005)

        # project settings
        self.addSetting("simpleIntersectionWritePoint", "bool", "project", False)
        self.addSetting("advancedIntersectionWritePoint", "bool", "project", False)
        self.addSetting("advancedIntersectionWriteReport", "bool", "project", False)
        self.addSetting("dimensionDistanceWrite", "bool", "project", False)
        self.addSetting("dimensionDistanceObservationWrite", "bool", "project", False)
        self.addSetting("dimensionDistancePrecisionWrite", "bool", "project", False)
        self.addSetting("dimensionOrientationWrite", "bool", "project", False)
        self.addSetting("dimensionOrientationObservationWrite", "bool", "project", False)
        self.addSetting("dimensionOrientationPrecisionWrite", "bool", "project", False)
        # fields and layers
        self.addSetting("dimensionDistanceLayer", "string", "project", "")
        self.addSetting("dimensionDistancePrecisionField", "string", "project", "")
        self.addSetting("dimensionDistanceObservationField", "string", "project", "")
        self.addSetting("dimensionOrientationLayer", "string", "project", "")
        self.addSetting("dimensionOrientationPrecisionField", "string", "project", "")
        self.addSetting("dimensionOrientationObservationField", "string", "project", "")

        self.addSetting("simpleIntersectionLayer", "string", "project", "")
        self.addSetting("advancedIntersectionLayer", "string", "project", "")
        self.addSetting("reportField", "string", "project", "")
        self.addSetting("memoryLineLayer", "string", "project", "")
        self.addSetting("memoryPointLayer", "string", "project", "")
