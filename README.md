blind-Pyrsync
=============

Blind backup solution (setup, plug drive, get notice, unplug drive) based on an rsync python wrapper. 
Tested with Ubuntu 10.4, Ubuntu 12.4 Desktop, Ubuntu 13.10 Desktop and Debian 6 Server.

The idea behind this srcipt is that one creates one or more recipes for a backup in plain json under the conf directory
and the script calls and executes the job depending on the drive inserted. Under ubuntu / debian one would create a udev rule under /etc/udev/rules.d/99-usb-drive.rules or any other name that suits. The rule should consist of one of the following : 
```
##### UBUNTU 12.4 Desktop And later Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="", ENV{UDISKS_IGNORE}="1", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P %r/%k"
```
```
##### UBUNTU 10.4 Desktop Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="", ENV{UDISKS_PRESENTATION_HIDE}="1", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P %r/%k" 
```
```
##### Debian Server Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P %r/%k"
```
One should fill out ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="" variables with their own details. The details can be attained with :
```udevadm info -a -p $(udevadm info -q path -n /dev/!!DEVICE!!) | egrep -i "ATTRS{serial}|ATTRS{idVendor}|ATTRS{idProduct}" -m 3```

Also under the "add" rule one should place a "change" rule for that device like :

```
####### Change rule
ACTION=="change", SUBSYSTEM=="usb",  ATTRS{serial}==""
```
This rule takes care the showing of the device to the user in case of desktop systems where after the sync one would want the drive to appear as if inserted to check the backup or use the drive for other stuff. 

The ATTRS{idVendor}=="" and ATTRS{idProduct}=="" can of course be ommited. They are used just for the highly unlikely case were there are two drives with the same serial. 

There can be as many rule couples as drives one would want to use for backup.

There is a known bug with some udev versions that doesn't let udev traverse the device tree for $attr although in the documentation it says it does. A handy work around for that is to create an ENV with the value that we want to pass and use that instead of the $attr. In the case of the serial for example the rule could be changed from 

```
##### Debian Server Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="", RUN+="/path/to/blind-Pyrsync/backup.py $attr{serial} %r/%P %r/%k"
```
to 
```
##### Debian Server Rule
ACTION=="add", KERNEL=="sd?1", ATTRS{idVendor}=="", ATTRS{idProduct}=="", ATTRS{serial}=="", ENV{serial}="SERIAL_NUMBER_HERE" RUN+="/path/to/blind-Pyrsync/backup.py $env{serial} %r/%P %r/%k"
```

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

The script doesn't support smtp authentication yet.(It will propably do sometime.) It is assumed that one can send email through the provider's smtp service. The recipient or recipients(comma delimited multiple mails: "test@gmail.com,test2@gmail.com") will receive an email with the report of the finished jobs.

Finally under conf directory we create the backup jobs as json files. The name should be the drive's serial number with the json extension. Example : 116AC2101219.json

It's contents should be in the form of :
```
{ "jobs" :
    { "Backup Job Name 1" :
        { "source"      : "/absolute/path/to/the/directory/to/be/rsynced",
          "destination" : "relative/path/to/the/destination/drive",
          "defaults"    : true
        },
      "Variable Backup Job Name 2" :
        { "source"      : "/absolute/path/to/the/directory/to/be/rsynced",
          "destination" : "relative/path/to/the/destination/drive",
          "defaults"    : true,
          "delete"      : false
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
    },
    
  "options" :
    { "enabled" : true,
      "eject"   : true,
      "percentageWarning" : 90,
      "gui"     : true
    },
    
  "report" :
  { "stdout"    : false,
    "log"       : false,
    "summary"   : true
  }
}
```

Please note that the source should be the absolute path of the rsynced directory BUT the destination must be the relative path under the drive's filesystem. So, if one where to backup the /etc directory in a directory with the name "etc" in the drive the settings should be according to the above final example. The above example would produce /etc/etc/miscfiles.... in the root of the destination file. If one wanted the directory name to be parent name and all the files to be under it then the correct setting would be:

