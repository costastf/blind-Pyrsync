#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: pyrsync.py
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
# Place, Suite 330, Boston, MA 02111-1307 USA
#
__author__ = 'Costas Tyfoxylos <costas.tyf@gmail.com>'
__docformat__ = 'plaintext'
__date__ = '21/03/2012'

from subprocess import Popen, PIPE
import subprocess
import sys, os
import logging



class Sync(object):
    class Options(object):
        def __init__(self, options):
            for key,value in options.items():
                self.__dict__[key] = value  
        def defaults(self):
            options = ['humanReadable', 'verbose', 'links', 'recursive', \
                       'permissions', 'executability', 'owner', 'group', \
                       'times', 'delete', 'ignoreErrors', 'force', \
                       'stats']   
            if sys.platform == 'linux2':
                options.append('extendedAttributes')
            for option in options:
                self.__dict__[option] = True
            
 
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Initializing sync object')
        self.output = ''
        self.error = ''
        self.__options = { 'humanReadable'     :'--human-readable',    # output numbers in a human-readable format
                           'verbose'           :'--verbose',           # increase verbosity
                           'recursive'         :'--recursive',         # recurse into directories
                           'links'             :'--links',             # copy symlinks as symlinks
                           'permissions'       :'--perms',             # preserve permissions
                           'executability'     :'--executability',     # preserve executability
                           'extendedAttributes':'--xattrs',            # preserve extended attributes
                           'owner'             :'--owner',             # preserve owner (super-user only)
                           'group'             :'--group',             # preserve group
                           'times'             :'--times',             # preserve modification times        
                           'delete'            :'--delete',            # delete extraneous files from dest dirs
                           'ignoreErrors'      :'--ignore-errors',     # delete even if there are I/O errors
                           'force'             :'--force',             # force deletion of dirs even if not empty
                           'exclude'           :'--exclude=',          # exclude files matching PATTERN
                           'include'           :'--include=',          # don't exclude files matching PATTERN
                           'logFile'           :'--log-file=',         # log what we're doing to the specified FILE 
                           'stats'             :'--stats',             # give some file-transfer stats
                           'archive'           :'--archive'            # archive mode; equals -rlptgoD (no -H,-A,-X)
                       }
        self.errorCodes = { '1' : 'Syntax or usage error' , 
                            '2' : 'Protocol incompatibility' ,
                            '3' : 'Errors selecting input/output files, dirs' ,
                            '4' : 'Requested action not supported: an attempt was made to manipulate 64-bit files on a platform that cannot support them; or an option was specified that is supported by the client and not by the server.' ,
                    	    '5' : 'Error starting client-server protocol' ,
                    	    '10': 'Error in socket I/O' ,
                    	    '11': 'Error in file I/O' ,
                    	    '12': 'Error in rsync protocol data stream' ,
                    	    '13': 'Errors with program diagnostics' ,
                    	    '14': 'Error in IPC code' ,
                    	    '20': 'Received SIGUSR1 or SIGINT' ,
                    	    '21': 'Some error returned by waitpid()' ,
                    	    '22': 'Error allocating core memory buffers' ,
                    	    '23': 'Partial transfer due to error' ,
                    	    '24': 'Partial transfer due to vanished source files' ,
                    	    '30': 'Timeout in data send/receive'
                		}
        self.options = self.Options(self.__options)
        self.options.humanReadable = False
        self.options.verbose = False
        self.options.recursive = False
        self.options.links = False
        self.options.permissions = False
        self.options.executability = False
        self.options.archive = False
        self.options.extendedAttributes = False
        self.options.owner = False
        self.options.group = False
        self.options.times = False
        self.options.delete = False
        self.options.ignoreErrors = False
        self.options.force = False
        self.options.stats = False
        self.options.exclude = None
        self.options.include = None
        self.options.logFile = None
        self.source = None
        self.destination = None
        self.binary = self.__getBinaryPath()
        self.logger.debug('Done initializing sync object')
        
    def __getBinaryPath(self):
        """Gets the software name and returns the path of the binary."""
        binary = ''
        if sys.platform == 'linux2':
            executable = 'rsync'
            binary = Popen(['which', executable], stdout=PIPE).stdout.read().strip()
        elif sys.platform == 'win32':
            executable = 'rsync.exe'
            if executable in os.listdir('pyrsync'):
                binary = os.path.join(os.getcwd(),'pyrsync', executable)              
            else:
                for path in os.environ['PATH'].split(os.pathsep):
                    if os.path.isfile(os.path.join(path, executable)):
                        binary = os.path.join(path, executable)
                        break
        if binary:
            self.logger.debug('Found rsync binary under : {0}'.format(binary))
            return binary
        else:
            self.logger.error('Could not find rsync binary. Probably software not installed.')
            raise SystemExit        

    def __normalizePath(self, path):
        if sys.platform == 'win32':
            self.logger.debug('Normalizing path for windows.')
            rsyncPath = path.replace(':', '').split(os.sep)
            rsyncPath.reverse()
            rsyncPath.append('/cygdrive')
            rsyncPath.reverse()
            path = '/'.join(rsyncPath)
            self.logger.debug('Normalized path as : {0}.'.format(path))
        return path
        
    def __appendOptions(self, command):
        for key, value in vars(self.options).items():
            if value:
                try:
                    if key == 'exclude':
                        for exclude in value.split():
                            self.logger.debug('Appending exclude option with argument : {0}'.format(exclude))
                            command.append(self.__options[key] + exclude)
                    elif key == 'include':
                        for include in value.split():
                            self.logger.debug('Appending include option with argument : {0}'.format(include))                        
                            command.append(self.__options[key] + include)
                    elif key == 'logFile':
                        command.append(self.__options[key] + self.__normalizePath(value))
                    else:
                        self.logger.debug('Appending option {0} with argument : {0}'.format(key, self.__options[key]))
                        command.append(self.__options[key])
                except KeyError:
                    self.logger.warning('Unknown or not supported option "{0}". Supported options : {1}'.format(key, ' '.join(self.__options.keys())))
                    pass
        self.logger.debug('Appending source option with argument : {0}'.format(self.source))            
        command.append(self.__normalizePath(self.source))
        self.logger.debug('Appending destination option with argument : {0}'.format(self.destination))        
        command.append(self.__normalizePath(self.destination))
        self.logger.debug('Final rsync options are : {0}'.format(command))        
        return command
                    
    def run(self):
        if self.source and self.destination:
            command = [self.binary]
            command = self.__appendOptions(command)
            self.logger.debug('Final rsync command is : {0}'.format(command))   
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = Popen(command, startupinfo=startupinfo, stdout=PIPE, stderr=PIPE)
            else:
                process = Popen(command, stdout=PIPE, stderr=PIPE)            
            self.output, self.error = process.communicate()
            returnCode = process.returncode
            if str(returnCode) != '0':
                try:
                    returnCode = self.errorCodes[str(returnCode)]
                    self.logger.warning('Got error code : {0}'.format(returnCode))
                except IndexError:
                    self.logger.warning('Error not in error code list.')                
            return returnCode             
        else:
            self.logger.error('Please set source and destination.')     
            raise Exception('Source and destination are not set.')           

if __name__ == '__main__':
    backup = Sync()
    backup.source           = r'c:\Documents And Settings\user\Desktop'
    backup.destination      = r'x:\backup' 
    backup.options.exclude  = '*.mp3 *.jpg'
    backup.options.links    = False
    backup.run()
