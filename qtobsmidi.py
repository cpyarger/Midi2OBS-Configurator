# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Signal, Slot, QObject


import logging
import time

from PySide2.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtWidgets,QtCore
from PyQt5.QtGui import QIcon

from PyQt5.QtCore import   pyqtSlot, pyqtSignal
import mido, sys, json,  signal
import mido.ports as Multi
from tinydb import TinyDB, Query
from websocket import create_connection

record=False
####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
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
               "SetVolume": """{"request-type": "SetVolume", "message-id" : "1", "source": "%s", "volume": %s}""",
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
savetime1 = time.time()

def ScriptExit(signal, frame):
    logging.info("Closing midi ports...")
    for port in midiports:
        port["object"].close()
    logging.info("Closing database...")
    database.close()
    logging.info("Exiting...")
    sys.exit(0)





def saveFaderToFile(msg_type, msgNoC, input_type, action, scale, cmd, deviceID):
    logging.info("Saved %s with control %s for action %s on device %s" % (msg_type, msgNoC, cmd, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "scale_low": scale[0], "scale_high": scale[1], "action": action, "cmd": cmd, "deviceID": deviceID})

def saveButtonToFile(msg_type, msgNoC, input_type, action, deviceID):
    # note_on, 20, button, action, deviceID
    logging.info("Saved %s with note/control %s for action %s on device %s" % (msg_type, msgNoC, action, deviceID))
    Search = Query()
    result = db.search((Search.msg_type == msg_type) & (Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
    if result:
        db.remove((Search.msgNoC == msgNoC) & (Search.deviceID == deviceID))
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})
    else:
        db.insert({"msg_type": msg_type, "msgNoC": msgNoC, "input_type": input_type, "action" : action, "deviceID": deviceID})

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

