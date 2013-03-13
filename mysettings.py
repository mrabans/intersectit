"""
Plain Geometry Editor
QGIS plugin

Denis Rouzaud
denis.rouzaud@gmail.com
Jan. 2013
"""
from qgistools.pluginsettings.pluginsettings import PluginSettings

from PyQt4.QtGui import QColor,QDialog

from ui.ui_settings import Ui_Settings

class MySettings(PluginSettings):
	def __init__(self,uiObject=None):
		PluginSettings.__init__(self, "intersectit",uiObject)
		self.addSetting("obs_snapping", "global", "bool", True)
		self.addSetting("intersect_result_confirm", "global", "bool", True)
		self.addSetting("intersect_select_tolerance", "global", "double", 0.3)
		self.addSetting("intersect_select_units", "global", "string", "map")
		
		
		
		self.addSetting("intersect_result_placePoint", "project", "bool", False)
		self.addSetting("intersect_result_placeReport", "project", "bool", False)
		
		
		self.addSetting("memoryLineLayer", "project", "string", "")
		self.addSetting("memoryPointLayer", "project", "string", "")

		

class MySettingsDialog(QDialog, Ui_Settings):
	def __init__(self):
		QDialog.__init__(self)
