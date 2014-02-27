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
import logging
if sys.platform == 'win32':
    from win32com.shell import shell, shellcon
    import win32api, win32gui, win32con, win32file, struct

class Drive(object):
    def __init__(self, device, partition):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Initializing drive object')
        if sys.platform == 'linux2':
            self.logger.debug('Drive is in linux platform')
            if os.path.exists(device):
                self.device = device
                self.logger.debug('Device is {0}'.format(device))
                self.mountedPath = False    
                self.partition = partition  
                self.logger.debug('Partition is {0}'.format(partition))      
                self.mount = self.__mountL
                self.umount = self.__umountL
                self.detach = self.__detachL
                self.attach = self.__attachL        
                self.logger.debug('Done initializing drive object')                                        
            else:
                self.logger.error('Device {0} not found. Exiting...'.format(device))
                raise SystemExit
        elif sys.platform == 'win32':
            self.logger.debug('Drive is in windows platform')
            if os.path.exists(partition):
                self.device = device
                self.logger.debug('Device is {0}'.format(device))
                self.partition = partition        
                self.logger.debug('Partition is {0}'.format(partition))                      
                self.mountedPath = partition                
                self.mount = self.__mountW
                self.umount = self.__umountW
                self.detach = self.__detachW
                self.attach = self.__attachW                     
                self.logger.debug('Done initializing drive object')                                              
            else:
                self.logger.error('Device {0} not found. Exiting...'.format(device))
                raise SystemExit

    def __mountL(self):
        self.mountedPath = tempfile.mkdtemp()
        self.logger.debug('Temporary mounted path {0}'.format(self.mountedPath)) 
        process = Popen(['/bin/mount', self.partition, self.mountedPath], \
                        stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        if error:
            self.logger.warning('Error in mounting, removing temp path {0}'.format(self.mountedPath))
            self.logger.warning('Error was : {0}'.format(error.strip()))
            shutil.rmtree(self.mountedPath)
            self.logger.warning('Done removing temporary path') 
        return out, error

    def __umountL(self):
        report = ''
        if self.mountedPath:
            self.logger.debug('Unmounting temporary mount : {0}'.format(self.mountedPath)) 
            process = Popen(['/bin/umount', self.mountedPath], \
                            stdout=PIPE, stderr=PIPE)
            report = process.communicate()
            try:
                self.logger.debug('Removing temporary directory : {0}'.format(self.mountedPath)) 
                shutil.rmtree(self.mountedPath)
                self.logger.debug('Done removing temporary directory : {0}'.format(self.mountedPath)) 
            except OSError:
                self.logger.warning('Temporary directory {0} not found for removal'.format(self.mountedPath)) 
        else:
            self.logger.warning('There doesn\'t appear to be a temporary mounted path.') 
        return report
        
    def __detachL(self):
        self.logger.debug('Detaching device : {0}'.format(self.device)) 
        process = Popen(['/usr/bin/udisks', '--detach', self.device], \
                        stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        if error:
            self.logger.warning('Error detaching device : {0}'.format(self.device))
            self.logger.warning('Error was : {0}'.format(error.strip()))
        else:
            self.logger.debug('Successfully detached device : {0}'.format(self.device))          
        return out, error      

    def __attachL(self):
        sysname = self.partition.split('/')[-1]
        self.logger.debug('Attaching device with sysname: {0}'.format(sysname)) 
        process = Popen(['/sbin/udevadm', \
                         'trigger', \
                         '--action=change', \
                         '--sysname-match={0}'.format(sysname)], \
                         stdout=PIPE, stderr=PIPE)
        out, error = process.communicate()
        if error:
            self.logger.warning('Error attaching device : {0}'.format(self.device))
            self.logger.warning('Error was : {0}'.format(error.strip()))
        else:
            self.logger.debug('Successfully attached device : {0}'.format(self.device))     
        return out, error    
        
    def __mountW(self):
        ''' We hide the drive letter from explorer so the user cannot meddle with the rsync process,
        and we try to show a similar usage with the linux process. The drive letter will be shown to 
        the user when the rsync process is finished. Since mount is not applicable in windows we just 
        make it seem like its working like on linux.'''
        try:
            shell.SHChangeNotify(shellcon.SHCNE_DRIVEREMOVED, shellcon.SHCNF_PATH, "{0}\\".format(self.partition))
            result = True, False
        except:
            self.logger.warning('Error hiding drive letter : {0}'.format(self.partition))
            self.logger.warning('Traceback : ', exc_info=True)    
            result = True, sys.exc_info()[0]
        return result

    def __umountW(self):    
        ''' We show the drive letter in explorer  after the rsync process is done.Since mount is not 
        applicable in windows we just make it seem like its working like on linux.'''    
        try:
            shell.SHChangeNotify(shellcon.SHCNE_DRIVEADD, shellcon.SHCNF_PATH, "{0}\\".format(self.partition))
            result = True, False
        except:
            self.logger.warning('Error showing drive letter : {0}'.format(self.partition))
            self.logger.warning('Traceback : ', exc_info=True)    
            result = True, sys.exc_info()[0]
        return result
        
    def __detachW(self):    
        FSCTL_LOCK_VOLUME = 0x0090018
        FSCTL_DISMOUNT_VOLUME = 0x00090020
        IOCTL_STORAGE_MEDIA_REMOVAL = 0x002D4804
        IOCTL_STORAGE_EJECT_MEDIA = 0x002D4808
        lpFileName = r"\\.\{0}".format(self.partition)
        dwDesiredAccess = win32con.GENERIC_READ|win32con.GENERIC_WRITE
        dwShareMode = win32con.FILE_SHARE_READ|win32con.FILE_SHARE_WRITE
        dwCreationDisposition = win32con.OPEN_EXISTING
        hVolume = win32file.CreateFile(lpFileName, dwDesiredAccess, dwShareMode, None, dwCreationDisposition, 0, None)
        win32file.DeviceIoControl(hVolume, FSCTL_LOCK_VOLUME, "", 0, None)
        win32file.DeviceIoControl(hVolume, FSCTL_DISMOUNT_VOLUME, "", 0, None)
        try:
	        win32file.DeviceIoControl(hVolume, IOCTL_STORAGE_MEDIA_REMOVAL, struct.pack("B", 0), 0, None)
	        win32file.DeviceIoControl(hVolume, IOCTL_STORAGE_EJECT_MEDIA, "", 0, None)
        except:
	        raise
        finally:
	        win32file.CloseHandle(hVolume)
        time.sleep(1)
        shell.SHChangeNotify(shellcon.SHCNE_DRIVEREMOVED, shellcon.SHCNF_PATH, "{0}\\".format(self.partition)) 

    def __attachW(self):
        '''Not applicable in windows'''
        return True, False
