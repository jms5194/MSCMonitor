# !/usr/bin/env python3
# -- coding: utf-8

"""MSC Monitor"""

__author__ = "Justin Stasiw"
__version__ = "$Revision 2.0$"
__date__ = "$Date: 2024/11/16"

from pubsub import pub
import wx
import sys
import midi_functions
import config_functions
import settings


class MSCPrintoutGUI(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="MSC Monitor")
        # Check for .ini file and populate settings.py with stored variables
        config_functions.check_configuration(config_functions.where_to_put_user_data())
        # Set Position and size of window based upon stored location
        self.SetPosition(settings.window_loc)
        self.SetSize(settings.window_size)
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        # Select Interface Label
        listener_text = wx.StaticText(panel, label="Select Interface:", style=wx.ALIGN_CENTER)
        panel_sizer.Add(listener_text, 0, wx.ALL | wx.EXPAND, 5)
        interface_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.Add(interface_sizer, 0, wx.ALL | wx.EXPAND, 5)
        # Refresh Interfaces button
        self.Refresh_Interfaces = wx.Button(panel, -1, "Refresh Interfaces")
        interface_sizer.Add(self.Refresh_Interfaces, 0, wx.ALL | wx.EXPAND, 5)
        # Interface selector dropdown
        self.Midi_Selector = wx.Choice(panel)
        interface_sizer.Add(self.Midi_Selector, 1, wx.ALL | wx.EXPAND, 5)

        # Log Window
        self.Msg_Panel = wx.ListCtrl(panel, size=(-1, 150), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.Msg_Panel.InsertColumn(0, "Timestamp", width=160, format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(1, "Device ID", format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(2, "Command Format", width=150, format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(3, "Command Type", width=130, format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(4, "Cue Number", width=150, format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(5, "Cue List", width=100, format=wx.LIST_FORMAT_CENTRE)
        self.Msg_Panel.InsertColumn(6, "Cue Path", width=100, format=wx.LIST_FORMAT_CENTRE)

        panel_sizer.Add(self.Msg_Panel, 1, wx.ALL | wx.EXPAND, 5)
        # Clear log button
        button_grid = wx.GridSizer(1, 2, 10, 10)
        # Clear Contents button
        clear_contents = wx.Button(panel, label="Clear MSC Log")
        button_grid.Add(clear_contents, flag=wx.ALIGN_CENTER_HORIZONTAL)
        save_as_log = wx.Button(panel, label="Save Log As...")
        button_grid.Add(save_as_log, flag=wx.ALIGN_CENTER_HORIZONTAL)
        panel_sizer.Add(button_grid, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(panel_sizer)

        filemenu = wx.Menu()
        m_about = filemenu.Append(wx.ID_ABOUT, "&About", "Info about this program.")
        filemenu.AppendSeparator()
        m_save = filemenu.Append(wx.ID_SAVE, "&Save Log as...", "Save this log to a file.")
        m_exit = filemenu.Append(wx.ID_EXIT, "&Exit\tAlt-X", "Close window and exit program.")
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        self.SetMenuBar(menubar)

        # Event bindings
        self.Bind(wx.EVT_CHOICE, self.update_interfaces)
        self.Bind(wx.EVT_BUTTON, self.on_clicked)
        self.Bind(wx.EVT_CLOSE, self.quit_app)
        self.Bind(wx.EVT_MENU, self.quit_app, m_exit)
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        self.Bind(wx.EVT_MENU, self.save_log_dialog, m_save)
        # Subscribe to new log messages and updates to the midi ports
        pub.subscribe(self.add_msg, 'logUpdates')
        pub.subscribe(self.add_choices, 'availablePorts')
        # Populate the midi ports dropdown
        self.midi_choices = None
        midi_functions.available_midi_ports()
        # Initialize the log
        self.log_index = 0
        self.Show()

    def on_about(self, event):
        # Create the About Dialog Box
        dlg = wx.MessageDialog(self, " A Midi monitor for MSC. Written by Justin Stasiw. Copyright 2025.",
                               "MSC Monitor", wx.OK)
        dlg.ShowModal()  # Shows it
        dlg.Destroy()  # Destroy pop-up when finished.

    def add_msg(self, msg):
        # Add new items to log
        wx.CallAfter(self.Msg_Panel.InsertItem, self.log_index, msg[0])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 1, msg[1])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 2, msg[2])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 3, msg[3])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 4, msg[4])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 5, msg[5])
        wx.CallAfter(self.Msg_Panel.SetItem, self.log_index, 6, msg[6])
        wx.CallAfter(self.Msg_Panel.EnsureVisible, self.log_index)
        # Set the color of the most recently received log item and reset the others as required
        if self.log_index > 0:
            wx.CallAfter(self.Msg_Panel.SetItemBackgroundColour, self.log_index, (16, 32, 240, 100))
            wx.CallAfter(self.Msg_Panel.SetItemBackgroundColour, (self.log_index - 1),
                         wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DDKSHADOW))
        self.log_index += 1

    def add_choices(self, choices):
        # Add choices to the midi port selector dropdown
        self.Midi_Selector.Clear()
        self.Midi_Selector.Append("\n")
        self.Midi_Selector.Append(choices)
        self.midi_choices = [""] + choices

    def update_interfaces(self, event):
        chosen_port = self.midi_choices[event.Selection]
        pub.sendMessage('chosenPort', port_to_open=chosen_port)

    def on_clicked(self, event):
        # Respond to button pressed events
        btn = event.GetEventObject().GetLabel()
        if btn == "Clear MSC Log":
            self.Msg_Panel.DeleteAllItems()
            self.log_index = 0
        elif btn == "Refresh Interfaces":
            pub.sendMessage('refreshInterfaces')
        elif btn == "Save Log As...":
            self.save_log_dialog(None)

    def quit_app(self, event):
        # Grab the current size and position of the app
        # and update the config file.
        cur_size = self.GetTopLevelParent().GetSize()
        cur_pos = self.GetTopLevelParent().GetPosition()
        ini_path = config_functions.where_to_put_user_data()
        config_functions.update_pos_in_config(cur_pos, ini_path)
        config_functions.update_size_in_config(cur_size, ini_path)
        self.Destroy()
        sys.exit()

    def save_log_dialog(self, event):
        # Build a save as dialog for the log
        with wx.FileDialog(self, "Save Log file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    self.save_log(file)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def save_log(self, file):
        item_count = self.Msg_Panel.GetItemCount()
        column_count = self.Msg_Panel.GetColumnCount()

        try:
            # Header Row:
            file.write("Timestamp,Device ID,Command Format,Command Type,Cue Number,Cue List,Cue Path" + "\n")
            # Write the MSC data, comma separated
            for i in range(item_count):
                if i != 0:
                    file.write("\n")
                for c in range(column_count):
                    item = self.Msg_Panel.GetItemText(item=i, col=c)
                    file.write(str(item))
                    file.write(",")
            file.close()
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    app = wx.App()
    frame = MSCPrintoutGUI()
    app.MainLoop()
