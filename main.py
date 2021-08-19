# !/usr/bin/env python3
# -- coding: utf-8

"""MSC Monitor"""

__author__ = "Justin Stasiw"
__version__ = "$Revision 0.1b$"
__date__ = "$Date: 2021/08/05"

import mido
import mido.backends.rtmidi
from datetime import datetime
from threading import Thread
from pubsub import pub
import multiprocessing
from multiprocessing import Process, Queue
import wx
import sys


def GetMidiInputNames(queue):
    names = mido.get_input_names()
    queue.put(names)

class MSCPrintout(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.start()
        self.MidiIn = None
        mido.set_backend('mido.backends.rtmidi')
        self.Command_Formats = {
            0: "Reserved",
            1: "Lighting",
            2: "Moving Lights",
            3: "Colour Changers",
            4: "Strobes",
            5: "Lasers",
            6: "Chasers",
            16: "Sound",
            17: "Music",
            18: "CD Players",
            19: "EEPROM Playback",
            20: "Audio Tape Machines",
            21: "Intercoms",
            22: "Amplifiers",
            23: "Audio Effects Devices",
            24: "Equalisers",
            32: "Machinery",
            33: "Rigging",
            34: "Flys",
            35: "Lifts",
            36: "Turntables",
            37: "Trusses",
            38: "Robots",
            39: "Animation",
            40: "Floats",
            41: "Breakaways",
            42: "Barges",
            48: "Video",
            49: "Video Tape Machines",
            50: "Video Cassette Machines",
            51: "Video Disc Players",
            52: "Video Switchers",
            53: "Video Effects:",
            54: "Video Character Generators",
            55: "Video Still Stores",
            56: "Video Monitors",
            64: "Projection",
            65: "Film Projectors",
            66: "Slide Projectors",
            67: "Video Projectors",
            68: "Dissolvers",
            69: "Shutter Controls",
            80: "Process Control",
            81: "Hydraulic Oil",
            82: "H2O",
            83: "CO2",
            84: "Compressed Air",
            85: "Natural Gas",
            86: "Fog",
            87: "Smoke",
            88: "Cracked Haze",
            96: "Pyro",
            97: "Fireworks",
            98: "Explosions",
            99: "Flame",
            100: "Smoke Pots",
            127: "All-Types"
        }
        self.Command_Types = {
            0: "Reserved",
            1: "GO",
            2: "STOP",
            3: "RESUME",
            4: "TIMED_GO",
            5: "LOAD",
            6: "SET",
            7: "FIRE",
            8: "ALL_OFF",
            9: "RESTORE",
            10: "RESET",
            11: "GO_OFF",
            16: "GO/JAM CLOCK",
            17: "STANDBY_+",
            18: "STANDBY_-",
            19: "SEQUENCE_+",
            20: "SEQUENCE_-",
            21: "START_CLOCK",
            22: "STOP_CLOCK",
            23: "ZERO_CLOCK",
            24: "SET_CLOCK",
            25: "MTC_CHASE_ON",
            26: "MTC_CHASE_OFF",
            27: "OPEN_CUE_LIST",
            28: "CLOSE_CUE_LIST",
            29: "OPEN_CUE_PATH",
            30: "CLOSE_CUE_PATH"
        }

    def run(self):
        self.AvailableMidiPorts()
        pub.subscribe(self.AvailableMidiPorts, 'refreshInterfaces')

    def AvailableMidiPorts(self):
        queue = Queue()
        p = Process(target=GetMidiInputNames, args=(queue,))
        p.start()
        p.join()
        AvailablePorts = queue.get()
        AvailablePorts = list(dict.fromkeys(AvailablePorts))
        pub.sendMessage('availablePorts', choices=AvailablePorts)
        pub.subscribe(self.OpenMidiPort, "chosenPort")

    def OpenMidiPort(self, port_to_open):
        # Opens Midi Input Port, Starts thread for Midi Receive.
        if self.MidiIn != None:
            self.MidiIn.close()
        try:
            self.MidiIn = mido.open_input(port_to_open)
        except:
            print("Failed to open midi port")
        try:
            if MidiReceiveThread.is_alive():
                pass
        except:
            MidiReceiveThread = Thread(target=self.MidiReceiveHandler, daemon=True)
            MidiReceiveThread.start()

    def MidiReceiveHandler(self):
        # Passes off incoming midi from controller to the relevant Defs
        if self.MidiIn != None:
            for msg in self.MidiIn:
                if msg.type == "sysex":
                    wx.CallAfter(self.MSCTranslator, msg)
                del msg

    def MSCTranslator(self, msg):
        incoming_sysex = msg.data
        # Check for MSC:
        if incoming_sysex[0] == 127 and incoming_sysex[2] == 2:
            Device_ID = str(incoming_sysex[1])
            Command_Format = incoming_sysex[3]
            if incoming_sysex[3] in self.Command_Formats:
                Command_Format = self.Command_Formats[incoming_sysex[3]]
            else:
                Command_Format = "Invalid"
            if incoming_sysex[4] in self.Command_Types:
                Command_Type = self.Command_Types[incoming_sysex[4]]
            else:
                Command_Type = "Invalid"
            remaining_data = incoming_sysex[5:]
            size = len(remaining_data)
            # List Comprehension magic that I don't really understand:
            try:
                idx_list = [idx + 1 for idx, val in enumerate(remaining_data) if val == 0]
                res = [remaining_data[i:j] for i, j in
                       zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))]
                counter = 0
                for i in res:
                    if i[-1] == 0:
                        i = i[:-1]
                        res[counter] = i
                    counter += 1
            except:
                res = [remaining_data]
            try:
                cue_number_data = res[0]
            except:
                cue_number_data = ""
            try:
                cue_list_data = res[1]
            except:
                cue_list_data = ""
            try:
                cue_path_data = res[2]
            except:
                cue_path_data = ""
            cue_number_hex = ""
            try:
                if cue_number_data != "":
                    for i in cue_number_data:
                        cue_number_hex += hex(i)[2:]
                    cue_number_bytes = bytes.fromhex(cue_number_hex)
                    cue_number = cue_number_bytes.decode("ASCII")
                else:
                    cue_number = ""
            except:
                cue_number = ""
            cue_list_hex = ""
            try:
                if cue_list_data != "":
                    for i in cue_list_data:
                        cue_list_hex += hex(i)[2:]
                    cue_list_bytes = bytes.fromhex(cue_list_hex)
                    cue_list = cue_list_bytes.decode("ASCII")
                else:
                    cue_list = ""
            except:
                cue_list = ""
            cue_path_hex = ""
            try:
                if cue_path_data != "":
                    for i in cue_path_data:
                        cue_path_hex += hex(i)[2:]
                    cue_path_bytes = bytes.fromhex(cue_path_hex)
                    cue_path = cue_path_bytes.decode("ASCII")
                else:
                    cue_path = ""
            except:
                cue_path = ""
            current_time = datetime.now()
            timestamp_str = current_time.strftime("%d-%b-%Y (%H:%M:%S)")
            msg_to_snd = timestamp_str + ":   Device ID:" + Device_ID + "   Command Format:" + Command_Format + "   Command Type:" + Command_Type + "   Cue Number:" + cue_number + "   Cue List:" + cue_list + "   Cue Path:" + cue_path
            pub.sendMessage('logUpdates', msg=msg_to_snd)


