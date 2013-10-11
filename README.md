blind-Pyrsync
=============

Blind backup solution (setup, plug drive, get notice, unplug drive) based on an rsync wrapper.

The idea behind this srcipt is that one creates one or more recipes for a backup in plain json under the conf directory
and the script calls and executes the job depending on the drive inserted. Under ubuntu / debian one would create a udev rule under /etc/udev/rules.d/99-usb-drive.rules or any other name that suits. The rule should consist of one of the following : 

##### UBUNTU 12.4 Desktop And later Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="",SYMLINK+="BackupHD", ENV{UDISKS_IGNORE}="1", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P"

##### UBUNTU 10.4 Desktop Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="",SYMLINK+="BackupHD", ENV{UDISKS_PRESENTATION_HIDE}="1", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P"

##### Debian Server Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="",SYMLINK+="BackupHD", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P"

One should fill out ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="" variables with their own details. The details can be attained with :
udevadm info -a -p $(udevadm info -q path -n /dev/!!DEVICE!!) | egrep -i "ATTRS{serial}|ATTRS{idVendor}|ATTRS{idProduct}" -m 3

After the udev rule is set a file named email.json should be created under conf directory with the following structure

```
{ "settings" :
    {   "smtp"        : "", 
        "sender"      : "",
        "recipients"  : "",      
        "subject"     : ""       
    }
}
```

The script doesn't support smtp authentication. It is assumed that one can send email through the provider's smtp service. The recipient or recipients(comma delimited multiple mails: "test@gmail.com,test2@gmail.com") will receive an email with the full rsync log as attachment and a summary with only the basic details of the finished jobs.

Finally under conf directory we create the backup jobs as json files. The name should be the drive's serial number with the json extension. Example : 116AC2101219.json

It's contents should be in the form of :
```
{ "Backup Job Name 1" :
    { "source"      : "/absolute/path/to/the/directory/to/be/rsynced",
      "destination" : "relative/path/to/the/destination/drive"
    },
  "Variable Backup Job Name 2" :
    { "source"      : "/absolute/path/to/the/directory/to/be/rsynced",
      "destination" : "relative/path/to/the/destination/drive",
      "delete"      : "False"   
    },
  "Job whatever" :
    { "source"      : "/absolute/path/to/the/directory/to/be/rsynced",
      "destination" : "bin",
      "exclude"     : "*.sh *.mp3"        
    },
  "ETC Backup" :
    { "source"      : "/etc",
      "destination" : "etc"
    }        
}
```

Please note that the source should be the absolute path of the rsynced directory BUT the destination must be the relative path under the drives filesystem. So, if one where to backup the /etc directory in a directory with the name "etc" in the drive the settings should be according to the above final example. 
The rsync options supported are :
```
     'humanReadable'     :'--human-readable',    # output numbers in a human-readable format
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
```
one can easyly add more, under the pyrsync.py wrapper. The options that are set by default (because of my needs) are :
```
      humanReadable = True
      verbose = True
      recursive = True
      links = True
      permissions = True
      executability = True
      extendedAttributes = True
      owner = True
      group = True
      times = True
      delete = True
      ignoreErrors = True
      force = True
      stats = True        
```
One can remove any of the supported settings by setting the variable to False ("delete": "False" ) in the recipe, or set new ones. The logFile is set automatically by the main script when it is run, so even if it is set in the json configuration file  the variable will be overriden.

******************    TROUBLESHOOTING   ******************

rsync should be installed (DOH!!)

mount and umount should be under /bin/. If not, change the paths accordingly in Drive class. 

One should have udisks installed. In ubuntu desktop it is installed by befault but in debian server it is not so, make sure to install it and check that it is under /usr/bin.

One should check first that the drive is mountable by the system (filesystem supported, read - write). 
If the drive's filesystem is NTFS make sure that the mount command mounts the drive with ntfs-3g so it can write to it.

If the drive is FAT then the script will spit errors if one tries to move file attributes, since FAT does not support Linux file attributes. This is rsync's errors, not the scripts.

Before setting the whole thing up, one should check that the udev rule is working by making it call a simple bash script that writes to a file the arguments it gets. Example :

```
#!/usr/bin/env bash

echo $1 >> /tmp/udevCheck
echo $2 >> /tmp/udevCheck
```

name the file test.sh make it executable and put it in your udev rule in RUN command : 
    RUN+="/path/to/test.sh $attr{serial} %r/%P"
after you have pluged the drive there should be a file under /tmp named udevCheck with contents the drive's serial number and it's device name under /dev. If that doesn't happen then there is a problem with the rule and should be troubleshooted as a udev problem. Google it...

If the rule is working as expected one could call the script manually to check that everything is working before settings it up to work blindly. Plug the drive in and check the device name that it is given under /dev (ie: /dev/sdb1)
Edit the backup.py script in its main and change 
```
    backUp.setJobDetails(serial)    
    to
    backUp.setJobDetails(serial, partition='/dev/sdb1')        
```    
Call the backup script as root line /path/to/scipt/backup.py DRIVESERIAL DEVICENAMEUNDERDEV and everything should run OK. If not, troubleshoot according to the error messages given. If everything works out as expected revert the changes to the setJobDetails call since the udev rule is set to create a symlink under dev with name BackupHD and that is defaulted in the script so the partition argument is not needed when combined with udev.
