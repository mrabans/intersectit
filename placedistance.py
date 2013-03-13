"""
IntersectIt QGIS plugin
Denis Rouzaud
denis.rouzaud@gmail.com
Jan. 2012

mapTools
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

#from mysettings import MySettings
from observation import Observation
from ui.ui_place_distance import Ui_place_distance

class PlaceDistanceDialog(QDialog, Ui_place_distance ):
	def __init__(self,point):
		QDialog.__init__(self)
		# Set up the user interface from Designer.
		self.setupUi(self)	
		self.x.setText("%.3f" % point.x())
		self.y.setText("%.3f" % point.y())
		self.distance.selectAll()

class PlaceDistanceOnMap(QgsMapToolEmitPoint):
	def __init__(self, iface, snapping=0):
		self.iface = iface
		self.canvas = iface.mapCanvas()
		self.snapping = snapping
		self.rubber = QgsRubberBand(self.canvas)
		QgsMapToolEmitPoint.__init__(self, self.canvas)

	def canvasMoveEvent(self, mouseEvent):
		if self.snapping:
			snappedPoint = self.snapToLayers( mouseEvent.pos() )
			if snappedPoint is None:
				self.rubber.reset()
			else:
				self.rubber.setToGeometry( QgsGeometry.fromPoint(snappedPoint), None )

	def canvasPressEvent(self, mouseEvent):
		if mouseEvent.button() != Qt.LeftButton: return
		self.rubber.reset()
		pixPoint = mouseEvent.pos()
		mapPoint = self.toMapCoordinates( pixPoint )
		#snap to layers
		if self.snapping:
			mapPoint = self.snapToLayers( pixPoint, mapPoint)
		# creates ditance with dialog
		dlg = PlaceDistanceDialog(mapPoint)
		if dlg.exec_():
			radius    = dlg.distance.value()
			precision = dlg.precision.value()
			if radius==0: return
			Observation( self.iface, "distance", mapPoint, radius, precision )
			
	def snapToLayers(self, pixPoint, dfltPoint=None):
		if not self.snapping:
			return None
		result,snappingResults = QgsMapCanvasSnapper(self.canvas).snapToBackgroundLayers(pixPoint,[])
		if result == 0 and len(snappingResults)>0:
			return QgsPoint(snappingResults[0].snappedVertex)
		else:
			return dfltPoint