class MSCPrintoutGUI(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, size=(900, 300), title="MSC Monitor")
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        Listener_Text = wx.StaticText(panel, label="Select Interface:", style=wx.ALIGN_CENTER)
        panel_sizer.Add(Listener_Text, 0, wx.ALL | wx.EXPAND, 5)
        interface_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.Add(interface_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.Refresh_Interfaces = wx.Button(panel, -1, "Refresh Interfaces")
        interface_sizer.Add(self.Refresh_Interfaces, 0, wx.ALL | wx.EXPAND, 5)
        self.Midi_Selector = wx.Choice(panel)
        interface_sizer.Add(self.Midi_Selector, 1, wx.ALL | wx.EXPAND, 5)
        self.Msg_Panel = wx.TextCtrl(panel, size=(-1, 150), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        panel_sizer.Add(self.Msg_Panel, 1, wx.ALL | wx.EXPAND, 5)
        Clear_Contents = wx.Button(panel, -1, "Clear MSC Log")
        panel_sizer.Add(Clear_Contents, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(panel_sizer)
        self.Show()
        self.Processor = MSCPrintout()
        self.Bind(wx.EVT_CHOICE, self.UpdateInterface)
        self.Bind(wx.EVT_BUTTON, self.OnClicked)
        self.Bind(wx.EVT_CLOSE, self.QuitApp)
        pub.subscribe(self.Add_Msg, 'logUpdates')
        pub.subscribe(self.Add_Choices, 'availablePorts')
        self.midi_choices = None
        menubar = wx.MenuBar()
        wx.MenuBar.MacSetCommonMenuBar(menubar)

    def Add_Msg(self, msg):
        current_lines = self.Msg_Panel.GetNumberOfLines()
        if current_lines <= 1000:
            wx.CallAfter(self.Msg_Panel.AppendText, msg + "\n")
        else:
            #wx.CallAfter(self.Msg_Panel.Remove, 0, self.Msg_Panel.GetLineLength(0) + 1)
            #This remove line is too process intensive. Can it be optimized?
            #Hacky solution for now:
            wx.CallAfter(self.Msg_Panel.Clear)
            wx.CallAfter(self.Msg_Panel.AppendText, msg + "\n")

    def Add_Choices(self, choices):
        self.Midi_Selector.Clear()
        self.Midi_Selector.Append("\n")
        self.Midi_Selector.Append(choices)
        self.midi_choices = [""] + choices

    def UpdateInterface(self, event):
        chosenPort = self.midi_choices[event.Selection]
        pub.sendMessage('chosenPort', port_to_open=chosenPort)

    def OnClicked(self, event):
        btn = event.GetEventObject().GetLabel()
        if btn == "Clear MSC Log":
            wx.CallAfter(self.Msg_Panel.Clear)
        elif btn == "Refresh Interfaces":
            pub.sendMessage('refreshInterfaces')

    def QuitApp(self, event):
        print("Quitting App")
        self.Destroy()
        sys.exit()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = wx.App()
    frame = MSCPrintoutGUI()
    app.MainLoop()