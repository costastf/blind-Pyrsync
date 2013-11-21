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
from notify.notify import Notify
from utils.utils import tail
from utils.utils import checkPartitionUsage

class BackUp(object):
    def __init__(self):
        self.__cwd = os.path.abspath(os.path.dirname(__file__))
        self.attributes = Sync().__dict__['_Sync__options'].keys()
        self.email = False
        try:
            self.__notify = Notify()
            self.guiAble = True
        except ImportError:
            self.guiAble = False
    
    def setDrive(self, drive, partition):
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
            raise SystemExit    
            
    def setJobDetails(self, serial):
        self.jobs = {}
        try:
            self.__configuration = json.loads(open(os.path.join(self.__cwd, 'conf', serial.strip() + '.json')).read())
            for job, settings in self.__configuration['jobs'].iteritems():
                self.jobs[job] = {'source':settings['source'], 'destination':settings['destination']}
                try:
                    self.jobs[job].update({'defaults':settings['defaults']})                    
                except KeyError:
                    self.jobs[job].update({'defaults':False})                                        
                for key in self.attributes:
                    try:
                        self.jobs[job].update({key:settings[key]})
                    except KeyError:
                        pass
            self.enabled = self.__configuration['options']['enabled']                    
            self.eject   = self.__configuration['options']['eject']                                
            self.warning = self.__configuration['options']['percentageWarning']
            if self.guiAble:            
                self.gui = self.__configuration['options']['gui']               
            else:
                self.gui = False                
            self.stdout  = self.__configuration['report']['stdout']
            self.log     = self.__configuration['report']['log']                                
            self.summary = self.__configuration['report']['summary']            
        except:
            print('Backup configuration file not found or something wrong with the syntax.')
            raise SystemExit            
    
    def __emailReport(self, text, logFile, stdoutFile, summaryFile):
        attach = []
        import socket
        hostname = socket.gethostname()
        now = time.asctime( time.localtime(time.time()))
        if self.log:
            log = os.path.join(self.__cwd, hostname + ' ' + now + ' full report.pdf')            
            log2pdf = PyText2Pdf(ofile=log, ifilename=logFile.name, buffers=False)
            log2pdf.convert()
            attach.append(log)
        if self.stdout:
            stdout = os.path.join(self.__cwd, hostname + ' ' + now + ' stdout printout.pdf')
            stdout2pdf = PyText2Pdf(ofile=stdout, ifilename=stdoutFile.name, buffers=False)
            stdout2pdf.convert()   
            attach.append(stdout)
        if self.summary:
            summary = os.path.join(self.__cwd, hostname + ' ' + now + ' summary.pdf')                
            summary2pdf = PyText2Pdf(ofile=summary, ifilename=summaryFile.name, buffers=False)
            summary2pdf.convert()           
            attach.append(summary)                
        self.message.send( self.sender, \
                           self.recipients, \
                           self.subject, \
                           text, \
                           attachments=','.join(attach))    
        if self.log:                           
            os.unlink(log)
        if self.stdout: 
            os.unlink(stdout)
        if self.summary:            
            os.unlink(summary)
            summaryFile.close()
        os.unlink(logFile.name)            
        os.unlink(stdoutFile.name)                        
        os.unlink(summaryFile.name)            
            
    def __jobsRun(self):
        text = ''
        logFile     = tempfile.NamedTemporaryFile(delete=False)              
        stdoutFile  = tempfile.NamedTemporaryFile(delete=False)              
        summaryFile = tempfile.NamedTemporaryFile(delete=False)            
        for job, settings in self.jobs.iteritems():
            sync = Sync()
            sync.source      = settings['source']
            sync.destination = os.path.join(self.drive.mountedPath, settings['destination'])
            if settings['defaults']:
                sync.options.defaults()            
            for key in self.attributes:
                try:
                    if not settings[key]:
                        delattr(sync.options, key)
                    else:
                        setattr(sync.options, key, settings[key])
                except KeyError:
                    pass     

            partLogFile = tempfile.NamedTemporaryFile(delete=False)  
            setattr(sync.options, 'logFile', partLogFile.name)
            sync.run()
            text += '{0} done\n'.format(job)    
            with open(logFile.name, 'a') as ifile:
                ifile.write(open(partLogFile.name).read())
            with open(stdoutFile.name, 'a') as olfile:
                olfile.write('rsync stdout output :\n\n {0}'.format(sync.output))
                if sync.error:
                    olfile.write('rsync stderr output :\n\n {0}'.format(sync.error))
            with open(summaryFile.name, 'a') as sifile:
                sifile.write(job + '\n\n')                        
                sifile.write(tail(open(partLogFile.name), 13) + '\n\n')  
        if sys.platform == 'linux2':
            with open(summaryFile.name, 'a') as sifile:
                sifile.write(checkPartitionUsage(self.drive.mountedPath ,self.warning))
        return text, logFile, stdoutFile, summaryFile
    
    def run(self):
        if not self.enabled:
            out, error = self.drive.attach()
            raise SystemExit
        else:
            out, error = self.drive.mount()
            if error:
                print(error)        
                raise SystemExit
        if self.gui:
            self.__notify.message('Pyrsync Backup','Drive inserted, starting job(s)...')
        text, logFile, stdoutFile, summaryFile = self.__jobsRun()   
        out, error = self.drive.umount()
        if error:
            print(error)
        if self.email:
            self.__emailReport(text, logFile, stdoutFile, summaryFile)
        # A little time to settle
        time.sleep(5)
        if self.eject:
            message = 'Job(s) ended, ejecting drive...'
            out, error = self.drive.detach()
        else:
            message = 'Job(s) ended, attaching drive...'
            out, error = self.drive.attach()
        if self.gui:
                self.__notify.message('Pyrsync Backup', message)   
        if error:
            print(error)   

                
if __name__=='__main__':
    try:
        serial      = sys.argv[1]
        device      = sys.argv[2]
        partition   = sys.argv[3]        
    except IndexError:
        print('Not enough arguments. Exiting')
        raise SystemExit
    
    backUp = BackUp()
    backUp.setDrive(device, partition)
    backUp.enableEmail()
    backUp.setJobDetails(serial)    
    backUp.run()
