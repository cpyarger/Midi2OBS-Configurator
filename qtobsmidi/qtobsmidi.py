#!/usr/bin/python3
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
import asyncws
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
inpType = ["button", "fader"]
devdb = database.table("devices", cache_size=0)

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
                "SetTransitionDuration":     [0],
                "StartStopStreaming":        [0],
                "StartStreaming":            [0],
                "StopStreaming":             [0],
                "StartStopRecording":        [0],
                "StartRecording":            [0],
                "StopRecording":             [0],
                "PauseRecording":            [0],
                "ResumeRecording":           [0],
                "TakeSourceScreenshot":      [1,  'source'                          ],
                "ToggleMute":                [1,  'source'                          ],
                "SetVolume":                 [1,  'source'                          ],
                "SetCurrentScene":           [1,  'scene-name'                      ],
                "SetPreviewScene":           [1,  'scene-name'                      ],
                "TransitionToProgram":       [1,  'scene-name'                      ],
                "SetCurrentTransition":      [1,  'transition'                      ],
                "SetCurrentProfile":         [1,  'profile'                         ],
                "SetCurrentSceneCollection": [1,  'sc-name'                         ],
                "ResetSceneItem":            [1,  'item'                            ],
                "SetMute":                   [2,  'source', 'bool'                  ],
                "SetSyncOffset":             [2,  'source', 'offset'                ],
                "ReloadBrowserSource":       [2,  'source', 'url'                   ],
                "EnableSourceFilter":        [2,  'source', 'filter'                ],
                "DisableSourceFilter":       [2,  'source', 'filter'                ],
                "SetTextGDIPlusText":        [2,  'source', 'text'                  ],
                "SetBrowserSourceURL":       [2,  'source', 'url'                   ],
                "SetSourceVisibility":       [2,  'item',   'bool'                  ],
                "ToggleSourceVisibility":    [2,  'item',   'bool'                  ],
                "SetSourceScale":            [3,  'source', 'item',     'scale'     ],
                "SetSourcePosition":         [3,  'source', 'item',     'position'  ],
                "SetSourceRotation":         [3,  'source', 'item',     'rotation'  ],
                "SetGainFilter":             [3,  'source', 'filter',   'db'        ],
                "ToggleSourceFilter":        [3,  'source', 'filter',   'bool'      ]
}

Actions={  "source"        :   "self.Make.Combo(sourceListShort,                            row, col, extra)"   ,
           "scene-name"    :   "self.Make.Combo(sceneListShort,                             row, col, extra)"   ,
           "transition"    :   "self.Make.Combo(transitionList,                             row, col, extra)"   ,
           'profile'       :   "self.Make.Combo(profilesList,                               row, col, extra)"   ,
           'sc-name'       :   "self.Make.Combo(sceneCollectionList,                        row, col, extra)"   ,
           'item'          :   "self.Make.Combo(itemList,                                   row, col, extra)"   ,
           'bool'          :   "self.Make.Checkbox(                                         row,col)"           ,
           'position'      :   "self.Make.Position(                                         row,col)"           ,
           'rotation'      :   "self.Make.Rotation(                                         row,col)"           ,
           'scale'         :   "self.Make.Scale(                                            row,col)"           ,
           'offset'        :   "self.Make.Offset(                                           row,col)"           ,
           'url'           :   "self.Make.URL(                                              row,col)"           ,
           'db'            :   "self.Make.DB(                                               row,col)"           ,
           'text'          :   "self.Make.TextInput(                                        row,col)"           ,
           'filter'        :   "self.Make.Combo(self.Update.filter(sourceListShort[0]),     row,col)"           }
rowTemplate = { 1   :   "msg_type"      ,
                2   :   "msgNoC"        ,
                3   :   "input_type"    ,
                4   :   "request-type"  ,
                5   :   "deviceID"      ,
                6   :   "option"
                }
ActionsType = {  "button":  [   "SetCurrentScene", "SetPreviewScene",          "TransitionToProgram","SetCurrentTransition","SetSourceVisibility","ToggleSourceVisibility",
                            "ToggleMute", "SetMute", "StartStopStreaming", "StartStreaming","StopStreaming","StartStopRecording","StartRecording",
                            "StopRecording", "StartStopReplayBuffer",      "StartReplayBuffer","StopReplayBuffer","SaveReplayBuffer","PauseRecording",
                            "ResumeRecording", "SetTransitionDuration",    "SetCurrentProfile","SetCurrentSceneCollection","ResetSceneItem","SetTextGDIPlusText",
                            "SetBrowserSourceURL", "ReloadBrowserSource",  "TakeSourceScreenshot","EnableSourceFilter","DisableSourceFilter", "ToggleSourceFilter"
                        ],
            "fader":    [   "SetVolume", "SetSyncOffset", "SetSourcePosition", "SetSourceRotation", "SetSourceScale", "SetTransitionDuration", "SetGainFilter"     ]
            }

