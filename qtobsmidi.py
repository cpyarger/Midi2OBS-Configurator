# This Python file uses the following encoding: utf-8
from __future__ import division
from sys import exit, stdout
from os import path
from time import time, sleep
import logging, json, mido, base64
try:
   from dbj import dbj
except ImportError:
   print("Could not import dbj. Please install it using 'pip install dbj'")
from PySide2.QtCore import Signal, Slot, QObject
from PySide2.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtWidgets,QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import   pyqtSlot, pyqtSignal
import  sys,  signal
from tinydb import TinyDB, Query
import asyncio
from websocket import WebSocketApp, create_connection
import obswebsocket, obswebsocket.requests
from obswebsocket import obsws, events, requests  # noqa: E402

import tracemalloc

tracemalloc.start()

TEMPLATES = {
"ToggleSourceVisibility": """{
 "request-type": "GetSceneItemProperties",
 "message-id": "%d",
 "item": "%s"
}""",
"ReloadBrowserSource": """{
 "request-type": "GetSourceSettings",
 "message-id": "%d",
 "sourceName": "%s"
}""",
"ToggleSourceFilter": """{
 "request-type": "GetSourceFilterInfo",
 "message-id": "%d",
 "sourceName": "%s",
 "filterName": "%s"
}"""
}

SCRIPT_DIR = path.dirname(path.realpath(__file__))
record=False
####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
password="banana"
####
rowNumber=0
database = TinyDB("config.json", indent=4)
db = database.table("keys", cache_size=0)
inpType = ["Button", "Fader"]
devdb = database.table("devices", cache_size=0)
buttonActions = ["SetCurrentScene", "SetPreviewScene", "TransitionToProgram", "SetCurrentTransition", "SetSourceVisibility", "ToggleSourceVisibility", "ToggleMute", "SetMute",
                 "StartStopStreaming", "StartStreaming", "StopStreaming", "StartStopRecording", "StartRecording", "StopRecording", "StartStopReplayBuffer",
                 "StartReplayBuffer", "StopReplayBuffer", "SaveReplayBuffer", "PauseRecording", "ResumeRecording", "SetTransitionDuration", "SetCurrentProfile","SetCurrentSceneCollection",
                 "ResetSceneItem", "SetTextGDIPlusText", "SetBrowserSourceURL", "ReloadBrowserSource", "TakeSourceScreenshot", "EnableSourceFilter", "DisableSourceFilter", "ToggleSourceFilter"]

faderActions = ["SetVolume", "SetSyncOffset", "SetSourcePosition", "SetSourceRotation", "SetSourceScale", "SetTransitionDuration", "SetGainFilter"]

