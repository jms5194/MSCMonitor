# !/usr/bin/env python3
# -- coding: utf-8

"""MSC Monitor"""

__author__ = "Justin Stasiw"
__version__ = "$Revision 1.0$"
__date__ = "$Date: 2024/11/16"

from pubsub import pub
import wx
import sys
import midi_functions


class MSCPrintoutGUI(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, size=(900, 300), title="MSC Monitor")
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
        self.Msg_Panel = wx.TextCtrl(panel, size=(-1, 150), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        msg_panel_default_style: wx.TextAttr = self.Msg_Panel.GetDefaultStyle()
        msg_panel_default_style.SetFontFamily(wx.FONTFAMILY_TELETYPE | wx.FONTSIZE_XX_LARGE)
        self.Msg_Panel.SetDefaultStyle(msg_panel_default_style)
        panel_sizer.Add(self.Msg_Panel, 1, wx.ALL | wx.EXPAND, 5)
        clear_contents = wx.Button(panel, -1, "Clear MSC Log")
        panel_sizer.Add(clear_contents, 0, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(panel_sizer)

        filemenu = wx.Menu()
        about_menuitem = filemenu.Append(wx.ID_ABOUT, "&About", "Info about this program")
        filemenu.AppendSeparator()
        m_exit = filemenu.Append(wx.ID_EXIT, "&Exit\tAlt-X", "Close window and exit program.")
        # properties_menuitem = filemenu.Append(wx.ID_PROPERTIES, "Properties", "Program Settings")
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_CHOICE, self.update_interfaces)
        self.Bind(wx.EVT_BUTTON, self.on_clicked)
        self.Bind(wx.EVT_CLOSE, self.quit_app)
        self.Bind(wx.EVT_MENU, self.quit_app, m_exit)
        self.Bind(wx.EVT_MENU, self.on_about, about_menuitem)
        pub.subscribe(self.add_msg, 'logUpdates')
        pub.subscribe(self.add_choices, 'availablePorts')
        self.midi_choices = None
        midi_functions.available_midi_ports()

        self.Show()

    def on_about(self, event):
        # Create the About Dialog Box
        dlg = wx.MessageDialog(self, " A Midi monitor for MSC. Written by Justin Stasiw. Copyright 2025.",
                               "MSC Monitor", wx.OK)
        dlg.ShowModal()  # Shows it
        dlg.Destroy()  # Destroy pop-up when finished.

    def add_msg(self, msg):
        current_lines = self.Msg_Panel.GetNumberOfLines()
        if current_lines <= 1000:
            wx.CallAfter(self.Msg_Panel.AppendText, msg + "\n")
        else:
            # wx.CallAfter(self.Msg_Panel.Remove, 0, self.Msg_Panel.GetLineLength(0) + 1)
            # This remove line is too process intensive. Can it be optimized?
            # Hacky solution for now:
            wx.CallAfter(self.Msg_Panel.Clear)
            wx.CallAfter(self.Msg_Panel.AppendText, msg + "\n")

    def add_choices(self, choices):
        print("Choices added")
        self.Midi_Selector.Clear()
        self.Midi_Selector.Append("\n")
        self.Midi_Selector.Append(choices)
        self.midi_choices = [""] + choices

    def update_interfaces(self, event):
        chosen_port = self.midi_choices[event.Selection]
        pub.sendMessage('chosenPort', port_to_open=chosen_port)

    def on_clicked(self, event):
        btn = event.GetEventObject().GetLabel()
        if btn == "Clear MSC Log":
            wx.CallAfter(self.Msg_Panel.Clear)
        elif btn == "Refresh Interfaces":
            pub.sendMessage('refreshInterfaces')

    def quit_app(self, event):
        print("Quitting App")
        self.Destroy()
        sys.exit()


if __name__ == "__main__":
    app = wx.App()
    frame = MSCPrintoutGUI()
    app.MainLoop()
