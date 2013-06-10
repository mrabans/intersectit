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

from PyQt4.QtGui import QMessageBox
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsMapLayerRegistry
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand

from ..core.mysettings import MySettings
from ..core.memorylayers import MemoryLayers
from ..core.leastsquares import LeastSquares
from ..core.intersections import TwoCirclesIntersection, TwoDirectionIntersection, CircleDirectionIntersection

from placedimension import PlaceDimension
from lsreport import LSreport
from mysettingsdialog import MySettingsDialog


class placeIntersectionOnMap(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.settings = MySettings()
        self.lineLayer = MemoryLayers(iface).lineLayer
        self.pointLayer = MemoryLayers(iface).pointLayer
        self.rubber = QgsRubberBand(self.canvas)
        self.rubber.setWidth(self.settings.value("intersectRubberWidth"))
        self.rubber.setColor(self.settings.value("intersectRubberColor"))
        self.tolerance = self.settings.value("intersecSelectTolerance")
        units = self.settings.value("intersecSelectUnits")
        if units == "pixels":
            self.tolerance *= self.canvas.mapUnitsPerPixel()

    def deactivate(self):
        self.rubber.reset()

    def canvasMoveEvent(self, mouseEvent):
        # put the observations within tolerance in the rubber band
        self.rubber.reset()
        point = self.toMapCoordinates(mouseEvent.pos())
        for f in self.getFeatures(point):
            self.rubber.addGeometry(f.geometry(), None)

    def canvasPressEvent(self, mouseEvent):
        self.rubber.reset()
        observations = []
        point = self.toMapCoordinates(mouseEvent.pos())
        for f in self.getFeatures(point):
            observations.append(QgsFeature(f))
        self.doIntersection(point, observations)

    def getFeatures(self, point):
        features = []
        featReq = QgsFeatureRequest()
        box = QgsRectangle(point.x()-self.tolerance,
                           point.y()-self.tolerance,
                           point.x()+self.tolerance,
                           point.y()+self.tolerance)
        featReq.setFilterRect(box)
        f = QgsFeature()
        vliter = self.lineLayer().getFeatures(featReq)
        while vliter.nextFeature(f):
            features.append(QgsFeature(f))
        return features

    def doIntersection(self, initPoint, observations):
        nObs = len(observations)
        report = ""
        if nObs < 2:
            return
        if nObs == 2:
            if observations[0]["type"] == "distance" and observations[1]["type"] == "distance":
                intersectedPoint = TwoCirclesIntersection(observations, initPoint).intersection
            elif observations[0]["type"] == "prolongation" and observations[1]["type"] == "prolongation":
                intersectedPoint = TwoDirectionIntersection(observations).intersection
            else:
                intersectedPoint = CircleDirectionIntersection(observations, initPoint).intersection
            if intersectedPoint is None:
                return
            if self.settings.value("intersecResultConfirm"):
                reply = QMessageBox.question(self.iface.mainWindow(), "IntersectIt",
                                             "A perfect intersection has been found using two elements."
                                             " Use this solution?", QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
        else:
            LS = LeastSquares(observations, initPoint)
            intersectedPoint = LS.solution
            report = LS.report
            if self.settings.value("intersecResultConfirm"):
                if not LSreport(report).exec_():
                    return

        # save the intersection result (point) and its report
        # check first
        while True:
            if not self.settings.value("intersecResultPlacePoint"):
                break  # if we do not place any point, skip
            layerid = self.settings.value("intersectionLayer")
            message = "To place the intersection solution, you must select a layer in the settings."
            status, intLayer = self.checkLayerExists(layerid, message)
            if status == 2:
                continue
            if status == 3:
                return
            if self.settings.value("intersecResultPlaceReport"):
                reportField = self.settings.value("reportField")
                message = "To save the intersection report, please select a field for it."
                status = self.checkFieldExists(intLayer, reportField, message)
                if status == 2:
                    continue
                if status == 3:
                    return
            break

        # save the intersection results
        if self.settings.value("intersecResultPlacePoint"):
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPoint(intersectedPoint))
            if self.settings.value("intersecResultPlaceReport"):
                irep = intLayer.dataProvider().fieldNameIndex(reportField)
                f.addAttribute(irep, report)
            intLayer.dataProvider().addFeatures([f])
            intLayer.updateExtents()
            self.canvas.refresh()

         # check that dimension layer and fields have been set correctly
        while True:
            if not self.settings.value("dimenPlaceDimension"):
                return  # if we do not place any dimension, skip
            layerid = self.settings.value("dimensionLayer")
            message = "To place dimension arcs, you must select a layer in the settings."
            status, dimLayer = self.checkLayerExists(layerid, message)
            if status == 2:
                continue
            if status == 3:
                return
            if self.settings.value("dimenPlaceMeasure"):
                field = self.settings.value("observationField")
                message = "To save the observed distance, please select a field for it."
                status = self.checkFieldExists(dimLayer, field, message)
                if status == 2:
                    continue
                if status == 3:
                    return
            if self.settings.value("dimenPlacePrecision"):
                field = self.settings.value("precisionField")
                message = "To save the observation precision, please select a field for it."
                status = self.checkFieldExists(dimLayer, field, message)
                if status == 2:
                    continue
                if status == 3:
                    return
            break
        dlg = PlaceDimension(self.iface, intersectedPoint, observations, [self.lineLayer(), self.pointLayer()])
        dlg.exec_()

    def checkLayerExists(self, layerid, message):
        # returns:
        # 1: layer exists
        # 2: does not exist, settings has been open, so loop once more (i.e. continue)
        # 3: does not exist, settings not edited, so cancel
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        if layer is not None:
            return 1, layer

        reply = QMessageBox.question(self.iface.mainWindow(), "IntersectIt",
                                     message + " Would you like to open settings?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if MySettingsDialog().exec_():
                return 2
        return 3

    def checkFieldExists(self, layer, field, message):
        # returns:
        # 1: field exists
        # 2: does not exist, settings has been open, so loop once more (i.e. continue)
        # 3: does not exist, settings not edited, so cancel
        if layer.dataProvider().fieldNameIndex(field) != -1:
            return 1

        reply = QMessageBox.question(self.iface.mainWindow(), "IntersectIt",
                                     message + " Would you like to open settings?", QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if MySettingsDialog().exec_():
                return 2
        return 3