makes={}
itemList = {}
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
InList=[]
OutList=[]
filterList=[]
msgType=["control_change", "program_change", "note_on"]
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
class asyncOBS():
    def __init__(self,config_path="config.json", ws_server="localhost", ws_port=4444):

        # Internal service variables
        self._action_buffer = []
        self._action_counter = 2
        self._portobjects = []

        #load tinydb configuration database
        logging.debug("Trying to load config file  from %s" % config_path)
        tiny_database = TinyDB(config_path, indent=4)
        tiny_db = tiny_database.table("keys", cache_size=20)
        tiny_devdb = tiny_database.table("devices", cache_size=20)

        #get all mappings and devices
        self._mappings = tiny_db.all()
        self._devices = tiny_devdb.all()

        #open dbj datebase for mapping and clear
        self.mappingdb = dbj("temp-mappingdb.json")
        self.mappingdb.clear()

        #convert database to dbj in-memory
        for _mapping in self._mappings:
            self.mappingdb.insert(_mapping)

        logging.debug("Mapping database: `%s`" % str(self.mappingdb.getall()))

        if len(self.mappingdb.getall()) < 1:
            logging.critical("Could not cache device mappings")
            # ENOENT (No such file or directory)
            exit(2)

        logging.debug("Successfully imported mapping database")

        result = tiny_devdb.all()
        if not result:
            logging.critical("Config file %s doesn't exist or is damaged" % config_path)
            # ENOENT (No such file or directory)
            exit(2)

        logging.info("Successfully parsed config file")

        logging.debug("Retrieved MIDI port name(s) `%s`" % result)


        # close tinydb
        tiny_database.close()

        # setting up a Websocket client
        logging.debug("Attempting to connect to OBS using websocket protocol")
        self.obs_socket = WebSocketApp("ws://%s:%d" % (ws_server, ws_port))

    def handle_midi_fader(self, deviceID, control, value):
            results = self.mappingdb.getmany(self.mappingdb.find('msg_type == "control_change" and msgNoC == %s and deviceID == %s' % (control, deviceID)))

            if not results:
                logging.debug("Cound not find action for fader %s", control)
                return

            for result in results:
                input_type = result["input_type"]
                action = result["action"]

                if input_type == "button":
                    if value == 127 and not self.send_action(result):
                        continue

                if input_type == "fader":
                    command = result["cmd"]
                    scaled = map_scale(value, 0, 127, result["scale_low"], result["scale_high"])

                    if command == "SetSourceScale":
                        self.obs_socket.send(action.format(scaled))

                    # Super dirty hack but @AlexDash says that it works
                    # @TODO: find an explanation _why_ it works
                    if command == "SetVolume":
                        # Yes, this literally raises a float to a third degree
                        self.obs_socket.send(action % scaled**3)

                    if command == "SetGainFilter":
                        self.obs_socket.send(action % scaled)

                    if command == "SetSourceRotation" or command == "SetTransitionDuration" or command == "SetSyncOffset" or command == "SetSourcePosition":
                        self.obs_socket.send(action % int(scaled))
    def handle_obs_message(self, message):
            self.log.debug("Received new message from OBS")
            payload = json.loads(message)

            self.log.debug("Successfully parsed new message from OBS: %s" % message)

            if "error" in payload:
                self.log.error("OBS returned error: %s" % payload["error"])
                return

            message_id = payload["message-id"]

            self.log.debug("Looking for action with message id `%s`" % message_id)
            for action in self._action_buffer:
                (buffered_id, template, kind) = action

                if buffered_id != int(payload["message-id"]):
                    continue

                del buffered_id
                self.log.info("Action `%s` was requested by OBS" % kind)

                if kind == "ToggleSourceVisibility":
                    # Dear lain, I so miss decent ternary operators...
                    invisible = "false" if payload["visible"] else "true"
                    self.obs_socket.send(template % invisible)
                elif kind == "ReloadBrowserSource":
                    source = payload["sourceSettings"]["url"]
                    target = source[0:-1] if source[-1] == '#' else source + '#'
                    self.obs_socket.send(template % target)
                elif kind == "ToggleSourceFilter":
                    invisible = "false" if payload["enabled"] else "true"
                    self.obs_socket.send(template % invisible)

                self.log.debug("Removing action with message id %s from buffer" % message_id)
                self._action_buffer.remove(action)
                break

            if message_id == "MIDItoOBSscreenshot":
                if payload["status"] == "ok":
                    with open(str(time()) + ".png", "wb") as fh:
                        fh.write(base64.decodebytes(payload["img"][22:].encode()))


    def handle_obs_error(self, ws, error=None):
        # Protection against potential inconsistencies in `inspect.ismethod`
        if error is None and isinstance(ws, BaseException):
            error = ws

        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            self.log.info("Keyboard interrupt received, gracefully exiting...")
            self.close(teardown=True)
        else:
            self.log.error("Websocket error: %" % str(error))

    def handle_obs_close(self, ws):
        self.log.error("OBS has disconnected, timed out or isn't running")
        self.log.error("Please reopen OBS and restart the script")

    def handle_obs_open(self, ws):
        self.log.info("Successfully connected to OBS")

    def send_action(self, action_request):
        action = action_request.get("action")
        if not action:
            # @NOTE: this potentionally should never happen but you never know
            self.log.error("No action supplied in current request")
            return False

        request = action_request.get("request")
        if not request:
            self.log.debug("No request body for action %s, sending action" % action)
            self.obs_socket.send(action)
            # Success, breaking the loop
            return True

        template = TEMPLATES.get(request)
        if not template:
            self.log.error("Missing template for request %s" % request)
            # Keep searching
            return False

        target = action_request.get("target")
        if not target:
            self.log.error("Missing target in %s request for %s action" % (request, action))
            # Keep searching
            return False

        field2 = action_request.get("field2")
        if not field2:
            field2 = False

        self._action_buffer.append([self._action_counter, action, request])
        if field2:
            self.obs_socket.send(template % (self._action_counter, target, field2))
        else:
            self.obs_socket.send(template % (self._action_counter, target))
        self._action_counter += 1

        # Explicit return is necessary here to avoid extra searching
        return True

    def start(self):
        self.log.info("Connecting to OBS...")
        self.obs_socket.run_forever()

    def close(self, teardown=False):
        self.log.debug("Attempting to close midi port(s)")
        result = self.devdb.all()
        for device in result:
            device.close()

        self.log.info("Midi connection has been closed successfully")

        # If close is requested during keyboard interrupt, let the websocket
        # client tear itself down and make a clean exit
        if not teardown:
            self.log.debug("Attempting to close OBS connection")
            self.obs_socket.close()

            self.log.info("OBS connection has been closed successfully")

        self.log.info("Config file has been successfully released")

    def __end__(self):
        self.log.info("Exiting script...")
        self.close()
