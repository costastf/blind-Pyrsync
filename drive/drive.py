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

import shutil, tempfile, os, time
from subprocess import Popen, PIPE

class Drive(object):
    def __init__(self, device, partition='/dev/BackupHD'):
        if os.path.exists(device):
            self.device = device
            self.mountedPath = False    
            self.partition = partition        
        else:
            print('Device not found. Exiting')
            raise SystemExit

    def mount(self):
        self.mountedPath = tempfile.mkdtemp()
        process = Popen(['/bin/mount', self.partition, self.mountedPath], stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        if error:
            print('Error in mounting, removing temp path {0}'.format(self.mountedPath))
            shutil.rmtree(self.mountedPath)
        return out, error

    def umount(self):
        report = ''
        if self.mountedPath:
            process = Popen(['/bin/umount', self.mountedPath], stdout=PIPE, stderr=PIPE)
            report = process.communicate()
            try:
                shutil.rmtree(self.mountedPath)
            except OSError:
                print('Temp mounted directory not found')
        return report
    
    def detach(self):
        process = Popen(['/usr/bin/udisks', '--detach', self.device], stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        return out, error    