```
          "source"      : "/etc",
          "destination" : ""
```

It would be good at this point to check the json files through a json validator. Just google for one on line and check the settings.

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
one can easily add more, under the pyrsync.py wrapper. The "defaults" option when set, sets the following options to true (because of my needs):
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
Of course all options can be overriden. So one could set "defaults" : true which would set all the above to true and then set "delete" : false overiding the delete option set before.

One can remove any of the supported settings by setting the variable to False ("delete": false) in the recipe, or set new ones. The logFile is set automatically by the main script when it is run, so even if it is set in the json configuration file the variable will be overriden.

The options are "enabled" for the rsync to run, one could set it to false so the backup would not run and he/she could have access to the drive normaly.
"eject" is for automatic detachment of the drive after the rsync. Of course if the "enabled" is set to false the "eject" is ignored. If eject is not set then the drive gets automounted just like it would without the backup job. This is useful for desktop machines with gui where the user would probably want to use or verify the backup in the drive. The "percentageWarning" is the drive's percentage usage above which one would get a warning in the end of the summary file. Something like 90 is a reasonable value. But then again, that is all relevant.. The last option, "gui" if set sends two notifications to the GUI, one for the start of the backup and one for the end of the back and the status of the device after that. (Attached or ejected, according to the setting of "eject") The "gui" in linux depends on the pynotify library. So that has to be installed or the notifications will not work, sillently of course.

The reporting has three possible outputs. "stdout" will send the output of the rsync command, "log" will send the rsync logfile and "summary" will send a summary of all the jobs. They can be set in any combination. WARNING! The stdout and log can be quite large in a big job. Please make sure that the files can fit through your smtp.

These default variables are needed and the script will fail without them in the configuration file...

******************    TROUBLESHOOTING   ******************

rsync should be installed (DOH!!)

mount and umount should be under /bin/. If not, change the paths accordingly in Drive class. 

One should have udisks installed for the eject to work. In ubuntu desktop it is installed by befault but in debian server it is not so, make sure to install it and check that it is under /usr/bin.

One should check first that the drive is mountable by the system (filesystem supported, read - write). 
If the drive's filesystem is NTFS make sure that the mount command mounts the drive with ntfs-3g so it can write to it.

If "gui" is set the pynotify library should be installed in linux.

If the drive is FAT then the script will spit errors if one tries to move file attributes, since FAT does not support Linux file attributes. This is rsync's errors, not the script's.

Before setting the whole thing up, one should check that the udev rule is working by making it call a simple bash script that writes to a file the arguments it gets. Example :

```
#!/usr/bin/env bash

echo $1 >> /tmp/udevCheck
echo $2 >> /tmp/udevCheck
echo $3 >> /tmp/udevCheck
```

name the file test.sh make it executable and put it in your udev rule in RUN command : 
    RUN+="/path/to/test.sh $attr{serial} %r/%P %r/%k"
after you have pluged the drive there should be a file under /tmp named udevCheck with contents the drive's serial number and it's device name under /dev. If that doesn't happen then there is a problem with the rule and should be troubleshooted as a udev problem. Google it...

If the rule is working as expected one could call the script manually to check that everything is working before settings it up to work blindly. Plug the drive in and check the device name that it is given under /dev (ie: /dev/sdb1)
  
Call the backup script as root /path/to/scipt/backup.py DRIVESERIAL DEVICENAMEUNDERDEV PARTITIONNAMEUNDERDEV and everything should run OK. If not, troubleshoot according to the error messages given. If everything works out as expected you are good to go.

Added heavy logging for debugging purposes. Under conf directory there is logging.json file with options for logging. I have enabled debug level as default. One should only change to the desired logging level in the json file. The logging is done on stdout and on a file called backup.log. If one would want that back up file to be in a specific directory one should change the path in the logging.json file. If the backup script is run by udev as it is intended the default location of the backup.log is the root of the filesystem.  With a simple tail -f on that file one could figure out any trouble with the back up. Have fun!
