#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: backup.py
# Copyright (c) 2011 by None
#
# GNU General Public Licence (GPL)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USAe
#
__author__      = 'Costas Tyfoxylos <costas.tyf@gmail.com>'
__docformat__   = 'plaintext'
__date__        = '27/10/2013'

import json, sys, os, time, tempfile
from subprocess import Popen, PIPE
from pyrsync.pyrsync import Sync
from drive.drive import Drive
from Email.Email import Email
from pytxt2pdf.pyText2Pdf import PyText2Pdf
from utils.utils import tail
from utils.utils import checkPartitionUsage
from utils.utils import checkSwapUsage

class BackUp(object):
    def __init__(self):
        self.__cwd = os.path.abspath(os.path.dirname(__file__))
        self.attributes = Sync().__dict__['_Sync__options'].keys()
    
    def setDrive(self, drive, partition='/dev/BackupHD'):
        self.drive = Drive(drive, partition)

    def enableEmail(self, emailConfigFile = 'email.json'):
        try:
            self.__email = json.loads(open(os.path.join(self.__cwd, 'conf', emailConfigFile)).read())
            self.message    = Email(self.__email['settings']['smtp'])
            self.sender     = self.__email['settings']['sender']
            self.recipients = self.__email['settings']['recipients']
            self.subject    = self.__email['settings']['subject']
            self.email = True
        except:
            print('Email configuration file not found, or something wrong with the settings.')        
            
    def setJobDetails(self, serial):
        self.jobs = {}
        try:
            self.__configuration = json.loads(open(os.path.join(self.__cwd, 'conf', serial.strip() + '.json')).read())
            for job, settings in self.__configuration.iteritems():
                self.jobs[job] = {'source':settings['source'], 'destination':settings['destination']}
                for key in self.attributes:
                    try:
                        self.jobs[job].update({key:settings[key]})
                    except KeyError:
                        pass
        except:
            print('Backup configuration file not found or something wrong with the syntax.')

    
    def run(self, detach=True, reportOutput=True, checkStatus=True, partitionChecked='/home', partitionPercentageWarn=90, swapPercentageWarn=40, USBPercentageWarn=90):
        text = ''
        if self.drive:
            out, error = self.drive.mount()
            if error:
                return error
            logFile = tempfile.NamedTemporaryFile()              
            outputLogFile = tempfile.NamedTemporaryFile()              
            summarylogFile = tempfile.NamedTemporaryFile()            
            for job, settings in self.jobs.iteritems():
                sync = Sync()
                sync.source      = settings['source']
                sync.destination = os.path.join(self.drive.mountedPath, settings['destination'])
                for key in  self.attributes:
                    try:
                        if settings[key] == 'False' or settings[key] == 'None':
                            delattr(sync.options, key)
                        else:
                            setattr(sync.options, key, settings[key])
                    except KeyError:
                        pass     
                partLogFile = tempfile.NamedTemporaryFile()  
                setattr(sync.options, 'logFile', partLogFile.name)
                sync.run()
                if self.email:
                    text += job + ' done\n'    
                    with open(logFile.name, 'a') as ifile:
                        ifile.write(open(partLogFile.name).read())
                    with open(outputLogFile.name, 'a') as olfile:
                        olfile.write('rsync stdout output :\n\n' + sync.output + '\n\nrsync stderr output :\n\n' + sync.error)
                    with open(summarylogFile.name, 'a') as sifile:
                        sifile.write(job + '\n\n')                        
                        sifile.write(tail(open(partLogFile.name), 13) + '\n\n')  
                    #os.unlink(partLogFile.name)
            if checkStatus:
                with open(summarylogFile.name, 'a') as sifile:
                    sifile.write(checkPartitionUsage(partitionChecked, partitionPercentageWarn) + '\n\n')
                    sifile.write(checkSwapUsage(swapPercentageWarn) + '\n\n')                             
                    sifile.write(checkPartitionUsage(self.drive.mountedPath ,USBPercentageWarn) + '\n\n')
            time.sleep(1)
            out, error = self.drive.umount()
            if error:
                print(error)
            if detach:
                out, error = self.drive.detach()
                if error:
                    print(error)                
            if self.email:
                import socket
                hostname = socket.gethostname()
                now = time.asctime( time.localtime(time.time()))
                pdfLogFile = os.path.join(self.__cwd, hostname + ' ' + now + ' full report.pdf')
                pdfSummaryFile = os.path.join(self.__cwd, hostname + ' ' + now + ' summary.pdf')                
                if reportOutput:
                    report2pdf = PyText2Pdf(ofile=pdfLogFile, ifilename=outputLogFile.name, buffers=False)
                else:
                    report2pdf = PyText2Pdf(ofile=pdfLogFile, ifilename=logFile.name, buffers=False)
                report2pdf.convert()
                summary2pdf = PyText2Pdf(ofile=pdfSummaryFile, ifilename=summarylogFile.name, buffers=False)
                summary2pdf.convert()                
                self.message.send( self.sender, self.recipients, self.subject, text, attachments=pdfLogFile + ',' + pdfSummaryFile)    
                os.unlink(pdfLogFile)
                os.unlink(pdfSummaryFile)                
                
if __name__=='__main__':
    try:
        serial = sys.argv[1]
        device = sys.argv[2]
    except IndexError:
        print('Not enough arguments. Exiting')
        raise SystemExit
    
    backUp = BackUp()
    backUp.setDrive(device)
    backUp.enableEmail()
    backUp.setJobDetails(serial)    
    backUp.run(detach=True, checkStatus=True, partitionChecked='/', partitionPercentageWarn=95, swapPercentageWarn=10, USBPercentageWarn=93)
#    backUp.run()