jsonArchive = {"SetCurrentScene": """{"request-type": "SetCurrentScene", "message-id" : "1", "scene-name" : "%s"}""",
               "SetPreviewScene": """{"request-type": "SetPreviewScene", "message-id" : "1","scene-name" : "%s"}""",
               "TransitionToProgram": """{"request-type": "TransitionToProgram", "message-id" : "1"%s}""",
               "SetCurrentTransition": """{"request-type": "SetCurrentTransition", "message-id" : "1", "transition-name" : "%s"}""",
               "StartStopStreaming": """{"request-type": "StartStopStreaming", "message-id" : "1"}""",
               "StartStreaming": """{"request-type": "StartStreaming", "message-id" : "1"}""",
               "StopStreaming": """{"request-type": "StopStreaming", "message-id" : "1"}""",
               "StartStopRecording": """{"request-type": "StartStopRecording", "message-id" : "1"}""",
               "StartRecording": """{"request-type": "StartRecording", "message-id" : "1"}""",
               "StopRecording": """{"request-type": "StopRecording", "message-id" : "1"}""",
               "ToggleMute": """{"request-type": "ToggleMute", "message-id" : "1", "source": "%s"}""",
               "SetMute": """{"request-type": "SetMute", "message-id" : "1", "source": "%s", "mute": %s}""",
               "StartStopReplayBuffer": """{"request-type": "StartStopReplayBuffer", "message-id" : "1"}""",
               "StartReplayBuffer": """{"request-type": "StartReplayBuffer", "message-id" : "1"}""",
               "StopReplayBuffer": """{"request-type": "StopReplayBuffer", "message-id" : "1"}""",
               "SaveReplayBuffer": """{"request-type": "SaveReplayBuffer", "message-id" : "1"}""",
               "SetTransitionDuration": """{"request-type": "SetTransitionDuration", "message-id" : "1", "duration": %s}""",
               "SetVolume": """{"request-type": "SetVolume", "message-id" : "1", "source": "%s", "volume": "%s"}""",
               "SetSyncOffset": """{"request-type": "SetSyncOffset", "message-id" : "1", "source": "%s", "offset": %s}""",
               "SetCurrentProfile": """{"request-type": "SetCurrentProfile", "message-id" : "1", "profile-name": "%s"}""",
               "SetCurrentSceneCollection": """{"request-type": "SetCurrentSceneCollection", "message-id" : "1", "sc-name": "%s"}""",
               "ResetSceneItem": """{"request-type": "ResetSceneItem", "message-id" : "1", "item": %s}""",
               "SetTextGDIPlusText": """{"request-type": "SetTextGDIPlusProperties", "message-id" : "1", "source": "%s", "text": "%s"}""",
               "SetBrowserSourceURL": """{"request-type": "SetBrowserSourceProperties", "message-id" : "1", "source": "%s", "url": "%s"}""",
               "SetSourcePosition": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "position": {"%s": %s}}""",
               "SetSourceRotation": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "rotation": %s}""",
               "SetSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "ToggleSourceVisibility": """{"request-type": "SetSceneItemProperties", "message-id" : "1", "item": "%s", "visible": %s}""",
               "SetSourceScale": """{{"request-type": "SetSceneItemProperties", "message-id" : "1", "scene-name": "%s", "item": "%s", "scale": {{"%s": %s}}}}""",
               "ReloadBrowserSource": """{"request-type": "SetBrowserSourceProperties", "message-id" : "1", "source": "%s", "url": "%s"}""",
               "TakeSourceScreenshot": """{"request-type": "TakeSourceScreenshot", "message-id" : "MIDItoOBSscreenshot","sourceName" : "%s", "embedPictureFormat": "png"}""",
               "SetGainFilter": """{"request-type": "SetSourceFilterSettings", "message-id" : "1","sourceName" : "%s", "filterName": "%s", "filterSettings": {"db": %s}}""",
               "EnableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": true, "message-id": "MIDItoOBS-EnableSourceFilter"}""",
               "DisableSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": false, "message-id": "MIDItoOBS-DisableSourceFilter"}""",
               "PauseRecording": """{"request-type": "PauseRecording", "message-id" : "MIDItoOBS-PauseRecording"}""",
               "ResumeRecording": """{"request-type": "ResumeRecording", "message-id" : "MIDItoOBS-ResumeRecording"}""",
               "ToggleSourceFilter": """{"request-type": "SetSourceFilterVisibility", "sourceName": "%s", "filterName": "%s", "filterEnabled": %s, "message-id": "MIDItoOBS-EnableSourceFilter"}"""}

actionList   = {"StartStopReplayBuffer":     [0],
                "StartReplayBuffer":         [0],
                "StopReplayBuffer":          [0],
                "SaveReplayBuffer":          [0],
                "SetTransitionDuration":     [0],                                 # <=duration
                "StartStopStreaming":        [0],
                "StartStreaming":            [0],
                "StopStreaming":             [0],
                "StartStopRecording":        [0],
                "StartRecording":            [0],
                "StopRecording":             [0],
                "PauseRecording":            [0],
                "ResumeRecording":           [0],
                "TakeSourceScreenshot":      [1,  'source',                       "self.Make.SourceSelector(row, col, extra)"],                                                               # Source
                "ToggleMute":                [1,  'source',                       "self.Make.SourceSelector(row, col, extra)"],                                                               # Source
                "SetVolume":                 [1,  'source',                       "self.Make.VolumeSelector(row, col, extra)"],                                                               # source <-volume
                "SetCurrentScene":           [1,  'scene-name',                   "self.Make.SceneSelector(row, col, extra)"],                                                         # Scene
                "SetPreviewScene":           [1,  'scene-name',                   "self.Make.SceneSelector(row, col, extra)"],                                                         # Scene
                "TransitionToProgram":       [1,  'scene-name',                   "self.Make.SceneSelector(row, col, extra)"],                                                         # Scene
                "SetCurrentTransition":      [1,  'transition',                   "self.Make.TransitionSelector(row, col, extra)"],                                                    # Scenee1,   # Transition
                "SetCurrentProfile":         [1,  'profile',                      "self.Make.ProfileSelector(row, col, extra)"],                                                       # Profile
                "SetCurrentSceneCollection": [1,  'sc-name',                      "self.Make.SceneCollectionSelector(row, col, extra)"],                                               # sc-name
                "ResetSceneItem":            [1,  'item',                         "self.Make.ItemSelector(row, col, extra)"],                                                          # Item
                "SetMute":                   [2,  'source', 'bool',               "self.Make.VolumeSelector(row, col, extra)",                    "self.Make.Checkbox(row,col)"],              # Source, bool
                "SetSyncOffset":             [2,  'source', 'offset',             "self.Make.SourceSelector(row, col, extra)",                    "self.Make.OffsetSelector(row,col)"],        # Source, Offset
                "ReloadBrowserSource":       [2,  'source', 'url',                "self.Make.SourceSelector(row, col, extra)",                    "self.Make.URLSelector(row,col)"    ],       # Source, URL
                "EnableSourceFilter":        [2,  'source', 'filter',             "self.Make.SourceSelector(row, col, extra)",                    "self.Make.FilterSelector(row,col)",],       # Source, Filter
                "DisableSourceFilter":       [2,  'source', 'filter',             "self.Make.SourceSelector(row, col, extra)",                    "self.Make.FilterSelector(row,col)",],       # Source, Filter
                "SetTextGDIPlusText":        [2,  'source', 'text',               "self.Make.SourceSelector(row, col, extra)",                    "self.Make.TextboxSelector(row,col)"],            # Source, Text
                "SetBrowserSourceURL":       [2,  'source', 'url',                "self.Make.SourceSelector(row, col, extra)",                    "self.Make.URLSelector(row,col)"],           # Source, URL
                "SetSourceVisibility":       [2,  'item', 'bool',                 "self.Make.ItemSelector(row, col, extra)",                      "self.Make.Checkbox(row,col)"],              # Item, Bool(visible)
                "ToggleSourceVisibility":    [2,  'item', 'bool',                 "self.Make.ItemSelector(row, col, extra)",                      "self.Make.Checkbox(row,col)"],              # Item, Bool(visible)
                "SetSourceScale":            [3,  'source', 'item', 'scale',      "self.Make.SourceSelector(row, col, extra)",                    "self.Make.ItemSelector(row, col, extra)",   "self.makeScaleSelector(row,col)"],      # Scene, Item, Scale
                "SetSourcePosition":         [3,  'source', 'item', 'position',   "self.Make.SourceSelector(row, col, extra)",                    "self.Make.ItemSelector(row, col, extra)",   "self.makePositionSelector(row,col)"],   # Scene, Item, Position
                "SetSourceRotation":         [3,  'source', 'item', 'rotation',   "self.Make.SourceSelector(row, col, extra)",                    "self.Make.ItemSelector(row, col, extra)",   "self.makeRotationSelector(row,col)"],   # Scene, Item, Rotation
                "SetGainFilter":             [3,  'source', 'filter', 'db',       "self.Make.SourceSelector(row, col, extra)",                    "self.Make.FilterSelector(row,col)",         "self.makeDBSelector(row,col)"],         # SOurce, Filter, Setting.DB
                "ToggleSourceFilter":        [3,  'source', 'filter', 'bool',     "self.Make.SourceSelector(row, col, extra)",                    "self.Make.FilterSelector(row,col)",         "self.makeCheckbox(row,col)"]            # Source, Filter, <-Bool
}
rowTemplate = { 1   :   "msg_type"      ,
                2   :   "msgNoC"        ,
                3   :   "input_type"    ,
                4   :   "request-type"  ,
                5   :   "deviceID"      ,
                6   :   "option"
                }
sceneListShort = []
sceneListLong = []
sourceListShort = []
sourceListLong = []
transitionList = []
specialSourcesList = []
profilesList = []
sceneCollectionList = []
gdisourcesList = []
gainList=[]
value = ""
note = ""
midiports = []
btnStart=False
import ast
ignore = 255
try:
    import thread
except ImportError:
    import _thread as thread
class handler(QtCore.QObject):
    closed=pyqtSignal()
    SendMessage=pyqtSignal(str,str,name="SendMessage")
    def handle(self,message):
        #logging.debug(str(message))

        #logging.debug(message.type)

        if message.type == "note_on":
            if  entryExists(message.note)!=True:
                self.SendMessage.emit( "note_on", str(message.note))
        elif message.type == "control_change":
            if entryExists(message.control)!=True:
                self.SendMessage.emit( "control_change", str(message.control))
    def connectToDevice(self):
        devices = devdb.all()
        #multi=Multi.MultiPort(devices,yield_ports=True)
        #multi.callback(callback=midi.handle)

        for device in devices: #gave up on documentation here
            try:
                #logging.debug("device name "+device["devicename"])
                tempmidiport = mido.open_input(device["devicename"],callback=midi.handle)
                tempobj = {"id": device.doc_id, "object": tempmidiport, "devicename": device["devicename"]}
                midiports.append(tempobj)
                #logging.debug("successfully opened" + str(device["devicename"]))
            except:
                logging.debug("\nCould not open", str(device["devicename"]))
                #QtWidgets.QMessageBox.Critical(self, "Could not open", "The midi device might be used by another application/not plugged in/have a different name.")
                database.close()
                #sys.exit(5)


class EditTable():
    rowNumber=0
    Update=None
    Make=None
    #define row dropdowns
    def __init__(self, form):
        self.Make=self.MAKE(form, EditTable)
        self.Update=self.UPDATE(form)
        result = db.all()
        self.rowNumber=rowNumber
        for rowNumbers, RowData in enumerate (result):
            res = ast.literal_eval(RowData["action"])
            x=actionList[res["request-type"]]
            option="".join(res[x[x[0]]])
            self.addRow(str(RowData["msg_type"]),str(RowData["msgNoC"]),str(RowData["input_type"]),str(res["request-type"]),str(RowData["deviceID"]),option)
        self.table()


    class UPDATE():
        def __init__(self, form):
            logging.info("make update")

        def UpdateSourceList(self):
            logging.info("updateSourceList")
        def UpdateSceneList(self):
            logging.info("updateSourceList")
        def UpdateFilterList(self):
            logging.info("updateSourceList")
        def UpdateItemList(self):
            logging.info("updateSourceList")
        def UpdateTransitionList(self):
            logging.info("updateSourceList")
        def UpdateProfileList(self):
            logging.info("updateSourceList")

    class MAKE():
        def __init__(self, form, EditTable):
            logging.info("Create Make Class")
        def MsgTypeSelector(self, msg):
            drop_msg_type=QtWidgets.QComboBox()
            drop_msg_type.insertItems(0, ["control_change", "program_change", "note_on"])
            x=drop_msg_type.findText(msg, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            drop_msg_type.setCurrentIndex(x)
            return drop_msg_type
        def ActionSelector(self, type, *action):
            #logging.debug("Setting up actions")
            drop_msg_type=QtWidgets.QComboBox()
            counter=0
            if type == "button":
                for each in buttonActions:
                    drop_msg_type.addItem(str(each))
                    counter+=1
            elif type== "fader":
                for each in faderActions:
                    drop_msg_type.addItem(str(each))
                    counter+=1
            if action:
                x=drop_msg_type.findText(action[0], QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                drop_msg_type.setCurrentIndex(x)
            drop_msg_type.currentIndexChanged.connect(EditTable.updateAction)
            return drop_msg_type
        def SceneSelector(self,row, col=5,*existing):
            sceneCombo=QtWidgets.QComboBox()
            for scene in sceneListShort:
                sceneCombo.addItem(scene)
            if existing:
                a=str(existing[0][0])
                logging.info(a)
                x=sceneCombo.findText(a, QtCore.Qt.MatchStartsWith | QtCore.Qt.MatchRecursive)
                sceneCombo.setCurrentIndex(x)

            sceneCombo.setCurrentIndex(0)
            sceneCombo.currentIndexChanged.connect(EditTable.updateAction)
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,col,sceneCombo)
            return sceneCombo
        def SourceSelector(self, row, col=5, *existing):
            sceneCombo=QtWidgets.QComboBox()
            for source in sourceListShort:
                #logging.debug(line)
                sceneCombo.addItem(source)
                #logging.debug(scene)

            sceneCombo.currentIndexChanged.connect(editTable.updateAction)
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,col,sceneCombo)
        def BrowserSourceSelector(self, row, col, *existing):
            sceneCombo=QtWidgets.QComboBox()
            for source in sourceListShort:
                #logging.debug(line)
                sceneCombo.addItem(source)
                #logging.debug(scene)
            if existing:
                logging.info("existing = "+ existing[0])
                x=sceneCombo.findText(existing[0], QtCore.Qt.MatchStartsWith | QtCore.Qt.MatchRecursive)
                sceneCombo.setCurrentIndex(x)

            sceneCombo.currentIndexChanged.connect(editTable.updateAction)
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,col,sceneCombo)
        def InputDeviceList(self,*existing):
            deviceCombo=QtWidgets.QComboBox()
            inputs=mido.get_input_names()
            for each in inputs:
                deviceCombo.addItem(str(each))
            if existing:
                deviceCombo.setCurrentIndex(int(existing[0])-1)
            return deviceCombo
        def MakeOutputDeviceList(self, *existing):
            deviceCombo=QtWidgets.QComboBox()
            inputs=mido.get_input_names()
            for each in inputs:
                deviceCombo.addItem(str(each))
            if existing:
                deviceCombo.setCurrentIndex(int(existing[0])-1)
            return deviceCombo
        def VolumeSelector(self, row, col=5, *existing):
            volumeCombo=QtWidgets.QComboBox()
            for item in specialSourcesList:
                volumeCombo.addItem(str(item))
            if existing:
                x=volumeCombo.findText(str(existing[0]), QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
                volumeCombo.setCurrentIndex(x)
            volumeCombo.setCurrentIndex(0)
            volumeCombo.currentIndexChanged.connect(EditTable.updateAction)
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,col,volumeCombo)
        def ProfileSelector(self,*existing):
            logging.debug("Setting up profiles")
        def TransitionsSelector(self,*existing):
            logging.debug("Setting up transitions")
        def Checkbox(self, row, col=6, *existing):
            logging.info("make checkbox")
        def add_input_type_drop(self, msg):
            x=0

            drop_msg_type=QtWidgets.QComboBox()
            drop_msg_type.insertItems(0, ["button", "fader"])
            x=drop_msg_type.findText(msg, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            drop_msg_type.setCurrentIndex(x)
            drop_msg_type.currentIndexChanged.connect(EditTable.updateAction)
            return drop_msg_type


    def disableCombo(self, Combo):
        Combo.setEnabled(False)
        return Combo

    def enableCombo(self,Combo):
        Combo.setEnabled(True)
    def saveTable(self, *options):
        logging.debug(options)
        #This function iterates through table, and switches between Sending SaveFaderToFile and saveButtonToFile based on inputType
        logging.debug("Save Table")
        table=form.list_action
        rowcount=table.rowCount()
        irow=0
        arg=0
        #iterate through rows
        while irow < rowcount:

            msg_type   = table.cellWidget(irow, 0).currentText()
            msgNoC     = table.item(irow, 1).text()
            input_type = table.cellWidget(irow, 2).currentText()
            deviceID   = table.cellWidget(irow, 3).currentIndex()
            action     = table.cellWidget(irow, 4).currentText()
            try:
                cmd    = table.cellWidget(irow, 5).currentText()
                try:
                    scale  = table.cellWidget(irow, 6).currentText()
                    if scale =="":
                        arg=1
                        scale=(0,1)
                    else:
                        arg=2
                except:
                    if cmd =="":
                        arg=0
                    else:
                        arg=1

            except:
                arg=0
                logging.debug("no values")

            logging.debug(str(irow)+ ": "+str(msg_type))
            logging.debug(arg)

            #logging.debug(str(irow)+ ": "+str(msgNoC))
            #logging.debug(str(irow)+ ": "+str(input_type))
            #logging.debug(str(irow)+ ": "+str(action))
            #logging.debug(str(irow)+ ": "+str(scale))
            #logging.debug(str(irow)+ ": "+str(cmd))
            #logging.debug(str(irow)+ ": "+str(deviceID))
            irow+=1

                #set save variables
            if arg==2:
                self.newFaderSetup(action, int(msgNoC), msg_type, deviceID, cmd, scale)
            elif arg==1:
                self.newFaderSetup(action, int(msgNoC), msg_type, deviceID,cmd, scale)

            elif arg==0:
                self.setupButtonEvents(self, action, int(msgNoC), msg_type, deviceID)

                #save
            #move to next row

    def saveFaderToFile(self, msg_type, msgNoC, input_type, action, scale, cmd, deviceID ):
        logging.debug("Saved %s with control %s for action %s on device %s" % (msg_type, msgNoC, cmd, deviceID))
        Search = Query()
        result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        if result:
            db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": int(scale[0]), "scale_high": int(scale[1]), "action": action, "cmd": cmd, "deviceID": deviceID})
        else:
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": int(scale[0]), "scale_high": int(scale[1]), "action": action, "cmd": cmd, "deviceID": deviceID})

    def saveButtonToFile(self, msg_type, msgNoC, input_type, action, deviceID):
        # note_on, 20, button, action, deviceID
        logging.debug("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
        Search = Query()
        result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        if result:
            db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})
        else:
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})


    def table(self):
        self.tableWidget = form.list_action
    def SetupOptions(self,action,row, col, extra="None"):
        #Grab Action List)
        x=actionList[action]
        #Get the Number of blank slots and insert them
        Blanks=3-x[0]
        self.insertblank(Blanks)
        actnum=0
        while actnum < x[0]:
            y=x[0]+actnum+1
            act=x[y]
            actnum+=1
            return eval(act)





    def GainFilter(self, row, col, source):
        text=form.list_action.cellWidget(row, 5).currentText()
    # Inserts blank disabled comboboxes into table when needed
    def insertblank(self, num):
        combo=QtWidgets.QComboBox()
        combo2=QtWidgets.QComboBox()
        combo3=QtWidgets.QComboBox()
        if num == 1:
            form.list_action.setItem(self.rowNumber,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,7, combo)
            self.disableCombo(combo)
            self.enableCombo(combo2)
            self.enableCombo(combo3)
        elif num == 2:
            form.list_action.setItem(self.rowNumber,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,7, combo2)
            form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,6, combo3)
            self.enableCombo(combo)
            self.disableCombo(combo2)
            self.disableCombo(combo3)
        elif num ==3:
            form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,5, combo)
            form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,6, combo)
            form.list_action.setItem(self.rowNumber,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,7, combo)
            self.disableCombo(combo)
            self.disableCombo(combo2)
            self.disableCombo(combo3)

    # Updates each field in table when a new option is chosen.
    @Slot(int)
    def updateAction(self):
        x=form.list_action.selectedItems()
        row=0
        text=""
        for each in x:
            row=each.row()
            col=each.column()
            text=form.list_action.cellWidget(row, col).currentText()
            logging.info("Change in col: "+str(col))
            if col==2:
                logging.info("Changed Input type")
                form.list_action.setItem(row,4,QtWidgets.QTableWidgetItem())
                form.list_action.setCellWidget(row,4, self.MakeActionSelector(text))
                if text =="fader":
                    self.SetupOptions("SetVolume", row, 5 )
                elif text=="button":
                    self.SetupOptions("SetCurrentScene", row,5)
            elif col ==4: #action
                logging.info("Changed action")
                action=form.list_action.cellWidget(row, 4).currentText()
                self.SetupOptions(action,row,5)

            elif col ==5:
                logging.info("Changed Option 1")

            elif col ==6:
                logging.info("Changed Option 2")
            elif col ==7:
                logging.info("Changed Option 3")




    def GetCurrentScene(self):
        ws = create_connection("ws://" + serverIP + ":" + serverPort)
        ws.send('{"request-type": "GetCurrentScene","message-id": "MIDItoOBS-checksourcegainfilter"}')
        result =  ws.recv()
        ws.close()
        jsn = json.loads(result)
        return str(jsn["name"])

    #for Initial Rows
    def addRow(self, mtype, msgNoC, inputType, action, deviceID, *option):
        rowNumber=self.rowNumber
        form.list_action.insertRow(self.rowNumber)

        form.list_action.setItem(self.rowNumber,0,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,0, self.Make.MsgTypeSelector(mtype))


        x= QtWidgets.QTableWidgetItem(msgNoC)
        x.setTextAlignment(QtCore.Qt.AlignCenter)

        form.list_action.setItem(self.rowNumber,1,x)

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        combo=self.Make.add_input_type_drop(inputType)
        combo.currentIndexChanged.connect(self.updateAction)
        form.list_action.setCellWidget(self.rowNumber,2, combo)


        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.Make.ActionSelector(inputType, action))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.Make.InputDeviceList(deviceID))



        if option:
            self.SetupOptions(action,self.rowNumber,5,option)



        self.rowNumber=+1

    @Slot(str, str,int)
    def AddNewRow(self, msg_type, msgNoC,deviceID=1):
        form.list_action.insertRow(self.rowNumber)

        inputType=""
        option=""
        if msg_type=="control_change":
            inputType="fader"
            option="SetVolume"
        elif msg_type == "note_on":
            inputType = "button"
            option="SetCurrentScene"

        form.list_action.setItem(self.rowNumber,0,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,0, editTable.MakeMsgTypeSelector(msg_type))

        form.list_action.setItem(self.rowNumber,1,QtWidgets.QTableWidgetItem(msgNoC))

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,2, editTable.add_input_type_drop(inputType, self.rowNumber))

        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.MakeActionSelector(inputType))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.MakeInputDeviceList(deviceID))

        form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,5, self.SetupOptions(inputType, option[0]))

        form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem(str(rowNumber)))

        self.rowNumber+=1

class qtobsmidi(QMainWindow):
    def currentIndexChanged(self, qmodelindex):
            item = self.InputTypeSelector.currentItem()
            logging.debug(str(item.index()))
    def __init__(self):
        QMainWindow.__init__(self)


class newobs():
    def __init__(self, host = "localhost", port= 4444, password= "banana"):
        self.ws = obsws(host, port)
        #self.ws.register(self.on_event)
        #self.ws.register(self.on_switch, events.SwitchScenes)
        QApplication.processEvents()
        logging.debug("Setup OBS")


    def connect(self):
        logging.debug("Connecting to OBS")
        QApplication.processEvents()

        self.ws.connect()

        return True

    def disconnect(self):
        QApplication.processEvents()
        self.ws.disconnect()

    def on_event(self, message):
        QApplication.processEvents()
        logging.debug(u"Got message: {}".format(message))
    def on_switch(self, message):
        logging.debug(u"You changed the scene to {}".format(message.getSceneName()))
    def getSpecialSources(self):
        sources=specialSourcesList
        scenes = self.ws.call(requests.GetSpecialSources())
        #logging.debug(scenes    )
        try:
            scenes.getDesktop1()

        except:
            logging.debug("test failed")
        else:
            sources.append(scenes.getDesktop1())
        try:
            scenes.getDesktop2()
        except:
            logging.debug("desk 2 input failed")
        else:
            sources.append(scenes.getDesktop2())
        try:
            scenes.getDesktop3()
        except:
            logging.debug("desk 3 input failed")
        else:
            sources.append(scenes.getDesktop3())
        try:
            scenes.getDesktop4()
        except:
            logging.debug("desk 4 input failed")
        else:
            sources.append(scenes.getDesktop4())
        try:
            scenes.getDesktop5()
        except:
            logging.debug("desk 5 input failed")
        else:
            sources.append(scenes.getDesktop5())
        try:
            scenes.getMic1()
        except:
            logging.debug("mic1 failed")
        else:
            sources.append(scenes.getMic1())
        try:
            scenes.getMic2()
        except:
            logging.debug("Mic 2 input failed")
        else:
            sources.append(scenes.getMic2())
        try:
            scenes.getMic3()
        except:
            logging.debug("mic 3 input failed")
        else:
            sources.append(scenes.getMic3())
        try:
            scenes.getMic4()
        except:
            logging.debug("mic 4 input failed")
        else:
            sources.append(scenes.getMic4())
        try:
            scenes.getMic5()
        except:
            logging.debug("mic 5 input failed")
        else:
            sources.append(scenes.mic5())
        #logging.debug(sources)
        return sources
    def test(self):
        logging.debug("test")
        self.getSourceList()
    def getscenelist(self):
        try:
            scenes = self.ws.call(requests.GetSceneList())
            sceneListLong.clear()
            sceneListShort.clear()
            #logging.debug(scenes)
            for each in scenes.getScenes():
                #logging.debug(each['name'])
                sceneListLong.append(each)
                sceneListShort.append(each["name"])


        except:
            logging.debug("unable to get scenes")
    def getSourceList(self):
        sources = self.ws.call(requests.GetSourcesList())
        for each in sources.getSources():
            logging.info(each)
            sourceListLong.append(each)
            sourceListShort.append(each["name"])
    def getSourceTypesList(self):
        sources = self.ws.call(requests.GetSourceTypesList())
        for each in sources.getTypes():
            if each['caps']['hasAudio'] == True:
                specialSourcesList.append(each['displayName'])
def ResetMidiController():
    outport= mido.open_output("X-TOUCH COMPACT 1")
    counter=0
    counter2=0
    counter3=26
    while counter <=39:
        x=mido.Message("note_off", note=counter)
        outport.send(x)
        counter+=1
    while counter2 <=9:
        x=mido.Message("control_change", control=counter2,value=0)
        outport.send(x)
        counter2+=1
    while counter3 <=41:
        x=mido.Message("control_change", control=counter3,value=0)
        outport.send(x)
        counter3+=1
def myExitHandler():
    logging.debug("kill application")

    app.quit
    #sys.exit(app.exec_())
def startStopBtnHandle():
    global btnStart
    if btnStart == False:
       startOBSconnection()
       form.btn_Start.setText("Stop")
       btnStart = True
    elif btnStart == True:
        stopOBSconnection()
        form.btn_Start.setText("Start")
        btnStart = False
def startOBSconnection():
    tray.showMessage("Connecting","Connecting to OBS",icon)
    OBS.connect()
def stopOBSconnection():
    OBS.disconnect()
    tray.showMessage("Disconnecting","disconnecting from OBS",icon)
def map_scale(inp, ista, isto, osta, osto):
    return osta + (osto - osta) * ((inp - ista) / (isto - ista))
def get_logger( level=logging.debug):
   log_format = logging.Formatter('[%(asctime)s] (%(levelname)s) T%(thread)d : %(message)s')
   std_output = logging.StreamHandler(stdout)
   std_output.setFormatter(log_format)
   std_output.setLevel(level)
   file_output = logging.FileHandler(path.join(SCRIPT_DIR, "debug.log"))
   file_output.setFormatter(log_format)
   file_output.setLevel(level)
   logger = logging.getLogger()
   logger.setLevel(logging.DEBUG)
   logger.addHandler(file_output)
   logger.addHandler(std_output)
   return logger




def entryExists(value):
    x=form.list_action.findItems(str(value), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
    if x!=[]:
        return True
    else:
        return False

    #used for connecting Midi to obs for actually controlling OBS
            #logging.info(str(each['hasAudio']))

def ScriptExit(signal, frame):
    logging.debug("Closing midi ports...")
    for port in midiports:
        port["object"].close()
    logging.debug("Closing database...")
    database.close()
    logging.debug("Exiting...")
    sys.exit(0)
if __name__ == "__main__":
    get_logger(logging.INFO)
    signal.signal(signal.SIGINT, ScriptExit)
    Form, Window = uic.loadUiType("qtOBSMIDI.ui")

    app = QApplication(sys.argv)
    window = Window()
    form = Form()
    form.setupUi(window)
    window.show()
    logging.debug("Program Startup")


    #initialize table

    # Setup external MidiToOBS Script

    OBS=newobs()
    OBS.connect()
    OBS.getscenelist()
    OBS.getSpecialSources()
    OBS.getSourceList()
    OBS.getSourceTypesList()
    midi=handler()
    editTable=EditTable(form)

    #logging.debug(midiports)
    #ResetMidiController()

    #Setup System Tray
    icon = QIcon("icon.png")
    Menu=QtWidgets.QMenu()
    tray=QtWidgets.QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setContextMenu(Menu)
    actionStart=Menu.addAction("start")
    actionStop=Menu.addAction("Stop")
    actionQuit=Menu.addAction("Quit")

    #Setup signal/slot connections
    app.aboutToQuit.connect(myExitHandler)
    actionStart.triggered.connect(startStopBtnHandle)
    actionStop.triggered.connect(stopOBSconnection)
    midi.SendMessage.connect(editTable.AddNewRow)
    actionQuit.triggered.connect(app.quit)
    form.btn_SaveTable.clicked.connect(editTable.saveTable)
    form.btn_Start.clicked.connect(startStopBtnHandle)
    form.btn_test.clicked.connect(OBS.test)

    #Setup Connection for adding to table
    #midi.SendMessage.connect(editTable.testing)

    #form.list_action.itemSelectionChanged.connect(editTable.updateAction)
    #form.list_action.itemSelectionChanged.connect(editTable.updateAction)



    tray.show()
    midi.connectToDevice()
    sys.exit(app.exec_())
    #logging.debug(actionQuit)

    #editTable.MakeinputDeviceList()



