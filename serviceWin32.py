#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: windowsService.py
# Copyright (c) 2013 by None
#
# GNU General Public Licence (GPL)
# 
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#
__author__    = 'Costas Tyfoxylos <costas.tyf@gmail.com>'
__docformat__ = 'plaintext'
__date__      = '15/11/2013'

import win32serviceutil
import win32service
import win32event
import servicemanager
import time
import win32gui
import win32gui_struct
struct = win32gui_struct.struct
pywintypes = win32gui_struct.pywintypes
import win32con
GUID_DEVINTERFACE_USB_DEVICE = "{A5DCBF10-6530-11D2-901F-00C04FB951ED}"
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004
from subprocess import Popen, PIPE
import ctypes
import os


PYTHONPATH = r'C:\Program Files\Python\python.exe'
STAGINGPROG = r'P:\backupWin32.py'

# Cut-down clone of UnpackDEV_BROADCAST from win32gui_struct, to be
# used for monkey-patching said module with correct handling
# of the "name" param of DBT_DEVTYPE_DEVICEINTERFACE
#
def _UnpackDEV_BROADCAST (lparam):
    if lparam == 0: return None
    hdr_format = "iii"
    hdr_size = struct.calcsize (hdr_format)
    hdr_buf = win32gui.PyGetMemory (lparam, hdr_size)
    size, devtype, reserved = struct.unpack ("iii", hdr_buf)
    # Due to x64 alignment issues, we need to use the full format string over
    # the entire buffer.  ie, on x64:
    # calcsize('iiiP') != calcsize('iii')+calcsize('P')
    buf = win32gui.PyGetMemory (lparam, size)

    extra = {}
    if devtype == win32con.DBT_DEVTYP_DEVICEINTERFACE:
        fmt = hdr_format + "16s"
        _, _, _, guid_bytes = struct.unpack (fmt, buf[:struct.calcsize(fmt)])
        extra['classguid'] = pywintypes.IID (guid_bytes, True)
        extra['name'] = ctypes.wstring_at (lparam + struct.calcsize(fmt))
    else:
        raise NotImplementedError("unknown device type %d" % (devtype,))
    return win32gui_struct.DEV_BROADCAST_INFO(devtype, **extra)
win32gui_struct.UnpackDEV_BROADCAST = _UnpackDEV_BROADCAST

class DeviceEventService (win32serviceutil.ServiceFramework):

    _svc_name_ = "DevEventHandler"
    _svc_display_name_ = "Device Event Handler"
    _svc_description_ = "Handle device notification events"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__ (self, args)
        self.hWaitStop = win32event.CreateEvent (None, 0, 0, None)
        #
        # Specify that we're interested in device interface
        # events for USB devices
        #
        filter = win32gui_struct.PackDEV_BROADCAST_DEVICEINTERFACE (
            GUID_DEVINTERFACE_USB_DEVICE
        )
        self.hDevNotify = win32gui.RegisterDeviceNotification (
            self.ssh, # copy of the service status handle
            filter,
            win32con.DEVICE_NOTIFY_SERVICE_HANDLE
        )

    #
    # Add to the list of controls already handled by the underlying
    # ServiceFramework class. We're only interested in device events
    #
    def GetAcceptedControls(self):
        rc = win32serviceutil.ServiceFramework.GetAcceptedControls (self)
        rc |= win32service.SERVICE_CONTROL_DEVICEEVENT
        return rc

    #
    # Handle non-standard service events (including our device broadcasts)
    # by logging to the Application event log
    #
    def SvcOtherEx(self, control, event_type, data):
        if control == win32service.SERVICE_CONTROL_DEVICEEVENT:
            info = win32gui_struct.UnpackDEV_BROADCAST(data)
        #
        # This is the key bit here where you'll presumably
        # do something other than log the event. Perhaps pulse
        # a named event or write to a secure pipe etc. etc.
        #
        serial = info.name.split('#')[2].strip()
        if event_type == DBT_DEVICEARRIVAL:
            servicemanager.LogMsg (
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                0xF000,
                ("Device %s arrived" % serial, '')
            )
            Popen([PYTHONPATH, STAGINGPROG, serial],close_fds=True)
        elif event_type == DBT_DEVICEREMOVECOMPLETE:
            servicemanager.LogMsg (
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                0xF000,
                ("Device %s removed" % serial, '')
            )
    #
    # Standard stuff for stopping and running service; nothing
    # specific to device notifications
    #
    def SvcStop(self):
        self.ReportServiceStatus (win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent (self.hWaitStop)

    def SvcDoRun(self):
        win32event.WaitForSingleObject (self.hWaitStop, win32event.INFINITE)
        servicemanager.LogMsg (
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

if __name__=='__main__':
    win32serviceutil.HandleCommandLine (DeviceEventService)
