#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: drive.py
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
__date__      = '30/09/2013'

import shutil
import tempfile
import os
import time
import sys
from subprocess import Popen, PIPE

class Drive(object):
    def __init__(self, device, partition):
        if sys.platform == 'linux2':
            if os.path.exists(device):
                self.device = device
                self.mountedPath = False    
                self.partition = partition        
                self.mount = self.__mountL
                self.umount = self.__umountL
                self.detach = self.__detachL
                self.attach = self.__attachL                                                
            else:
                print('Device not found. Exiting')
                raise SystemExit
        elif sys.platform == 'win32':
            if os.path.exists(partition):
                self.device = device
                self.partition = partition        
                self.mountedPath = partition                
                self.mount = self.__mountW
                self.umount = self.__umountW
                self.detach = self.__detachW
                self.attach = self.__attachW                                                
            else:
                print('Device not found. Exiting')
                raise SystemExit

    def __mountL(self):
        self.mountedPath = tempfile.mkdtemp()
        process = Popen(['/bin/mount', self.partition, self.mountedPath], \
                        stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        if error:
            print('Error in mounting, removing temp path {0}'.format(self.mountedPath))
            print('Error : {0}'.format(error))
            shutil.rmtree(self.mountedPath)
        return out, error

    def __mountW(self):
        return True, False

    def __umountL(self):
        report = ''
        if self.mountedPath:
            process = Popen(['/bin/umount', self.mountedPath], \
                            stdout=PIPE, stderr=PIPE)
            report = process.communicate()
            try:
                shutil.rmtree(self.mountedPath)
            except OSError:
                print('Temp mounted directory not found')
        return report

    def __umountW(self):    
        return True, False
    
    def __detachL(self):
        process = Popen(['/usr/bin/udisks', '--detach', self.device], \
                        stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        return out, error    

    def __detachW(self):    
        pass
    
    def __attachL(self):
        sysname = self.partition.split('/')[-1]
        process = Popen(['/sbin/udevadm', \
                         'trigger', \
                         '--action=change', \
                         '--sysname-match={0}'.format(sysname)], \
                         stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        return out, error    

    def __attachW(self):
        return True, False
