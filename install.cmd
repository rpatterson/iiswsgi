set IIS_BIN=%ProgramFiles%\IIS Express
"%IIS_BIN%\appcmd.exe" set config -section:system.webServer/fastCgi /+"[fullPath='%SystemDrive%\Python27\python.exe',arguments='-u %SystemDrive%\Python27\Scripts\iiswsgi-script.py',maxInstances='1',monitorChangesTo='C:\Python27\Scripts\iiswsgi-script.py']" /commit:apphost
