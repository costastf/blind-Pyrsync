#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: utils.py
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
__date__      = '01/10/2013'


from subprocess import Popen, PIPE

def tail( f, window=20 ):
    ''' from http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail'''
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (bytes - BUFSIZ > 0):
            # Seek back one whole BUFSIZ
            f.seek(block*BUFSIZ, 2)
            # read BUFFER
            data.append(f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.append(f.read(bytes))
        linesFound = data[-1].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return '\n'.join(''.join(data).splitlines()[-window:])

def checkPartitionUsage(partition, threshold=90):
    df = Popen(['df','-h'],stdout=PIPE, stderr=PIPE).stdout.read()
    percentage = ''
    for line in df.splitlines():
        if partition in line:
            percentage = int(line.split()[-2].replace('%',''))
            break
    if partition.startswith('/tmp'):
        partition = 'External HDD'
    if not percentage:
        text = 'Partition {0} not found'.format(partition)
    elif percentage < threshold:
        text = 'Partition {0} usage OK'.format(partition)
    elif percentage >= threshold:
        text = 'Warning! Partition usage has exceeded {0}% and is {1}%'.format(threshold, percentage)
    return text 

def checkSwapUsage(threshold=40):
    free = Popen(['free'],stdout=PIPE, stderr=PIPE).stdout.read()        
    for line in free.splitlines():
        if line.startswith('Swap:'):
            total = int(line.split()[1])
            used = int(line.split()[2])            
            free = int(line.split()[3])            
            break
    percentage = 100 * used / total        
    if percentage < threshold:
        text = 'Swap usage OK'
    elif percentage >= threshold:
        text = 'Warning! Swap usage has exceeded {0}% and is {1}%'.format(threshold, percentage)        
    return text

