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
from functools import partial

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
sceneListShort = []
sceneListLong = []
transitionList = []
specialSourcesList = []
profilesList = []
sceneCollectionList = []
gdisourcesList = []
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
def ScriptExit(signal, frame):
    logging.info("Closing midi ports...")
    for port in midiports:
        port["object"].close()
    logging.info("Closing database...")
    database.close()
    logging.info("Exiting...")
    sys.exit(0)







def saveTODOButtonToFile(msg_type, msgNoC, input_type, action, request, target, field2, deviceID):
    logging.info("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "request": request, "target": target, "deviceID": deviceID, "field2": field2})

def printArraySelect(array):
    counter = 0
    for line in array:
        logging.info("%s: %s" % (counter, line))
        counter += 1
    if counter > 1:
        return array[int(input("Select 0-%s: " % str(len(array)-1)))]
    else:
        return array[int(input("Select 0: "))]

def askForInputScaling():
    logging.info("Setup input scale")
    low = int(input("Select lower output value: "))
    high = int(input("Select higher output value: "))
    return low, high

def updateTransitionList():
    form.box_transitions.clear()
    counter = 0
    global transitionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("\nUpdating transition list, plase wait")
    ws.send("""{"request-type": "GetTransitionList", "message-id": "999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    transitionList = []
    if jsn["message-id"] == "999999":
        for item in jsn["transitions"]:
            transitionList.append(item["name"])
            form.box_transitions.insertItem(counter, str(item["name"]))
            counter += 1

        #logging.info("Transitions updated")
    else:
        logging.info("Failed to update Transition List")
    ws.close()





def updateProfileList():
    form.box_profiles.clear()
    counter = 0
    global profilesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("Updating Profiles List, plase wait")
    ws.send("""{"request-type": "ListProfiles", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    profilesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["profiles"]:
            profilesList.append(line["profile-name"])
            form.box_profiles.insertItem(counter, str(line["profile-name"]))
            counter += 1
        #logging.info("Profiles List updated")
    else:
        logging.info("Failed to update")

    ws.close()

def updatesceneCollectionList():
    form.box_collections.clear()
    counter = 0
    global sceneCollectionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("\nUpdating Scene Collection List, plase wait")
    ws.send("""{"request-type": "ListSceneCollections", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneCollectionList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["scene-collections"]:
            sceneCollectionList.append(line["sc-name"])
            form.box_collections.insertItem(counter, str(line["sc-name"]))
            counter += 1

        #logging.info("Scene Collection List updated")
    else:
        logging.info("Failed to update")
    ws.close()






def getSourceFilters(sourcename):
    form.box_filtersFaders.clear()
    counter = 0
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-getSourceFilters", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-getSourceFilters":
        form.box_filtersFaders.insertItem(counter, str(jsn["filters"]))
        #logging.info(str(jsn["filters"]))

        counter += 1
        return jsn["filters"]
    else:
        return False




def configureDevices(switch):
    dbresult = devdb.all()
    if switch:
        logging.info("\nTell me: What do you want to do?\n1: Rename a device and transfer their action assignments (because you plugged it into another USB port and windows decided to give the device a new name now)\n2: Delete all devices from config and re-add (Warning: this will dereference all button and fader actions(so they will no longer work). This might cause device confusion later.\n3: Remove a single device from the configuration INCLUDING their midi assignments\n4: Add new device\n5: Skip device configuration (Warning: If no device has been configured before, MIDItoOBS will NOT work)")
        action_select = int(input("Select 1-4: "))
        if action_select == 1:
            renameDevice()
            return
        elif action_select == 2:
            logging.info("Removing all devices from the database....")
            devdb.purge() #purge database table before adding new devices
        elif action_select == 3:
            removeDevice()
            return
        elif action_select == 4:
            pass
        else:
            return

    logging.info("\nWhich device do you want to add?")
    exitflag = 0
    while not exitflag:
        availableDeviceList = mido.get_input_names()
        deviceList = []
        counter = 0
        inUseDeviceList = devdb.all()
        for device in availableDeviceList:
            if devInDB(device, inUseDeviceList):
                pass
            else:
                logging.info("%s: %s" % (counter, device))
                counter += 1
                deviceList.append(device)

        if len(deviceList) == 0:
            logging.info("No midi input device available")
            return
        if len(deviceList) < 2:
            input_select = int(input("Select 0: "))
        else:
            input_select = int(input("Select 0-%s: " % str(len(deviceList)-1)))
        logging.info("Adding:", deviceList[input_select])
        result = devdb.search(Query().devicename == deviceList[input_select])
        if not result:
            deviceID = devdb.insert({"devicename": deviceList[input_select]})
        logging.info("Do you want to add another device?\n1: Yes\n2: No")
        action_select = int(input("Select 1 or 2: "))
        if action_select == 2:
            exitflag = 1

def devInDB(devicename, devicedatabase):
    for entry in devicedatabase:
        if entry["devicename"] == devicename:
            return True
    return False

def removeDevice():
    devices = devdb.all()
    logging.info("So you want to remove a device. Please keep in mind that this will not only remove the device but remove every action assigned to the device.\nWhich device and configuration do you want to remove?")
    counter = 0
    for (index, device) in enumerate(devices):
        logging.info("%s: %s" % (counter, device["devicename"]))
        counter += 1
    device_select = int(input("Select 0-%s: " % str(len(devices)-1)))
    logging.info("Selected:", devices[device_select]["devicename"])
    yousure = input("Are you really sure you want to remove the devices and all it's assignments?\nType 'YES' and press enter: ")
    if yousure == "YES":
        logging.info("As you wish. Deleting now......")
        try:
            result = devdb.get(Query().devicename == devices[device_select]["devicename"])
            devdb.remove(doc_ids=[result.doc_id])
            db.remove(Query().deviceID == result.doc_id)
        except:
            logging.info("There was an error removing the device")


def renameDevice():
    devices = devdb.all()
    counter = 0
    logging.info("Please select a device for your configuration that you want to \"rename\" to another device:")
    for (index, device) in enumerate(devices):
        logging.info("%s: %s" % (counter, device["devicename"]))
        counter += 1
    old_device_select = int(input("Select 0-%s: " % str(len(devices)-1)))
    old_device_name = devices[old_device_select]["devicename"]
    logging.info("Selected:", old_device_name)
    logging.info("Please select the new device name now:")
    availableDeviceList = mido.get_input_names()
    deviceList = []
    for device in availableDeviceList:
            if devInDB(device, devices):
                pass
            else:
                deviceList.append(device)
    if len(deviceList) > 0:
        counter = 0
        for (index, device) in enumerate(deviceList):
            logging.info("%s: %s" % (counter, device))
            counter += 1
        new_device_select = int(input("Select 0-%s: " % str(len(deviceList)-1)))
        new_device_name = deviceList[new_device_select]
        logging.info("Selected:", new_device_name, "as the new device name")
        logging.info("Updating \"", old_device_name, "\" to \"", new_device_name, "\" now", sep="")
        try:
            devdb.update({"devicename": new_device_name}, Query().devicename == old_device_name)
            logging.info("Sucessfully renamed the device")
        except:
            logging.info("There was an error renaming the device")
    else:
        logging.info("There is no other device available to switch over to. Aborting...")

def getDevices():
    availableinDeviceList = mido.get_input_names()
    deviceList = []
    inUseDeviceList = devdb.all()
    for device in availableinDeviceList:
        logging.info(device)
        if devInDB(device, inUseDeviceList):
            pass
        deviceList.append(device)







def entryExists(value):
    x=form.list_action.findItems(str(value), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
    if x!=[]:
        return True
    else:
        return False

    #used for connecting Midi to obs for actually controlling OBS


class handler(QtCore.QObject):
    closed=pyqtSignal()
    SendMessage=pyqtSignal(str,str,name="SendMessage")
    def handle(self,message):
        #logging.info(str(message))

        #logging.info(message.type)

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
                #logging.info("device name "+device["devicename"])
                tempmidiport = mido.open_input(device["devicename"],callback=midi.handle)
                tempobj = {"id": device.doc_id, "object": tempmidiport, "devicename": device["devicename"]}
                midiports.append(tempobj)
                #logging.info("successfully opened" + str(device["devicename"]))
            except:
                logging.info("\nCould not open", str(device["devicename"]))
                #QtWidgets.QMessageBox.Critical(self, "Could not open", "The midi device might be used by another application/not plugged in/have a different name.")
                database.close()
                #sys.exit(5)


class EditTable():
    rowNumber=0
    #define row dropdowns
    def __init__(self, form):
        result = db.all()
        self.rowNumber=rowNumber
        for rowNumbers, RowData in enumerate (result):
            res = ast.literal_eval(RowData["action"])
            #logging.info(res["request-type"])
            #m_pTableWidget->setItem(0, 1, new QTableWidgetItem("Hello"));
            #editTable.add(EditTable, rowNumber,RowData, colum_number, data);
            option=[]

            if str(res["request-type"]) == "SetCurrentScene" or str(res["request-type"]) == "SetPreviewScene" or str(res["request-type"]) == "SetSourcePosition" or str(res["request-type"]) == "SetSourceRotation" or str(res["request-type"]) == "SetSourcescale":
                option.append(res["scene-name"])
            elif str(res["request-type"]) == "SetVolume" or str(res["request-type"]) == "ToggleMute" or str(res["request-type"]) == "SetMute"or str(res["request-type"]) == "SetSyncOffset" or str(res["request-type"]) == "SetTextGDIPlusText" or str(res["request-type"]) == "SetBrowserSourceURL" or str(res["request-type"]) == "ReloadBrowserSource":
                option.append(res["source"])
            elif  str(res["request-type"]) == "TakeSourceScreenshot" or str(res["request-type"]) =="SetGainFilter" or str(res["request-type"]) =="EnableSourceFilter" or str(res["request-type"]) =="DisableSourceFilter" or str(res["request-type"]) =="ToggleSourceFilter":
                option.append(res["sourceName"])
            else:
                #option.append(res["transition-name"])
                #option.append(res["duration"])
                #option.append(res["filterName"])
                #option.append(res["offset"])
                #option.append(res["scale"])
                #option.append(res["item"])
                #option.append(res["url"])
                #option.append(res["visible"])
                #option.append(res["position"])
                #option.append(res["rotation"])
                #option.append(res["sc-name"])
                option.append("error")

            self.addRow(str(RowData["msg_type"]),str(RowData["msgNoC"]),str(RowData["input_type"]),str(res["request-type"]),str(RowData["deviceID"]),*tuple(option))

        self.variable="foo"
        self.table()
    def disableCombo(self, Combo):
        Combo.setEnabled(False)
        return Combo

    def enableCombo(self,Combo):
        Combo.setEnabled(True)
    def newFaderSetup(self,action, NoC, msgType, deviceID, source, scale, *options):
        #source, scale deviceID
        deviceID=deviceID+1
        if action == "SetVolume":
             # pull from dropdown
            scale = (0,2)
            action = jsonArchive["SetVolume"] % (source, "%s")
            self.saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetVolume", deviceID)
        elif action == "SetSyncOffset":
            source = "" #Pull from dropdown printArraySelect(tempSceneList)
            scale = options[1] #askForInputScaling()
            action = jsonArchive["SetSyncOffset"] % (source, "%s")
            self.saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSyncOffset", deviceID)
        elif action == "SetGainFilter":
            source = "" #Pull From Dropdown printArraySelect(tempSceneList)
            filtername = self.checkIfSourceHasGainFilter(source)
            if filtername:
                scale = (-30,30) #askForInputScaling()
                action = jsonArchive["SetGainFilter"] % (source, filtername, "%s")
                self.saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetGainFilter", deviceID)
            else:
                logging.info("The selected source has no gain filter. Please add it in the source filter dialog and try again.")
                #Setup Alertbox

    def setupButtonEvents(self, action, NoC, msgType, deviceID):
        deviceID=deviceID+1
        print()
        print("You selected: %s" % action)
        if action == "SetCurrentScene":
            updateSceneList()
            scene = printArraySelect(sceneListShort)
            action = jsonArchive["SetCurrentScene"] % scene
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetPreviewScene":
            updateSceneList()
            scene = printArraySelect(sceneListShort)
            action = jsonArchive["SetPreviewScene"] % scene
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "TransitionToProgram":
            updateTransitionList()
            print("Please select a transition to be used:")
            transitionList.append("--Current--")
            transition = printArraySelect(transitionList)
            print(transition)
            if transition != "--Current--":
                tmp = ' , "with-transition": {"name": "' + transition + '"}'
                action = jsonArchive["TransitionToProgram"] % tmp
            else:
                action = jsonArchive["TransitionToProgram"] % ""
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetCurrentTransition":
            updateTransitionList()
            transition = printArraySelect(transitionList)
            action = jsonArchive["SetCurrentTransition"] % transition
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartStopStreaming":
            action = jsonArchive["StartStopStreaming"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartStreaming":
            action = jsonArchive["StartStreaming"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StopStreaming":
            action = jsonArchive["StopStreaming"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartStopRecording":
            action = jsonArchive["StartStopRecording"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartRecording":
            action = jsonArchive["StartRecording"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StopRecording":
            action = jsonArchive["StopRecording"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartStopReplayBuffer":
            action = jsonArchive["StartStopReplayBuffer"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StartReplayBuffer":
            action = jsonArchive["StartReplayBuffer"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "StopReplayBuffer":
            action = jsonArchive["StopReplayBuffer"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SaveReplayBuffer":
            action = jsonArchive["SaveReplayBuffer"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "PauseRecording":
            action = jsonArchive["PauseRecording"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "ResumeRecording":
            action = jsonArchive["ResumeRecording"]
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetSourceVisibility":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            source = printArraySelect(tempSceneList)
            renderArray = ["0 (Invisible)", "1 (Visible)"]
            render = printArraySelect(renderArray)
            if render == "0 (Invisible)":
                render = "false"
            else:
                render = "true"
            sceneListShort.append("--Current--")
            scene = printArraySelect(sceneListShort)
            if scene != "--Current--":
                source = source + '", "scene-name": "' + scene
            action = jsonArchive["SetSourceVisibility"] % (source, str(render))
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "ToggleSourceVisibility":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            source = source1 = printArraySelect(tempSceneList)
            sceneListShort.append("--Current--")
            scene = printArraySelect(sceneListShort)
            if scene != "--Current--":
                source = source + '", "scene": "' + scene
            action = jsonArchive["ToggleSourceVisibility"] % (source, "%s")
            saveTODOButtonToFile(msgType, NoC, "button" , action, "ToggleSourceVisibility", source1, "" , deviceID)
        elif action == "ToggleMute":
            updateSceneList()
            updateSpecialSources()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for item in specialSourcesList:
                tempSceneList.append(item)
            source = printArraySelect(tempSceneList)
            action = jsonArchive["ToggleMute"] % source
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetMute":
            updateSceneList()
            updateSpecialSources()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for item in specialSourcesList:
                tempSceneList.append(item)
            source = printArraySelect(tempSceneList)
            tempArray = ["0 (Muted)", "1 (Unmuted)"]
            muted = printArraySelect(tempArray)
            if muted == "0 (Muted)":
                muted = "true"
            else:
                muted = "false"
            action = jsonArchive["SetMute"] % (source, muted)
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetTransitionDuration":
            time = int(input("Input the desired time(in milliseconds): "))
            action = jsonArchive["SetTransitionDuration"] % time
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetCurrentProfile":
            updateProfileList()
            profilename = printArraySelect(profilesList)
            action = jsonArchive["SetCurrentProfile"] % profilename
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetRecordingFolder":
            recpath = str(input("Input the desired path: "))
            action = jsonArchive["SetRecordingFolder"] % recpath
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetCurrentSceneCollection":
            updatesceneCollectionList()
            scenecollection = printArraySelect(sceneCollectionList)
            action = jsonArchive["SetCurrentSceneCollection"] % scenecollection
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "ResetSceneItem":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            source = printArraySelect(tempSceneList)
            sceneListShort.append("--Current--")
            scene = printArraySelect(sceneListShort)
            if scene != "--Current--":
                render = '"' + str(source) + '", "scene-name": "' + scene + '"'
            else:
                render = '"' + str(source) + '"'
            action = jsonArchive["ResetSceneItem"] % (render)
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetTextGDIPlusText":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList and line["type"] == "text_gdiplus":
                        tempSceneList.append(line["name"])
            source = printArraySelect(tempSceneList)
            text = str(input("Input the desired text: "))
            action = jsonArchive["SetTextGDIPlusText"] % (source, text)
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "SetBrowserSourceURL":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList and line["type"] == "browser_source":
                        tempSceneList.append(line["name"])
            source = printArraySelect(tempSceneList)
            url = str(input("Input the desired URL: "))
            action = jsonArchive["SetBrowserSourceURL"] % (source, url)
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "ReloadBrowserSource":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList and line["type"] == "browser_source":
                        tempSceneList.append(line["name"])
            source = printArraySelect(tempSceneList)
            action = jsonArchive["ReloadBrowserSource"] % (source, "%s")
            saveTODOButtonToFile(msgType, NoC, "button" , action, "ReloadBrowserSource", source, "", deviceID)
        elif action == "TakeSourceScreenshot":
            updateSceneList()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for scene in sceneListShort:
                tempSceneList.append(scene)
            source = printArraySelect(tempSceneList)
            action = jsonArchive["TakeSourceScreenshot"] % (source)
            self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
        elif action == "EnableSourceFilter":
            updateSceneList()
            updateSpecialSources()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for item in specialSourcesList:
                tempSceneList.append(item)
            source = printArraySelect(tempSceneList)
            filters = getSourceFilters(source)
            if filters:
                tempFilterList = []
                for line in filters:
                    tempFilterList.append(line["name"])
                selectedFilter = printArraySelect(tempFilterList)
                action = jsonArchive["EnableSourceFilter"] % (source, selectedFilter)
                self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
            else:
                print("\nThis source has no filters")
        elif action == "DisableSourceFilter":
            updateSceneList()
            updateSpecialSources()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for item in specialSourcesList:
                tempSceneList.append(item)
            source = printArraySelect(tempSceneList)
            filters = getSourceFilters(source)
            if filters:
                tempFilterList = []
                for line in filters:
                    tempFilterList.append(line["name"])
                selectedFilter = printArraySelect(tempFilterList)
                action = jsonArchive["DisableSourceFilter"] % (source, selectedFilter)
                self.saveButtonToFile(msgType, NoC, "button" , action, deviceID)
            else:
                print("\nThis source has no filters")
        elif action == "ToggleSourceFilter":
            updateSceneList()
            updateSpecialSources()
            tempSceneList = []
            for scene in sceneListLong:
                for line in scene["sources"]:
                    if line["name"] not in tempSceneList:
                        tempSceneList.append(line["name"])
            for item in specialSourcesList:
                tempSceneList.append(item)
            source = printArraySelect(tempSceneList)
            filters = getSourceFilters(source)
            if filters:
                tempFilterList = []
                for line in filters:
                    tempFilterList.append(line["name"])
                selectedFilter = printArraySelect(tempFilterList)
            action = jsonArchive["ToggleSourceFilter"] % (source, selectedFilter, "%s")
            saveTODOButtonToFile(msgType, NoC, "button" , action, "ToggleSourceFilter", source, selectedFilter, deviceID)

    def add_msg_type_drop(self, msg):
        drop_msg_type=QtWidgets.QComboBox()
        drop_msg_type.insertItems(0, ["control_change", "program_change", "note_on"])

        x=drop_msg_type.findText(msg, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        drop_msg_type.setCurrentIndex(x)
        return drop_msg_type
    def saveTable(self, *options):
        logging.info(options)
        #This function iterates through table, and switches between Sending SaveFaderToFile and saveButtonToFile based on inputType
        logging.info("Save Table")
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
                logging.info("no values")

            logging.info(str(irow)+ ": "+str(msg_type))
            logging.info(arg)

            #logging.info(str(irow)+ ": "+str(msgNoC))
            #logging.info(str(irow)+ ": "+str(input_type))
            #logging.info(str(irow)+ ": "+str(action))
            #logging.info(str(irow)+ ": "+str(scale))
            #logging.info(str(irow)+ ": "+str(cmd))
            #logging.info(str(irow)+ ": "+str(deviceID))
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
        logging.info("Saved %s with control %s for action %s on device %s" % (msg_type, msgNoC, cmd, deviceID))
        Search = Query()
        result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        if result:
            db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": int(scale[0]), "scale_high": int(scale[1]), "action": action, "cmd": cmd, "deviceID": deviceID})
        else:
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": int(scale[0]), "scale_high": int(scale[1]), "action": action, "cmd": cmd, "deviceID": deviceID})

    def saveButtonToFile(self, msg_type, msgNoC, input_type, action, deviceID):
        # note_on, 20, button, action, deviceID
        logging.info("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
        Search = Query()
        result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        if result:
            db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})
        else:
            db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})

    def add_input_type_drop(self, msg):
        x=0

        drop_msg_type=QtWidgets.QComboBox()

        drop_msg_type.insertItems(0, ["button", "fader"])

        x=drop_msg_type.findText(msg, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        drop_msg_type.setCurrentIndex(x)



        return drop_msg_type


    def table(self):
        self.tableWidget = form.list_action



    def MakeActionSelector(self, type, *action):
        #logging.info("Setting up actions")
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

        drop_msg_type.currentIndexChanged.connect(self.updateAction)

        return drop_msg_type

    def MakeSceneSelector(self,*existing):
        sceneCombo=QtWidgets.QComboBox()
        for scene in sceneListShort:
            #logging.info(line)
            sceneCombo.addItem(scene)
            #logging.info(scene)
        if existing:
            #logging.info(existing[0])
            x=sceneCombo.findText(existing[0], QtCore.Qt.MatchStartsWith | QtCore.Qt.MatchRecursive)
            sceneCombo.setCurrentIndex(x)
        return sceneCombo


    def MakeInputDeviceList(self,*existing):
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
    def GetCurrentScene(self):
        ws = create_connection("ws://" + serverIP + ":" + serverPort)
        ws.send('{"request-type": "GetCurrentScene","message-id": "MIDItoOBS-checksourcegainfilter"}')
        result =  ws.recv()
        ws.close()
        jsn = json.loads(result)
        return str(jsn["name"])

    def MakeVolumeSelector(self,*existing):
        volumeCombo=QtWidgets.QComboBox()

        for item in specialSourcesList:
            #logging.info(each)
            volumeCombo.addItem(str(item))
            #add code here for generating a dropdown
            volumeCombo.currentIndexChanged.connect(self.updateAction)
            volumeCombo.setCurrentIndex(1)

        if existing:
            x=volumeCombo.findText(existing[0], QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
            volumeCombo.setCurrentIndex(x)

        else:
            volumeCombo.setCurrentIndex(0)
        return volumeCombo
    @Slot(int)
    def updateAction(self):
        x=form.list_action.selectedItems()
        row=0
        text=""
        for each in x:

            row=each.row()
            col=each.column()
            text=form.list_action.cellWidget(row, col).currentText()
            logging.info(row)
            if col==2:
                form.list_action.setItem(row,4,QtWidgets.QTableWidgetItem())
                form.list_action.setCellWidget(row,4, self.MakeActionSelector(text))
            elif col ==4:
                action=form.list_action.cellWidget(row, 4).currentText()
                form.list_action.setItem(row,5,QtWidgets.QTableWidgetItem())
                form.list_action.setCurrentCell(row, 5)
                form.list_action.setCellWidget(row,5, self.setupoption1(action))




    def MakeProfileSelector(self):
        logging.info("Setting up profiles")

    def MakeTransitionsSelector(self):
        logging.info("Setting up transitions")

    def setupoption1(self,action,*extra):
        #logging.info("Setting up Option 1")
        logging.info(action)
        if action == "SetVolume":
            return self.MakeVolumeSelector(*extra)
            #logging.info("faderType")
        elif action == "SetSyncOffset":
            logging.info("faderType")
        elif action == "SetSourcePosition":
            logging.info("faderType")
        elif action == "SetSourceRotation":
            logging.info("faderType")
        elif action == "SetSourceScale":
            logging.info("faderType")
        elif action == "SetTransitionDuration":
            logging.info("faderType")
        elif action == "SetGainFilter":
            logging.info("faderType")
        #buttonActions
        elif action == "SetCurrentScene":
            return self.MakeSceneSelector(*extra)
        elif action == "SetPreviewScene":
            logging.info("set preview scene "+ extra[0])
            return self.MakeSceneSelector(*extra)
        elif action == "TransitionToProgram":
           logging.info("faderType")
        elif action == "SetCurrentTransition":
           logging.info("faderType")
        elif action == "SetSourceVisibility":
           logging.info("faderType")
        elif action == "ToggleSourceVisibility":
           logging.info("faderType")
        elif action == "ToggleMute":
           logging.info("faderType")
        elif action == "SetMute":
           logging.info("faderType")
        elif action == "SetTransitionDuration":
           logging.info("faderType")
        elif action == "SetCurrentProfile":
           logging.info("faderType")
        elif action == "SetCurrentSceneCollection":
           logging.info("faderType")
        elif action == "ResetSceneItem":
           logging.info("faderType")
        elif action == "SetTextGDIPlusText":
           logging.info("faderType")
        elif action == "SetBrowserSourceURL":
           logging.info("faderType")
        elif action == "ReloadBrowserSource":
           logging.info("faderType")
        elif action == "TakeSourceScreenshot":
           logging.info("faderType")
        elif action == "EnableSourceFilter":
           logging.info("faderType")
        elif action == "DisableSourceFilter":
           logging.info("faderType")
        elif action == "ToggleSourceFilter":
           logging.info("faderType")






    def setupOption2(self,action,*extra):
        logging.info("Option 2")
    def setupOption3(self,action,*extra):
        logging.info("Option 3")
    def insertblank(self, num):
        combo=QtWidgets.QComboBox()
        combo2=QtWidgets.QComboBox()
        combo3=QtWidgets.QComboBox()
        if num == 1:
            form.list_action.setItem(self.rowNumber,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,7, combo)
            self.disableCombo(combo)
        elif num == 2:
            form.list_action.setItem(self.rowNumber,7,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,7, combo2)
            form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,6, combo3)
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

    def addRow(self, mtype, msgNoC, inputType, action, deviceID, *option):
        rowNumber=self.rowNumber
        form.list_action.insertRow(self.rowNumber)

        form.list_action.setItem(self.rowNumber,0,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,0, self.add_msg_type_drop(mtype))


        x= QtWidgets.QTableWidgetItem(msgNoC)
        x.setTextAlignment(QtCore.Qt.AlignCenter)

        form.list_action.setItem(self.rowNumber,1,x)

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        combo=self.add_input_type_drop(inputType)
        combo.currentIndexChanged.connect(self.updateAction)
        form.list_action.setCellWidget(self.rowNumber,2, combo)


        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.MakeActionSelector(inputType, action))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.MakeInputDeviceList(deviceID))





        if option:

            form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())

            form.list_action.setCellWidget(self.rowNumber,5, self.setupoption1(action, option[0]))
            if len(option) >1:
                a=QtWidgets.QTableWidgetItem(option[1])
                a.setTextAlignment(QtCore.Qt.AlignCenter)

                form.list_action.setItem(self.rowNumber,6,a)
            self.insertblank(2)
        else:
            self.insertblank(3)

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
        form.list_action.setCellWidget(self.rowNumber,0, editTable.add_msg_type_drop(msg_type))

        form.list_action.setItem(self.rowNumber,1,QtWidgets.QTableWidgetItem(msgNoC))

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,2, editTable.add_input_type_drop(inputType, self.rowNumber))

        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.MakeActionSelector(inputType))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.MakeInputDeviceList(deviceID))

        form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,5, self.setupoption1(inputType, option[0]))

        form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem(str(rowNumber)))

        self.rowNumber+=1

    @Slot(str,str)
    def testing(self,type, msg):
        #logging.info(type)
        form.testlabel2.setText(msg)
        #form.testlabel.setText(type)
    # Add one full row at a time,
    # Add actions in class to handle when things change in drop down
    #Pre populate drop down.
    # or set it up so that an edit area is populated on a click
    # Lets go with # 2 for now

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

def ChangedScenes(scene):
    checkIfSourceHasGainFilter(scene)
    getSourceFilters(scene)
    logging.info(scene)
    updateSpecialSources()
    updateTransitionList()
    updateProfileList()
    updatesceneCollectionList()
def myExitHandler():
    logging.info("kill application")

    app.quit
    #sys.exit(app.exec_())

def startup():
    getDevices()
    #


class qtobsmidi(QMainWindow):
    def currentIndexChanged(self, qmodelindex):
            item = self.InputTypeSelector.currentItem()
            logging.info(str(item.index()))
    def __init__(self):
        QMainWindow.__init__(self)


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
    #Disconnect from setup connection to obs and Midi
    #Call OBSMIDI script
    #OBS.start()
    tray.showMessage("Connecting","Connecting to OBS",icon)
    OBS.connect()
    #logging.info("Connecting to OBS")
def stopOBSconnection():
    icon.Off
    #OBS.stop()
    OBS.disconnect()
    tray.showMessage("Disconnecting","disconnecting from OBS",icon)
def map_scale(inp, ista, isto, osta, osto):
    return osta + (osto - osta) * ((inp - ista) / (isto - ista))
def get_logger(name, level=logging.INFO):
   log_format = logging.Formatter('[%(asctime)s] (%(levelname)s) T%(thread)d : %(message)s')

   std_output = logging.StreamHandler(stdout)
   std_output.setFormatter(log_format)
   std_output.setLevel(level)

   file_output = logging.FileHandler(path.join(SCRIPT_DIR, "debug.log"))
   file_output.setFormatter(log_format)
   file_output.setLevel(level)

   logger = logging.getLogger(name)
   logger.setLevel(logging.DEBUG)
   logger.addHandler(file_output)
   logger.addHandler(std_output)
   return logger


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
        logging.info(u"Got message: {}".format(message))


    def on_switch(self, message):
        logging.info(u"You changed the scene to {}".format(message.getSceneName()))
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
        logging.info("test")
        self.getSpecialSources()
    def getscenelist(self):
        try:
            scenes = self.ws.call(requests.GetSceneList())
            #logging.info(scenes)
            for each in scenes.getScenes():
                #logging.info(each['name'])
                sceneListLong.append(each)
                sceneListShort.append(each["name"])

        except:
            logging.info("unable to get scenes")


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    signal.signal(signal.SIGINT, ScriptExit)
    Form, Window = uic.loadUiType("qtOBSMIDI.ui")

    app = QApplication(sys.argv)
    window = Window()
    form = Form()
    form.setupUi(window)
    window.show()
    logging.info("Program Startup")

    startuped=True
    if startuped==True:
        startup()
        startuped=False
    #initialize table

    # Setup external MidiToOBS Script

    OBS=newobs()
    OBS.connect()
    OBS.getscenelist()
    OBS.getSpecialSources()
    midi=handler()
    editTable=EditTable(form)

    #logging.info(midiports)
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
    midi.SendMessage.connect(editTable.testing)

    form.list_action.itemSelectionChanged.connect(editTable.updateAction)
    form.list_action.itemSelectionChanged.connect(editTable.updateAction)



    tray.show()
    midi.connectToDevice()
    sys.exit(app.exec_())
    #logging.info(actionQuit)

    #editTable.MakeinputDeviceList()



