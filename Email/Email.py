#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# File: Email.py
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
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA
#
__author__    = 'Ioannis Avraam <iavraam@eteth.gr>, Costas Tyfoxylos <costas.tyf@gmail.com>'
__docformat__ = 'plaintext'
__date__      = '28/04/2011'

from email.mime.application import MIMEApplication
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import smtplib, os

class Email(object):
    def __init__(self, smtp):
        self.smtp = smtp
    def send(self, sender, recipients, subject, text, attachments=None):
        To =[]
        for recipient in recipients.split(','):
            To.append(recipient)
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = COMMASPACE.join(To)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject.decode('utf-8')
        msg.preamble = 'Multipart massage.\n'
        part = MIMEText(text, 'plain', 'UTF-8')
        msg.attach(part)
        # This is the binary part(The Attachment):
        if attachments:
            for attachment in attachments.split(','):            
                part = MIMEApplication(open(attachment,"rb").read())
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
                msg.attach(part)        
        smtp = smtplib.SMTP(self.smtp)
        smtp.sendmail(sender, To, msg.as_string() )
        smtp.close()

if __name__ == '__main__':
    message=Email(smtp='smtp.provider.com')
    message.send(   sender      = 'sender@server.com',\
                    recipients  = 'recipient@server.com',\
                    subject     = 'test subject και λίγα utf 8 ελληνικά',\
                    text        = 'this is the first test και ειναι μια χαρα')
#                    pdf         = '/path/to/pdf/file.pdf,/path/to/other/pdf/file2.pdf')
