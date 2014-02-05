#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: backupWin32.py
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

import sys
import time
import wmi
from backup import BackUp

def getDriveLetterFromSerial(serial):
    try:
        c = wmi.WMI ()
        for disk in c.Win32_DiskDriveToDiskPartition():
            deviceSerial = disk.Antecedent.PNPDeviceID.split('\\')[-1].split('&')[0]
            if deviceSerial == serial:
                systemName = disk.Antecedent.SystemName                
                diskIndex = disk.Dependent.DiskIndex
                for partition in c.Win32_LogicalDiskToPartition():
                    if partition.Antecedent.DiskIndex == diskIndex:
                        driveLetter = partition.Dependent.Name
                        return systemName, driveLetter
    except Exception, e:
        print('Something happened with the drive query :{0}.Quiting..'.format(e))
        raise SystemExit


if __name__=='__main__':
    try:
        serial = sys.argv[1]
    except IndexError:
        print('Not enough arguments. Exiting')
        raise SystemExit
    device, partition = getDriveLetterFromSerial(serial)    
    backUp = BackUp()
    backUp.setDrive(device, partition)
    backUp.enableEmail()
    backUp.setJobDetails(serial)    
    backUp.run()