class handler(QtCore.QObject):
    closed=pyqtSignal()
    SendMessage=pyqtSignal(str,str,name="SendMessage")
    def handle(self,message):
        #logging.debug(str(message))

        #logging.debug(message.type)

        if message.type == "note_on":
            if  entryExists(message.note)!=True:
                self.SendMessage.emit( "note_on", str(message.note))
            else:
                editTable.actRow(getRow(message.note),message)

        elif message.type == "control_change":
            if entryExists(message.control)!=True:
                self.SendMessage.emit( "control_change", str(message.control))
            elif entryExists(message.control):
                editTable.actRow(getRow(message.control),message)



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
    def actRow(self,row,msg):
        logging.info(row)
        logging.info(msg)
        act=form.list_action.cellWidget(row, 4).currentText()
        scene=form.list_action.cellWidget(row, 5).currentText()
        if msg.type =="control_change":
            OBS2.handle_midi_fader( 1, msg.control, msg.value)
            #OBS.setVolume(scene, msg.value)
        logging.info(act)
    def GetSource(self, row):
        text=form.list_action.cellWidget(row, 5).currentText()
        return text

    class UPDATE():
        def __init__(self, form):
            logging.info("make update")

        def UpdateSourceList(self):
            logging.info("updateSourceList")
        def UpdateSceneList(self):
            logging.info("updateSourceList")
        def filter(self, source):
            filter=OBS.getFilterList(source)
            logging.info("updateSourceList")
            return filterList
        def UpdateItemList(self):
            logging.info("updateSourceList")
        def UpdateTransitionList(self):
            logging.info("updateSourceList")
        def UpdateProfileList(self):
            logging.info("updateSourceList")

    class MAKE():
        def __init__(self, form, EditTable):
            logging.info("Create Make Class")
        def Combo(self,list, row, col, *existing):
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            Combo=QtWidgets.QComboBox()
            for item in list:
                Combo.addItem(str(item))


            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            width = Combo.minimumSizeHint().width()
            Combo.view().setMinimumWidth(width)
            form.list_action.setCellWidget(row,col,Combo)
            if existing:
                logging.info(existing[0])
                x=Combo.findText(str(existing[0]), QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
                logging.info(x)
                if x == -1:
                    Combo.setCurrentIndex(0)
                else:
                    Combo.setCurrentIndex(x)
            else:
                Combo.setCurrentIndex(0)
            Combo.currentIndexChanged.connect(EditTable.updateAction)



        def Checkbox(self, row, col=6, *existing):
            logging.info("make checkbox")
            box=QtWidgets.QCheckBox()
            form.list_action.setItem(row,col,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,col,box)
            return box


        def TextInput(self, row, col, *existing):
            box=QtWidgets.QPlainTextEdit()
            return box
    def disableCombo(self, Combo):
        Combo.setEnabled(False)


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
    def SetupOptions(self,action,row, col2, extra="None"):
        #Grab Action List)
        x=actionList[action]
        #Get the Number of blank slots and insert them
        Blanks=x[0]
        self.insertblank(Blanks, row)
        actnum=0
        while actnum < x[0]:
            y=actnum+1
            act=x[y]
            logging.info("actnum: "+str(actnum))
            logging.info(" act: "+act)
            logging.info("Actions: "+Actions[act])
            col=col2+actnum
            eval(Actions[act])
            actnum+=1





    def GainFilter(self, row, col, source):
        text=form.list_action.cellWidget(row, 5).currentText()
    # Inserts blank disabled comboboxes into table when needed
    def insertblank(self, num,row):
        num2=3-num
        combo=QtWidgets.QComboBox()
        combo2=QtWidgets.QComboBox()
        combo3=QtWidgets.QComboBox()
        logging.info("blanknum: " +str(num2))
        if num2 == 1:
            form.list_action.setItem(row,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,7, combo)
            self.disableCombo(combo)
            self.enableCombo(combo2)
            self.enableCombo(combo3)
        elif num2 == 2:
            form.list_action.setItem(row,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,7, combo2)
            form.list_action.setItem(row,6,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,6, combo3)
            self.enableCombo(combo)
            self.disableCombo(combo2)
            self.disableCombo(combo3)
        elif num2 ==3:
            form.list_action.setItem(row,5,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,5, combo)
            form.list_action.setItem(row,6,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,6, combo2)
            form.list_action.setItem(row,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(row,7, combo3)
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
                editTable.Make.Combo(ActionsType[text], row, 4, text)

                if text =="fader":
                    editTable.SetupOptions("SetVolume", row, 5)
                elif text=="button":
                    editTable.SetupOptions("SetCurrentScene", row,5)
            elif col ==4: #action
                logging.info("Changed action")
                action=form.list_action.cellWidget(row, 4).currentText()
                editTable.SetupOptions(action,row,5)

            elif col ==5:
                logging.info("Changed Option 1")
                action=form.list_action.cellWidget(row, 4).currentText()

                editTable.SetupOptions(action,row,5)
            elif col ==6:
                action=form.list_action.cellWidget(row, 4).currentText()
                editTable.SetupOptions(action,row,6)

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
        #insert Message Type Combo
        self.Make.Combo(msgType,self.rowNumber,0,mtype)
        x= QtWidgets.QTableWidgetItem(msgNoC)
        x.setTextAlignment(QtCore.Qt.AlignCenter)
        form.list_action.setItem(self.rowNumber,1,x)

        self.Make.Combo(inpType, self.rowNumber, 2, inputType)
        self.Make.Combo(InList, self.rowNumber, 3, InList[int(deviceID)-1])
        self.Make.Combo(ActionsType[inputType], self.rowNumber, 4, action)
        if option:
            self.SetupOptions(action,self.rowNumber,5,option)



        self.rowNumber=+1

    @Slot(str, str,int)
    def AddNewRow(self, msg_type, msgNoC,deviceID=1):
        rowNumber=0
        form.list_action.insertRow(rowNumber)

        inputType=""
        option=""
        if msg_type=="control_change":
            inputType="fader"
            option="SetVolume"
        elif msg_type == "note_on":
            inputType = "button"
            option="SetCurrentScene"



            #insert Message Type Combo
        self.Make.Combo(msgType,rowNumber,0)
        x= QtWidgets.QTableWidgetItem(msgNoC)
        x.setTextAlignment(QtCore.Qt.AlignCenter)
        form.list_action.setItem(rowNumber,1,x)

        self.Make.Combo(inpType, rowNumber, 2,inputType)
        self.Make.Combo(InList, rowNumber, 3, InList[int(deviceID)-1])
        self.Make.Combo(ActionsType[inputType], rowNumber, 4)
        if option:
            self.SetupOptions(option,rowNumber,5, option)

        self.rowNumber+=1

class qtobsmidi(QMainWindow):
    def currentIndexChanged(self, qmodelindex):
            item = self.InputTypeSelector.currentItem()
            logging.debug(str(item.index()))
    def __init__(self):
        QMainWindow.__init__(self)


class newobs():
    def __init__(self, host = "localhost", port= 4444, password= ""):
        if password !="":
            self.ws = obsws(host, port, password)
        else:
            self.ws = obsws(host, port)
        self.ws.register(self.on_event)
        self.ws.register(self.on_vol, events.SourceVolumeChanged)

        #self.ws.register(self.on_switch, events.SwitchScenes)
        QApplication.processEvents()
        self.get_inputs()
        self.get_outputs()
        logging.debug("Setup OBS")


    def connect(self):
        logging.debug("Connecting to OBS")
        QApplication.processEvents()

        self.ws.connect()

        return True

    def disconnect(self):
        QApplication.processEvents()
        self.ws.disconnect()
    def get_inputs(self):
        count=1
        InList.clear()
        for each in mido.get_input_names():

            InList.append(each)
            count+=1
    def get_outputs(self):
        count=0
        OutList.clear()
        for each in mido.get_output_names():
            OutList.append(each)
            count+=1
    def on_event(self, message):
        QApplication.processEvents()
        logging.info(u"OBSWS: Got message: {}".format(message))
    def on_switch(self, message):
        logging.debug(u"You changed the scene to {}".format(message.getSceneName()))
    def on_vol(self, message):
        logging.debug("Changed volume")
    def getSpecialSources(self):
        tries=["scenes.getDesktop1()","scenes.getMic1()","scenes.getDesktop2()","scenes.getMic2()","scenes.getDesktop3()","scenes.getMic3()","scenes.getDesktop4()","scenes.getMic4()","scenes.getDesktop5()","scenes.getMic5()",]
        sources=specialSourcesList
        scenes = self.ws.call(requests.GetSpecialSources())
        #logging.debug(scenes    )
        for each in tries:
            try:
                x= eval(each)

            except:
                logging.debug("test failed")
            else:
                sources.append(x)
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
    def getFilterList(self, source):
        filterList.clear()
        sources = self.ws.call(requests.GetSourceFilters(source))
        count=0
        for each in sources.getFilters():
            logging.info(each["name"])
            filterList.append(each["name"])
            count+=1
        if count ==0:
            filterList.append("No Filters")

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
    def setVolume(self, source, vol):
        mapvol=map_scale(vol, 0, 127, 0, 1)

        deviceID, control, value
        self.ws.call(requests.SetVolume(source, mapvol))

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
def getRow(value):
    x=form.list_action.findItems(str(value), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
    if x!=[]:
        return x[0].row()

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
    makes={
           "action"    :   QtWidgets.QComboBox()   ,
           "scene"     :   QtWidgets.QComboBox()   ,
           "source"    :   QtWidgets.QComboBox()
           }
    window = Window()
    form = Form()
    form.setupUi(window)
    window.show()
    logging.debug("Program Startup")


    #initialize table

    OBS2=asyncOBS()    # Setup external MidiToOBS Script

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
    #form.btn_SaveTable.clicked.connect(editTable.saveTable)
    #form.btn_Start.clicked.connect(startStopBtnHandle)
    #form.btn_test.clicked.connect(OBS.test)
    form.actionSave.triggered.connect(editTable.saveTable)

    #Setup Connection for adding to table
    #midi.SendMessage.connect(editTable.testing)

    #form.list_action.itemSelectionChanged.connect(editTable.updateAction)
    #form.list_action.itemSelectionChanged.connect(editTable.updateAction)


    #editTable.Make.makeFromList("helo", 2,3)
    tray.show()
    midi.connectToDevice()
    sys.exit(app.exec_())
    #logging.debug(actionQuit)

    #editTable.MakeinputDeviceList()



