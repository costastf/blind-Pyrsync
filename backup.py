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
import socket
import logging.config

logger = logging.getLogger(__name__)
currentPath, _, scriptName = sys.argv[0].rpartition('/')
logConfig = os.path.join(currentPath,'conf','logging.json')
config = json.loads(open(logConfig).read())
logging.config.dictConfig(config)


class BackUp(object):   
    def __init__(self):
        logger.debug('Initializing backup object.')
        self.__cwd = os.path.abspath(os.path.dirname(__file__))
        self.attributes = Sync().__dict__['_Sync__options'].keys()
        self.email = False
        try:
            logger.debug('Trying to enable gui.')
            from notify.notify import Notify
            self.__notify = Notify()
            self.guiAble = True
            logger.debug('Gui enabled')            
        except Exception:
            self.guiAble = False
            logger.warning('Error in enabling gui')   
            logger.warning('Traceback : ', exc_info=True)         
    
    def setDrive(self, drive, partition):
        logger.debug('Initializing drive object')
        self.drive = Drive(drive, partition)
        logger.debug('Drive object initialized')        

    def enableEmail(self, emailConfigFile = 'email.json'):
        try:
            logger.debug('Getting email settings')
            self.__email = json.loads(open(os.path.join(self.__cwd, 'conf', emailConfigFile)).read())
            self.message = Email(self.__email['settings']['smtp'])
            logger.debug('Email : %s' % self.message)
            self.sender = self.__email['settings']['sender']
            logger.debug('Sender : %s'% self.sender)
            self.recipients = self.__email['settings']['recipients']
            logger.debug('Recipients : %s' % self.recipients)
            self.subject = self.__email['settings']['subject']
            logger.debug('Subject : %s' % self.subject)
            self.email = True
            logger.debug('Email configured successfully')
        except:
            logger.error('Email configuration file not found, or something wrong with the settings.')
            logger.error('Traceback : ', exc_info=True)
            raise SystemExit    
            
    def setJobDetails(self, serial):
        self.jobs = {}
        try:
            logger.debug('Getting jobs configuration for drive with serial : {0}'.format(serial))
            self.__configuration = json.loads(open(os.path.join(self.__cwd, 'conf', serial.strip() + '.json')).read())
            logger.debug('Done getting jobs configuration for drive with serial : {0}'.format(serial))
            for job, settings in self.__configuration['jobs'].iteritems():
                self.jobs[job] = {'source':settings['source'], 'destination':settings['destination']}
                logger.debug('Getting job\'s "{0}" configuration from file '.format(job))
                logger.debug('Job\'s "{0}" source : {1}'.format(job, settings['source']))                
                logger.debug('Job\'s "{0}" destination : {1}'.format(job, settings['destination']))
                try:
                    self.jobs[job].update({'defaults':settings['defaults']})        
                    logger.debug('Job\'s "{0}" defaults set : TRUE'.format(job))            
                except KeyError:
                    self.jobs[job].update({'defaults':False})                    
                    logger.debug('Job\'s "{0}" defaults set : FALSE'.format(job))                     
                for key in self.attributes:
                    try:
                        self.jobs[job].update({key:settings[key]})
                        logger.debug('Job\'s "{0}" attribute "{1}" set to : {2}'.format(job, key, settings[key])) 
                    except KeyError:
                        logger.debug('Job\'s "{0}" attribute "{1}" in not set.'.format(job, key)) 
                        pass
            self.enabled = self.__configuration['options']['enabled']  
            if self.enabled: 
                logger.debug('Job\'s "{0}" option "enabled" set to : TRUE'.format(job))
            else:
                logger.debug('Job\'s "{0}" option "enabled" set to : FALSE'.format(job))                   
            self.eject   = self.__configuration['options']['eject']                               
            if self.eject: 
                logger.debug('Job\'s "{0}" option "eject" set to : TRUE'.format(job))
            else:
                logger.debug('Job\'s "{0}" option "eject" set to : FALSE'.format(job))                    
            self.warning = self.__configuration['options']['percentageWarning']
            if self.warning: 
                logger.debug('Job\'s "{0}" option "Percentage warning" set to : {1}'.format(job, self.warning))
            else:
                logger.debug('Job\'s "{0}" option "Percentage warning" set to : DEFAULT(90)'.format(job))                   
            if self.guiAble:        
                self.gui = self.__configuration['options']['gui']               
            else:
                self.gui = False
            logger.debug('Job\'s "{0}" option "gui" set to : {1}'.format(job, str(self.gui).upper()))                        
            self.stdout  = self.__configuration['report']['stdout']
            self.log     = self.__configuration['report']['log']                                
            self.summary = self.__configuration['report']['summary']            
        except:
            logger.error('Backup configuration file not found or something wrong with the syntax. Quiting...')
            logger.error('Traceback : ', exc_info=True)
            raise SystemExit            
    
    def __emailReport(self, text, logFile, stdoutFile, summaryFile):
        attach = []
        hostname = socket.gethostname()
        logger.debug('Hostname set to : {0}'.format(hostname))
        now = time.asctime( time.localtime(time.time())).replace(':','-')
        logger.debug('Now time set to : {0}'.format(now))
        if self.log:
            log = os.path.join(self.__cwd, hostname + ' ' + now + ' full report.pdf')
            logger.debug('Created log : {0}'.format(log))            
            log2pdf = PyText2Pdf(ofile=log, ifilename=logFile.name, buffers=False)
            logger.debug('Converting log : {0} to pdf'.format(log))
            log2pdf.convert()
            logger.debug('Appending log : {0} to mail attachment.'.format(log))
            attach.append(log)
        if self.stdout:
            stdout = os.path.join(self.__cwd, hostname + ' ' + now + ' stdout printout.pdf')
            logger.debug('Created stdout log : {0}'.format(stdout))                        
            stdout2pdf = PyText2Pdf(ofile=stdout, ifilename=stdoutFile.name, buffers=False)
            logger.debug('Converting stdout log : {0} to pdf'.format(stdout))            
            stdout2pdf.convert()   
            logger.debug('Appending stdout log : {0} to mail attachment.'.format(stdout))            
            attach.append(stdout)
        if self.summary:
            summary = os.path.join(self.__cwd, hostname + ' ' + now + ' summary.pdf')  
            logger.debug('Created summary log : {0}'.format(summary))                                              
            summary2pdf = PyText2Pdf(ofile=summary, ifilename=summaryFile.name, buffers=False)
            logger.debug('Converting summary log : {0} to pdf'.format(summary))                        
            summary2pdf.convert()           
            logger.debug('Appending summary log : {0} to mail attachment.'.format(summary))                        
            attach.append(summary)                
        try:
            logger.debug('Sending email report with attachments.')      
            self.message.send( self.sender, \
                               self.recipients, \
                               self.subject, \
                               text, \
                               attachments=','.join(attach))    
            logger.debug('Done sending email report.')
        except socket.error:
            logger.warning('Sending of mail failed!')
            logger.warning('Traceback : ', exc_info=True)
            pass
        if self.log:    
            logger.debug('Removing log : {0}'.format(log))                          
            os.unlink(log)
            logger.debug('Done removing log : {0}'.format(log))
        if self.stdout: 
            logger.debug('Removing stdout log : {0}'.format(stdout))
            os.unlink(stdout)
            logger.debug('Done removing stdout log : {0}'.format(stdout))
        if self.summary:            
            logger.debug('Removing summary log : {0}'.format(summary))
            os.unlink(summary)
            logger.debug('Done removing log : {0}'.format(summary))
        logFile.close()            
        stdoutFile.close()            
        summaryFile.close()
        logger.debug('Removing temporary log file: {0}'.format(logFile.name))
        os.unlink(logFile.name)            
        logger.debug('Done removing temporary log file: {0}'.format(logFile.name))
        logger.debug('Removing temporary stdout log file: {0}'.format(stdoutFile.name))
        os.unlink(stdoutFile.name)                        
        logger.debug('Done removing temporary stdout log file: {0}'.format(stdoutFile.name))
        logger.debug('Removing temporary summary log file: {0}'.format(summaryFile.name))
        os.unlink(summaryFile.name)            
        logger.debug('Done removing temporary log file: {0}'.format(summaryFile.name))
            
    def __jobsRun(self):
        text = ''
        logFile     = tempfile.NamedTemporaryFile(delete=False) 
        logger.debug('Created temporary log file: {0}'.format(logFile.name))             
        stdoutFile  = tempfile.NamedTemporaryFile(delete=False)     
        logger.debug('Created temporary stdout log file: {0}'.format(stdoutFile.name))         
        summaryFile = tempfile.NamedTemporaryFile(delete=False) 
        logger.debug('Created temporary summary log file: {0}'.format(summaryFile.name))           
        for job, settings in self.jobs.iteritems():
            logger.debug('Configuring sync job "{0}"'.format(job))
            sync = Sync()
            sync.source      = settings['source']
            sync.destination = os.path.join(self.drive.mountedPath, settings['destination'])
            if settings['defaults']:
                logger.debug('Setting job default options.')
                sync.options.defaults()            
                logger.debug('Done setting job default options.')
            for key in self.attributes:
                try:
                    if not settings[key]:
                        logger.debug('Removing option "{0}"'.format(key))                              
                        delattr(sync.options, key)
                    else:
                        logger.debug('Settings job option "{0}" to "{1}".'.format(key, settings[key]))
                        setattr(sync.options, key, settings[key])
                except KeyError:
                    logger.debug('"{0}" is not set in configuration.'.format(key))
                    pass     

            partLogFile = tempfile.NamedTemporaryFile(delete=False) 
            logger.debug('Created rsync log file {0}'.format(partLogFile.name)) 
            setattr(sync.options, 'logFile', partLogFile.name)
            logger.debug('Running sync job "{0}"'.format(job))
            sync.run()
            logger.debug('Done running sync job "{0}"'.format(job))            
            text += '{0} done\n'.format(job)    
            with open(logFile.name, 'a') as ifile:
                logger.debug('Writing log file "{0}" with job\'s "{1}" details'.format(logFile.name, job)) 
                ifile.write(open(partLogFile.name).read())
            with open(stdoutFile.name, 'a') as olfile:
                logger.debug('Writing stdout log file "{0}" with job\'s "{1}" details'.format(stdoutFile.name, job))             
                olfile.write('rsync stdout output :\n\n {0}'.format(sync.output))
                if sync.error:
                    logger.warning('Rsync stderr output: \n\n{0}'.format(sync.error)) 
                    olfile.write('rsync stderr output :\n\n {0}'.format(sync.error))
            with open(summaryFile.name, 'a') as sifile:
                logger.debug('Writing summary log file "{0}" with job\'s "{1}" details'.format(summaryFile.name, job))  
                sifile.write(job + '\n\n')                        
                sifile.write(tail(open(partLogFile.name), 13) + '\n\n')  
                if sys.platform == 'linux2':
                    logger.debug('Appending to summary log file "{0}" drive\'s partition usage.'.format(summaryFile.name))  
                    sifile.write(checkPartitionUsage(self.drive.mountedPath ,self.warning))
            logger.debug('Removing rsync log file {0}'.format(partLogFile.name)) 
            partLogFile.close()
            os.unlink(partLogFile.name)
            logger.debug('Done removing rsync log file {0}'.format(partLogFile.name)) 
        return text, logFile, stdoutFile, summaryFile
    
    def run(self):
        text = logFile = stdoutFile = summaryFile = ''
        if not self.enabled:
            logger.debug('Job is disabled in configuration. Attaching partition {0}.'.format(self.drive.partition))
            logger.info('Job is disabled in configuration. Attaching partition {0}.'.format(self.drive.partition))            
            out, error = self.drive.attach()
            if error:
                logger.error('Error attaching partition {0} : {1}.'.format(self.drive.partition, error))
            raise SystemExit
        else:
            logger.debug('Mounting partition {0}.'.format(self.drive.partition))
            logger.info('Mounting partition {0}.'.format(self.drive.partition))            
            out, error = self.drive.mount()
            if error:
                logger.error('Error mounting partition {0} : {1}.'.format(self.drive.partition, error))
                raise SystemExit
        if self.gui:
            logger.debug('Notifying for the job start')
            self.__notify.message('Pyrsync Backup','Drive inserted, starting job(s)...')
        else:
            logger.debug('Gui is disabled in the settings. No notification will be shown.')
        try:
            logger.debug('Begging running backup jobs.')
            text, logFile, stdoutFile, summaryFile = self.__jobsRun()   
        except Exception:
            logger.error('There was error in the jobs. Cleaning up...')
            logger.error('Traceback : ', exc_info=True)
        finally:    
            logger.debug('Unmounting partition {0}.'.format(self.drive.partition))
            logger.info('Unmounting partition {0}.'.format(self.drive.partition))            
            out, error = self.drive.umount()
            if error:
                logger.error('Error unmounting partition {0} : {1}.'.format(self.drive.partition, error))
        if self.email:
            logger.debug('Sending email')
            logger.info('Sending email')            
            result = self.__emailReport(text, logFile, stdoutFile, summaryFile)
            logger.debug('Email sending result is : {0}.'.format(result))
            if result:
                logger.warning('Email not sent successfully!')
            else:
                logger.debug('Email sent succesfully.')
        if self.eject:
            logger.debug('Ejecting drive.')
            logger.info('Ejecting drive.')            
            message = 'Job(s) ended, ejecting drive...'
            out, error = self.drive.detach()
            logger.debug('Done ejecting drive.')
        else:
            logger.debug('Reattaching drive.')
            logger.info('Reattaching drive.')            
            message = 'Job(s) ended, attaching drive...'
            out, error = self.drive.attach()
            logger.debug('Done reattaching drive.')
        if self.gui:
            logger.debug('Notifying for the job end.')
            self.__notify.message('Pyrsync Backup', message)   
        else:
            logger.debug('Gui is disabled in the settings. No notification will be shown.')            
        if error:
            logger.warning('Error with ejecting or reattaching : {0}'.format(error))
        logger.info('All jobs completed! Finishing...')         


                
if __name__=='__main__':
    try:
        serial      = sys.argv[1]
        device      = sys.argv[2]
        partition   = sys.argv[3]        
    except IndexError:
        logger.error('Not enough arguments. Exiting...')
        raise SystemExit
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)        
    try: 
        logger.debug('Forking once')
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            logger.debug('Exiting first parent')
            raise SystemExit(0)
    except OSError, e: 
        logger.error('Fork #1 failed')
        logger.error('Traceback : ', exc_info=True)
        raise SystemExit(1)
    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 
    # do second fork
    try: 
        logger.debug('Forking twice')    
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            logger.debug('Exiting second parent')            
            logger.debug('Daemon PID : {0}'.format(pid))
            raise SystemExit(0)
    except OSError, e: 
        logger.error('Fork #2 failed')
        logger.error('Traceback : ', exc_info=True)
        raise SystemExit(1)
    
    backUp = BackUp()
    backUp.setDrive(device, partition)
    backUp.enableEmail()
    backUp.setJobDetails(serial)    
    backUp.run()