def updateSceneList():
    counter = 0
    global sceneListShort
    global sceneListLong
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("\nUpdating scene list, plase wait")
    ws.send("""{"request-type": "GetSceneList", "message-id": "9999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneListShort = []
    sceneListLong = []
    if jsn["message-id"] == "9999999":
        sceneListLong = jsn["scenes"]
        for item in jsn["scenes"]:
            sceneListShort.append(item["name"])
            counter += 1

        #logging.info("Scenes updated")
    else:
        logging.info("Failed to update scenes")

    ws.close()

def updateSpecialSources():
    global specialSourcesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    #logging.info("\nUpdating special sources, plase wait")
    ws.send("""{"request-type": "GetSpecialSources", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    specialSourcesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn:
            if line == "status" or line == "message-id":
                pass
            else:
                specialSourcesList.append(jsn[line])
        #logging.info("Special sources updated")
    else:
        logging.info("Failed to update")
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

def connectToDevice():
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

def entryExists(value):
    x=form.list_action.findItems(str(value), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
    if x!=[]:
        return True
    else:
        return False
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
    def enableCombo(self,Combo):
        Combo.setEnabled(True)
    def add_msg_type_drop(self, msg):
        #logging.info("type " +str(msg))

        drop_msg_type=QtWidgets.QComboBox()
        drop_msg_type.insertItems(0, ["control_change", "program_change", "note_on"])

        x=drop_msg_type.findText(msg, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        drop_msg_type.setCurrentIndex(x)
        return drop_msg_type

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


        return drop_msg_type

    def MakeSceneSelector(self,*existing):
        sceneCombo=QtWidgets.QComboBox()
        updateSceneList()
        updateSpecialSources()
        for scene in sceneListLong:
            for line in scene["sources"]:
                #logging.info(line)
                sceneCombo.addItem(str(line["name"]))
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

        updateSceneList()
        updateSpecialSources()
        tempSceneList = []
        for scene in sceneListLong:
            for line in scene["sources"]:
                if line["name"] not in tempSceneList:
                    tempSceneList.append(line["name"])
        for item in specialSourcesList:
            tempSceneList.append(item)
        source = tempSceneList
        for each in source:
            #logging.info(each)
            volumeCombo.addItem(str(each))
            #add code here for generating a dropdown
        if existing:
            x=volumeCombo.findText(existing[0], QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            volumeCombo.setCurrentIndex(x)
        return volumeCombo


    def MakeProfileSelector(self):
        logging.info("Setting up profiles")

    def MakeTransitionsSelector(self):
        logging.info("Setting up transitions")

    def setupoption1(self,action,*extra):

        #logging.info("Setting up Option 1")
            faderActions
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

    def addRow(self, mtype, msgNoC, inputType, action, deviceID, *option):
        form.list_action.insertRow(self.rowNumber)

        form.list_action.setItem(self.rowNumber,0,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,0, self.add_msg_type_drop(mtype))

        x= QtWidgets.QTableWidgetItem(msgNoC)
        x.setTextAlignment(QtCore.Qt.AlignCenter)
        form.list_action.setItem(self.rowNumber,1,x)

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,2, self.add_input_type_drop(inputType))

        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.MakeActionSelector(inputType, action))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.MakeInputDeviceList(deviceID))



        a=QtWidgets.QTableWidgetItem(option[0])
        a.setTextAlignment(QtCore.Qt.AlignCenter)
        form.list_action.setItem(self.rowNumber,6,a)

        if option:
            form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())
            form.list_action.setCellWidget(self.rowNumber,5, self.setupoption1(action, option[0]))
        self.rowNumber=+1

    @Slot(str, str,int)
    def AddNewRow(self, msg_type, msgNoC,deviceID=1):
        form.list_action.insertRow(self.rowNumber)

        inputType=""
        option[0]=""
        if msg_type=="control_change":
            inputType="fader"
            option[0]="SetVolume"
        elif msg_type == "note_on":
            inputType = "button"
            option[0]="SetCurrentScene"
        form.list_action.setItem(self.rowNumber,0,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,0, editTable.add_msg_type_drop(msg_type))

        form.list_action.setItem(self.rowNumber,1,QtWidgets.QTableWidgetItem(msgNoC))

        form.list_action.setItem(self.rowNumber,2,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,2, editTable.add_input_type_drop(inputType))

        form.list_action.setItem(self.rowNumber,4,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,4, self.MakeActionSelector(inputType))

        form.list_action.setItem(self.rowNumber,3,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,3, self.MakeInputDeviceList(deviceID))

        form.list_action.setItem(self.rowNumber,5,QtWidgets.QTableWidgetItem())
        form.list_action.setCellWidget(self.rowNumber,5, self.setupoption[0](inputType, option[0]))

        form.list_action.setItem(self.rowNumber,6,QtWidgets.QTableWidgetItem(str(rowNumber)))

        self.rowNumber+=1

    @Slot(str,str)
    def testing(self,type, msg):
        #logging.info(type)
        form.testlabel2.setText(msg)
        form.testlabel.setText(type)
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


def setupButtonEvents(action, note, type, deviceID) :
    form.Dnote.clear()
    form.DevID.clear()
    form.addr.clear()
    form.lineType.clear()
    form.DevID.setText(str(deviceID))
    form.Dnote.setText(str(note))
    ctl=str(action)
    form.addr.setText(ctl)
    form.lineType.setText(str(type))


def setupFaderEvents(action, note, type, deviceID):
    form.Dnote.clear()
    form.DevID.clear()
    form.addr.clear()
    form.lineType.clear()
    form.DevID.setText(str(deviceID))
    form.Dnote.setText(str(note))
    ctl=str(action)
    form.addr.setText(ctl)
    form.lineType.setText(str(type))

def newFaderSetup(action, NoC, msgType, deviceID):
    if action == "SetVolume":
        source = "" # pull from dropdown
        scale = (0,1)
        action = jsonArchive["SetVolume"] % (source, "%s")
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetVolume", deviceID)
    elif action == "SetSyncOffset":
        source = "" #Pull from dropdown printArraySelect(tempSceneList)
        scale = (0,1) #askForInputScaling()
        action = jsonArchive["SetSyncOffset"] % (source, "%s")
        saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetSyncOffset", deviceID)
    elif action == "SetGainFilter":
        source = "" #Pull From Dropdown printArraySelect(tempSceneList)
        filtername = checkIfSourceHasGainFilter(source)
        if filtername:
            scale = (-30,30) #askForInputScaling()
            action = jsonArchive["SetGainFilter"] % (source, filtername, "%s")
            saveFaderToFile(msgType, NoC, "fader" , action, scale, "SetGainFilter", deviceID)
        else:
            logging.info("The selected source has no gain filter. Please add it in the source filter dialog and try again.")
            #Setup Alertbox

def ChangedScenes(scene):
    checkIfSourceHasGainFilter(scene)
    getSourceFilters(scene)
    logging.info(scene)
    updateSpecialSources()
    updateTransitionList()
    updateProfileList()
    updatesceneCollectionList()

def disconnectFromDevice():
    logging.info("Disconnect From Device")

def myExitHandler():
    logging.info("kill application")

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
    tray.showMessage("Connecting","Connecting to OBS",icon)
    #logging.info("Connecting to OBS")
def stopOBSconnection():
    icon.Off
    tray.showMessage("Disconnecting","disconnecting from OBS",icon)
if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    signal.signal(signal.SIGINT, ScriptExit)
    Form, Window = uic.loadUiType("qtOBSMIDI.ui")

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(myExitHandler)
    window = Window()
    form = Form()
    form.setupUi(window)
    window.show()
    logging.info("Program Startup")
    midi=handler()
    startuped=True
    if startuped==True:
        startup()
        startuped=False
    #initialize table

    editTable=EditTable(form)

    #ResetMidiController()

    #Setup System Tray
    icon = QIcon("icon.png")
    Menu=QtWidgets.QMenu()
    tray=QtWidgets.QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setContextMenu(Menu)
    actionStart=Menu.addAction("start")
    actionStart.triggered.connect(startStopBtnHandle)

    actionStop=Menu.addAction("Stop")
    actionStop.triggered.connect(stopOBSconnection)
    actionQuit=Menu.addAction("Quit")
    actionQuit.triggered.connect(app.quit)


    #logging.info(actionQuit)
    #midi.SendMessage.connect(editTable.testing)
    midi.SendMessage.connect(editTable.AddNewRow)
    connectToDevice()
    tray.show()
    updateSceneList()
    #editTable.MakeinputDeviceList()
    sys.exit(app.exec_())

    worker.terminate()
