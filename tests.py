import sys
import unittest
from copy import deepcopy

from PyQt6.QtWidgets import QApplication

from lib.pv_item import PVItem
from lib.pv_editor import PVEditor
from lib.clock import Clock
        
class PVItemTest(unittest.TestCase):
    NAME = "dummy_pv_0"
    COLOR = "#123456"
    SUBPLOT_ID = 10
    KWARGS = {"original": {'enabled': False},
            "rolling_window": {'enabled': True, 'window': 7, 'center': True, 'closed': 'right'},
            "ewm": {'enabled': False, 'com': None, 'span': None, 'halflife': 0.5, 'alpha': None, 'adjust': True},
            "adaptive": {'enabled': True, 'phase_threshold': 2.3, 'n_avg': 10}}

    def updateSingleParamTest(self):
        # NAME
        item = PVItem()
        item.updateParams({"name": self.NAME})
        self.assertEqual(self.NAME, item.params["name"])
        self.assertEqual(f"{self.NAME}'s Parameters", item.param_dialog.windowTitle())
        
        # COLOR
        item = PVItem()
        item.updateParams({"color": self.COLOR})
        self.assertEqual(self.COLOR, item.params["color"])
        self.assertEqual(self.COLOR, item.param_dialog.palette_button.color)
        
        # SUBPLOT ID
        item = PVItem()
        item.updateParams({"subplot_id": self.SUBPLOT_ID})
        self.assertEqual(self.SUBPLOT_ID, item.params["subplot_id"])
        self.assertEqual(self.SUBPLOT_ID, item.param_dialog.subplot_id_spinbox.value())
        
        # KWARGS
        item = PVItem()
        item.updateParams({"kwargs": self.KWARGS})
        self.assertEqual(self.KWARGS, item.params["kwargs"])
        self.assertEqual(self.KWARGS, item.param_dialog.tree.getKwargs())
        
    def updateParamsTest(self):
        test_params = {"name": self.NAME, "color": self.COLOR, "subplot_id": self.SUBPLOT_ID, "kwargs": self.KWARGS}
        test_params_copy = deepcopy(test_params)  # to test ParamDialog.getParams()
        del test_params_copy["name"]
        
        # PARAM SUBSET
        item = PVItem()
        item.updateParams({"color": self.COLOR, "subplot_id": self.SUBPLOT_ID})
        self.assertEqual(self.COLOR, item.params["color"])
        self.assertEqual(self.COLOR, item.param_dialog.palette_button.color)
        self.assertEqual(self.SUBPLOT_ID, item.params["subplot_id"])
        self.assertEqual(self.SUBPLOT_ID, item.param_dialog.subplot_id_spinbox.value())
        
        # ALL PARAMS
        item = PVItem()
        item.updateParams(test_params)
        self.assertEqual(test_params, item.params)
        self.assertEqual(f"{test_params['name']}'s Parameters", item.param_dialog.windowTitle())
        self.assertEqual(test_params['color'], item.param_dialog.palette_button.color)
        self.assertEqual(test_params['subplot_id'], item.param_dialog.subplot_id_spinbox.value())
        self.assertEqual(test_params['kwargs'], item.param_dialog.tree.getKwargs())
        self.assertEqual(test_params_copy, item.param_dialog.getParams())
        
    def runTest(self):
        self.updateSingleParamTest()
        self.updateParamsTest()


class PVEditorTest(unittest.TestCase):
    ADD_ITEM_CALL_COUNT = 5
    DEFAULT_ITEM_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                           "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

    def runTest(self):
        pv_editor = PVEditor()
        
        # ADD ITEMS
        for _ in range(self.ADD_ITEM_CALL_COUNT):
            pv_editor.addItem()
        self.assertEqual(self.ADD_ITEM_CALL_COUNT, pv_editor.table.rowCount())
        
        # ITEMS ASSIGNED CORRECT COLOR
        for i, item in enumerate(pv_editor):
            self.assertEqual(self.DEFAULT_ITEM_COLORS[i], item.params["color"])
            
        # CLEAR
        pv_editor.clear()
        self.assertEqual(0, pv_editor.table.rowCount())
        

class ClockTest(unittest.TestCase):
    START_TEXT = "▶"
    STOP_TEXT = "■"
    HZ = 20
    
    def runTest(self):
        clock = Clock()
        
        # TOGGLE
        self.assertFalse(clock.timer.isActive())
        self.assertEqual(self.START_TEXT, clock.toggle_button.text())
        clock.toggle()
        self.assertEqual(self.STOP_TEXT, clock.toggle_button.text())
        self.assertTrue(clock.timer.isActive())
        
        # INTERVAL
        clock.hz_spinbox.setValue(self.HZ)
        self.assertEqual(int(1000 / self.HZ), clock.timer.interval())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    unittest.main()
    sys.exit(app.exec())