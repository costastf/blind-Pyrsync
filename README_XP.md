blind-Pyrsync
=============


I don't use windows, this is just for support to some old installs of friends that need it. The program requires python 2.7 as explained in the main help file, python wmi and pywin32 installed. 
For setting things up after having installed the requirements just edit serviceWin32.py file near the top for the needed globals :

```
CWD = r'C:\blind-Pyrsync\'

PYTHONPATH = r'C:\Python27\python.exe'
```

They are pretty self explanatory I think.

After setting the variables to ones valid settings the service should be installed and started. 

Just run on a prompt > python serviceWin32.py install

If no error is given, > python serviceWin32.py start

if everything went well and no error is given one should go to services, start > run > services.msc and under services find "Device Event Handler" and change its setting to start automatically. Also to get notifications to the desktop under the service's properties on the "Log On" tab the setting "Allow service to interact with Desktop" should be checked. If the name "Device Event Handler" doesn't suit it can be changed in the serviceWin32.py file. I left it as was given by the service's creator, Tim Golden.

The paths in the json for rsync MUST BE doubly escaped. So "c:\temp" should be "c:\\\temp". All paths (source, destination) must me doubly escaped. 

That is more or less all is needed to setup the service. pyrsync needs a statically compiled rsync for windows under cygwin inside the pyrsync folder. Find it on line. Have fun!
