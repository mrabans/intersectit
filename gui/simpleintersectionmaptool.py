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

from qgis.core import QGis, QgsFeatureRequest, QgsFeature, QgsPoint, QgsGeometry, QgsMapLayerRegistry, QgsMapLayer, QgsTolerance, QgsSnapper
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMessageBar

from ..core.mysettings import MySettings
from ..core.isfeaturerendered import isFeatureRendered


class SimpleIntersectionMapTool(QgsMapTool):
    def __init__(self, iface):
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        QgsMapTool.__init__(self, self.mapCanvas)
        self.settings = MySettings()
        self.rubber = QgsRubberBand(self.mapCanvas)

    def deactivate(self):
        self.rubber.reset()
        self.mapCanvas.layersChanged.disconnect(self.updateSnapperList)
        self.mapCanvas.scaleChanged.disconnect(self.updateSnapperList)
        QgsMapTool.deactivate(self)

    def activate(self):
        QgsMapTool.activate(self)
        self.rubber.setWidth(self.settings.value("rubberWidth"))
        self.rubber.setColor(self.settings.value("rubberColor"))
        self.updateSnapperList()
        self.mapCanvas.layersChanged.connect(self.updateSnapperList)
        self.mapCanvas.scaleChanged.connect(self.updateSnapperList)
        self.checkLayer()

    def updateSnapperList(self, dummy=None):
        # make a snapper list of all line and polygons layers
        self.snapperList = []
        scale = self.iface.mapCanvas().mapRenderer().scale()
        for layer in self.mapCanvas.layers():
            if layer.type() == QgsMapLayer.VectorLayer and layer.hasGeometryType():
                if layer.geometryType() in (QGis.Line, QGis.Polygon):
                    if not layer.hasScaleBasedVisibility() or layer.minimumScale() < scale <= layer.maximumScale():
                        snapLayer = QgsSnapper.SnapLayer()
                        snapLayer.mLayer = layer
                        snapLayer.mSnapTo = QgsSnapper.SnapToVertexAndSegment
                        snapLayer.mTolerance = self.settings.value("selectTolerance")
                        if self.settings.value("selectUnits") == "map":
                            snapLayer.mUnitType = QgsTolerance.MapUnits
                        else:
                            snapLayer.mUnitType = QgsTolerance.Pixels
                        self.snapperList.append(snapLayer)

    def canvasMoveEvent(self, mouseEvent):
        # put the observations within tolerance in the rubber band
        self.rubber.reset()
        for f in self.getFeatures(mouseEvent.pos()):
            self.rubber.addGeometry(f.geometry(), None)

    def canvasPressEvent(self, mouseEvent):
        self.rubber.reset()
        pos = mouseEvent.pos()
        features = self.getFeatures(pos)
        nFeat = len(features)
        if nFeat < 2:
            layerNames = " , ".join([feature.layer.name() for feature in features])
            self.iface.messageBar().pushMessage("Intersect It", "You need 2 features to proceed a simple intersection."
                                                " %u given (%s)" % (nFeat, layerNames), QgsMessageBar.WARNING, 3)
            return
        intersectionP = self.intersection(features, pos)
        if intersectionP == QgsPoint(0,0):
            self.iface.messageBar().pushMessage("Intersect It", "Objects do not intersect.", QgsMessageBar.WARNING, 2)
            return

        layer = self.checkLayer()
        if layer is None:
            return
        f = QgsFeature()
        initFields = layer.dataProvider().fields()
        f.setFields(initFields)
        f.initAttributes(initFields.size())
        f.setGeometry(QgsGeometry().fromPoint(intersectionP))
        layer.editBuffer().addFeature(f)
        layer.triggerRepaint()

    def getFeatures(self, pixPoint):
        # do the snapping
        snapper = QgsSnapper(self.mapCanvas.mapRenderer())
        snapper.setSnapLayers(self.snapperList)
        snapper.setSnapMode(QgsSnapper.SnapWithResultsWithinTolerances)
        ok, snappingResults = snapper.snapPoint(pixPoint, [])
        # output snapped features
        features = []
        alreadyGot = []
        for result in snappingResults:
            featureId = result.snappedAtGeometry
            f = QgsFeature()
            if (result.layer.id(), featureId) not in alreadyGot:
                if result.layer.getFeatures(QgsFeatureRequest().setFilterFid(featureId)).nextFeature(f) is False:
                    continue
                if not isFeatureRendered(self.mapCanvas, result.layer, f):
                    continue
                features.append(QgsFeature(f))
                features[-1].layer = result.layer
                alreadyGot.append((result.layer.id(), featureId))
        return features

    def intersection(self, features, pos):
        # try all the combinations
        nFeat = len(features)
        intersections = []
        for i in range(nFeat-1):
            for j in range(i+1,nFeat):
                intersection = features[i].geometry().intersection(features[j].geometry())
                intersectionMP = intersection.asMultiPoint()
                intersectionP = intersection.asPoint()
                if len(intersectionMP) == 0:
                    intersectionMP = intersection.asPolyline()
                if len(intersectionMP) == 0 and intersectionP == QgsPoint(0, 0):
                    continue
                if len(intersectionMP) > 1:
                    mousePoint = self.toMapCoordinates(pos)
                    intersectionP = intersectionMP[0]
                    for point in intersectionMP[1:]:
                        if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                            intersectionP = QgsPoint(point.x(), point.y())
                if intersectionP != QgsPoint(0,0):
                    intersections.append(intersectionP)
        if len(intersections) == 0:
            return QgsPoint(0,0)
        intersectionP = intersections[0]
        for point in intersections[1:]:
            if mousePoint.sqrDist(point) < mousePoint.sqrDist(intersectionP):
                intersectionP = QgsPoint(point.x(), point.y())
        return intersectionP

    def checkLayer(self):
        # check output layer is defined
        layerid = self.settings.value("simpleIntersectionLayer")
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        if not self.settings.value("simpleIntersectionWritePoint") or layer is None:
            self.iface.messageBar().pushMessage("Intersect It",
                                                "You must define an output layer for simple intersections",
                                                QgsMessageBar.WARNING, 3)
            self.mapCanvas.unsetMapTool(self)
            return None
        if not layer.isEditable():
            self.iface.messageBar().pushMessage("Intersect It",
                                                "The output layer <b>%s must be editable</b>" % layer.name(),
                                                QgsMessageBar.WARNING, 3)
            self.mapCanvas.unsetMapTool(self)
            return None
        return layer
