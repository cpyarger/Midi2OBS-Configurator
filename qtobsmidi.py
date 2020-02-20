# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Signal, Slot, QObject


import logging
import time
from time import sleep

from PySide2.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtWidgets,QtCore

Form, Window = uic.loadUiType("qtOBSMIDI.ui")
import mido, threading, sys, atexit, json, time, signal, socket
from tinydb import TinyDB, Query
from websocket import create_connection
global worker


####Change IP and Port here
serverIP = "localhost"
serverPort = "4444"
####
global stop_threads
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
    logging.info("\nUpdating transition list, plase wait")
    ws.send("""{"request-type": "GetTransitionList", "message-id": "999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    transitionList = []
    if jsn["message-id"] == "999999":
        for item in jsn["transitions"]:
            transitionList.append(item["name"])
            form.box_transitions.insertItem(counter, str(item["name"]))
            counter += 1

        logging.info("Transitions updated")
    else:
        logging.info("Failed to update")
    ws.close()

def updateSceneList():
    form.Combo_scene_list_box.clear()
    counter = 0
    global sceneListShort
    global sceneListLong
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("\nUpdating scene list, plase wait")
    ws.send("""{"request-type": "GetSceneList", "message-id": "9999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneListShort = []
    sceneListLong = []
    if jsn["message-id"] == "9999999":
        sceneListLong = jsn["scenes"]
        for item in jsn["scenes"]:
            sceneListShort.append(item["name"])
            form.Combo_scene_list_box.insertItem(counter, str(item["name"]))
            counter += 1

        logging.info("Scenes updated")
    else:
        logging.info("Failed to update")

    ws.close()

def updateSpecialSources():
    global specialSourcesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("\nUpdating special sources, plase wait")
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
        logging.info("Special sources updated")
    else:
        logging.info("Failed to update")
    ws.close()

def updateProfileList():
    form.box_profiles.clear()
    counter = 0
    global profilesList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("Updating Profiles List, plase wait")
    ws.send("""{"request-type": "ListProfiles", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    profilesList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["profiles"]:
            profilesList.append(line["profile-name"])
            form.box_profiles.insertItem(counter, str(line["profile-name"]))
            counter += 1
        logging.info("Profiles List updated")
    else:
        logging.info("Failed to update")

    ws.close()

def updatesceneCollectionList():
    form.box_collections.clear()
    counter = 0
    global sceneCollectionList
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("\nUpdating Scene Collection List, plase wait")
    ws.send("""{"request-type": "ListSceneCollections", "message-id": "99999999"}""")
    result =  ws.recv()
    jsn = json.loads(result)
    sceneCollectionList = []
    if jsn["message-id"] == "99999999":
        for line in jsn["scene-collections"]:
            sceneCollectionList.append(line["sc-name"])
            form.box_collections.insertItem(counter, str(line["sc-name"]))
            counter += 1

        logging.info("Scene Collection List updated")
    else:
        logging.info("Failed to update")
    ws.close()



def checkIfSourceHasGainFilter(sourcename):
    form.box_volumeFaders.clear()
    counter = 0
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-checksourcegainfilter", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-checksourcegainfilter":
        for line in jsn["filters"]:
            if line["type"] == "gain_filter":
                form.box_volumeFaders.insertItem(counter, str(line["name"]))
                counter += 1
                return line["name"]
    return False
def getSourceFilters(sourcename):
    form.box_filtersFaders.clear()
    counter = 0
    ws = create_connection("ws://" + serverIP + ":" + serverPort)
    logging.info("\nChecking source filters, plase wait")
    ws.send('{"request-type": "GetSourceFilters", "message-id": "MIDItoOBS-getSourceFilters", "sourceName": "' + sourcename + '"}')
    result =  ws.recv()
    ws.close()
    jsn = json.loads(result)
    if jsn["message-id"] == "MIDItoOBS-getSourceFilters":
        form.box_filtersFaders.insertItem(counter, str(jsn["filters"]))
        logging.info(str(jsn["filters"]))

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
    availableoutDeviceList = mido.get_output_names()

    deviceList = []
    counter = 0
    inUseDeviceList = devdb.all()
    for device in availableoutDeviceList:

        #logging.info("output: %s: %s" % (counter, device))
        counter += 1
        form.Combo_OutputDevices.insertItem(counter, device)

    for device in availableinDeviceList:
        if devInDB(device, inUseDeviceList):
            pass
        #logging.info("%s: %s" % (counter, device))
        counter += 1
        deviceList.append(device)

        form.Combo_InputDevices.insertItem(counter, device)

def read_from_file():
    result = db.all()

    for rowNumber, RowData in enumerate (result):
        form.list_action.insertRow(rowNumber)
        for colum_number, data in enumerate (RowData):
            #m_pTableWidget->setItem(0, 1, new QTableWidgetItem("Hello"));

            form.list_action.setItem(rowNumber, colum_number, QtWidgets.QTableWidgetItem(RowData.get(str(data))))


@Slot(int)
def setActionsSelector(int):
    form.Combo_Action.clear()
    counter = 0
    if (int == 0):
        for Action in buttonActions:
            counter += 1
            form.Combo_Action.insertItem(counter, Action)
        logging.info("0")
    if (int == 1):
        for Action in faderActions:
            counter += 1
            form.Combo_Action.insertItem(counter, Action)
        logging.info("1")
    form.Combo_Action.update()




def saveAction():
    logging.info("save")
    msg_type=str(" CC")
    msgNoC=str(" 20")
    input_type=str(form.InputTypeSelector.currentText())
    action=str(form.Combo_Action.currentText())
    deviceID=str(form.Combo_InputDevices.currentIndex()+1)
    printqt creator(msg_type, msgNoC, input_type, action, deviceID)
    #saveButtonToFile(msg_type, msgNoC, input_type, action, deviceID)
    # note_on, 20, button, action, deviceID
class MyThread(threading.Thread):

    def __init__(self, interval):
        logging.info("starting Thread")
        self.stop_event = threading.Event()
        self.interval = interval
        super(MyThread, self).__init__()


    # function using _stop function


    def run(self):
        while not self.stop_event.is_set():
            self.main()
            # wait self.interval seconds or until the stop_event is set
            self.stop_event.wait(self.interval)

    def terminate(self):
           self.stop_event.set()
    def main(self):
        #logging.info("starting")
        global ignore
        global savetime1
        global rowNumber
        global value
        note =""

        for device in midiports:
            try:
                msg = device["object"].poll()

                #logging.info(msg)
                x=msg.dict()


                # Allows for recording changed input if note or CC address is not already in list. Filtered by Note or CC (button or fader)
                # TODO: Figure out how to do this without filtering.


                if form.InputTypeSelector.currentText() == "Button":
                    items = form.table_incoming.findItems(str(x["note"]), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                else:
                    items = form.table_incoming.findItems(str(x["control"]), QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                if not items:

                    form.table_incoming.insertRow(rowNumber)

                    logging.info("start for loop")
                    for cn, data in enumerate (x):
                        #logging.info(cn)
                        #logging.info(x[data])
                        #logging.info(x)
                        form.table_incoming.setItem(rowNumber, cn, QtWidgets.QTableWidgetItem(str(x[data])))
                    rowNumber+=1
                    logging.info("end for loop")


                value = str(x["control"])
                note = str(x["note"])
                #logging.info()

                msg.reset()
                #form.list_action.setItem(rcount, ccount, QtWidgets.QTableWidgetItem(RowData.get(str(data))))
            except:
                logging.info(form.InputTypeSelector.currentText())

                logging.info("nonemsg")







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



def midicallback(message, deviceID, deviceName):
    global ignore
    #logging.info("Received message", str(message))
    #logging.info("from device", str(deviceName))

    #logging.info("type", str(message.type))
    #logging.info("devID", str(deviceID))
    action=""
    if message.type == "note_on": #button only
        ignore = message.note
        setupButtonEvents(action, message.note, message.type, deviceID)
    elif message.type == "control_change": #button or fader
        setupFaderEvents(action, message.control, message.type, deviceID)
def thread_function(name):
    logging.info("Thread %s: starting", str(name))


def flatten():
    global worker
    #form.btn_RecordInput.isFlat=True
    if form.btn_RecordInput.isChecked()==True:
        worker = MyThread(interval=.01)
        worker.start()
    if form.btn_RecordInput.isChecked()==False:
        logging.info("stop worker")
        worker.terminate()

def connectToDevice():
    devices = devdb.all()
    for device in devices: #gave up on documentation here
        try:
            tempmidiport = mido.open_input(device["devicename"])
            tempobj = {"id": device.doc_id, "object": tempmidiport, "devicename": device["devicename"]}
            midiports.append(tempobj)
            info="successfully opened" + str(device["devicename"])
            logging.info(info)
        except:
            logging.info("\nCould not open", str(device["devicename"]))
            logging.info("The midi device might be used by another application/not plugged in/have a different name.")
            logging.info("Please close the device in the other application/plug it in/select the rename option in the device management menu and restart this script.\n")
            database.close()
            sys.exit(5)

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

    logging.info("stop worker")
    worker.terminate()
    logging.info("kill application")

def startup():
    setActionsSelector(0)
    read_from_file()
    getDevices()

class qtobsmidi(QMainWindow):
    def currentIndexChanged(self, qmodelindex):
            item = self.InputTypeSelector.currentItem()
            logging.info(str(item.index()))
    def __init__(self):
        QMainWindow.__init__(self)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    signal.signal(signal.SIGINT, ScriptExit)
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(myExitHandler)
    window = Window()
    form = Form()
    form.setupUi(window)
    window.show()
    logging.info("Program Startup")
    startuped=True
    if startuped==True:
        startup()
        connectToDevice()
        startuped=False
    form.Combo_scene_list_box.currentTextChanged.connect(ChangedScenes)
    form.btn_Add.clicked.connect(saveAction)
    form.btn_RecordInput.clicked.connect(flatten)
    form.InputTypeSelector.currentIndexChanged.connect(setActionsSelector)
    updateSceneList()
    sys.exit(app.exec_())
    worker.terminate()
