#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: Notify.py
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
__date__      = '13/11/2013'

import sys
import os
from subprocess import Popen,PIPE
import logging


if sys.platform == 'linux2':
    import pynotify
if sys.platform == 'win32':
    from threading import Thread
    import win32api
    import win32gui
    import win32con
    import struct
    import time

#Gist from https://gist.github.com/wontoncc/1808234 THNX!!!!
class WindowsBalloonTip(object):
    def __init__(self):
        message_map = {win32con.WM_DESTROY: self.__OnDestroy,}
        wc = win32gui.WNDCLASS()
        self.hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "PythonTaskbar"
        wc.lpfnWndProc = message_map
        self.classAtom = win32gui.RegisterClass(wc)
        self.style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU

    def message(self, title, msg):
        self.hwnd = win32gui.CreateWindow( self.classAtom, "Taskbar", self.style, \
                0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                0, 0, self.hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)            
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "tooltip")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, \
                         (self.hwnd, 0, win32gui.NIF_INFO, win32con.WM_USER+20,\
                          hicon, "Balloon  tooltip",msg,200,title))
        time.sleep(5)
        win32gui.DestroyWindow(self.hwnd)
    def __OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)


class Notify(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Initializing notify object')
        if sys.platform == 'linux2':
            self.user = ''
            who = Popen(['/usr/bin/who'], stdout=PIPE).stdout.read()
            for line in who.splitlines():
                if 'tty7' in line:
                    self.user = line.split()[0]  
                    if '(' in line.split()[-1]:
                        self.display = line.split()[-1].replace('(','').replace(')','')
                    else:
                        self.display = ':0'
                    break
            self.logger.debug('Set user : {0}'.format(self.user))
            self.logger.debug('Set display : {0}'.format(self.display))
            self.logger.debug('Initializing pynotify')
            pynotify.init('Summary')
            self.__notifier = pynotify.Notification
            self.message = self.__message
                       
        if sys.platform == 'win32':
            self.logger.debug('Initializing WindowsBalloonTip')
            self.__notifier = WindowsBalloonTip()
            self.message = self.__message
            
    def __message(self, header, message):
        if sys.platform == 'linux2':
            os.putenv('XAUTHORITY', '/home/{0}/.Xauthority'.format(self.user))
            os.putenv('DISPLAY', self.display)
            self.logger.debug('Showing message.')
            self.__notifier(header, message).show()
            self.logger.debug('Done showing message.')
        if sys.platform == 'win32':
            tip = Thread(target=self.__notifier.message, args=(header, message))
            tip.start()                 
