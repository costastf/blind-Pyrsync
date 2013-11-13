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

class Notify(object):
    def __init__(self):
        if sys.platform == 'linux2':
            import pynotify
            pynotify.init('Summary')
            self.__notifier = pynotify.Notification
            self.message = self.__message
            who = Popen(['who'], stdout=PIPE).stdout.read()
            for line in who.splitlines():
                if 'tty7' in line:
                    self.user = line.split()[0]            
                    self.display = line.split()[-1].replace('(','').replace(')','')
                    break            
    
    def __message(self, header, message):
        if sys.platform == 'linux2':
            os.putenv('XAUTHORITY', '/home/{0}/.Xauthority'.format(self.user))
            os.putenv('DISPLAY', self.display)
            self.__notifier(header, message).show()

