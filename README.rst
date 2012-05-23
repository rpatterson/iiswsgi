=======
iisfcgi
=======

The `iisfcgi` module implements a FastCGI to WSGI gateway that is
compatible with IIS's variation of the FastCGI protocol.  In
particular, it supports using STDIN_FILENO opened twice, once each
approximating the recv and send end of a socket as is specified in
FastCGI.

Quick Start
===========

Use IIS's `AppCmd.exe
<http://learn.iis.net/page.aspx/114/getting-started-with-appcmdexe/>`_
to install a new FastCGI application.  You can find it at
``%ProgramFiles%\IIS Express\appcmd.exe`` for WebMatrix/IIS Express or
``%systemroot%\system32\inetsrv\AppCmd.exe`` for IIS.  Note that you
need to replace ``%PasteDeployINIFile%`` with the full path to a
`Paste Deploy INI configuration file
<http://pythonpaste.org/deploy/index.html?highlight=loadapp#introduction>`_
that defines the WSGI app and ``%WSGIAppName%`` with the name of your
app as IIS will see it::

    > appcmd.exe set config -section:system.webServer/fastCgi /+"[fullPath='%SystemDrive%\Python27\Scripts\iisfcgi.exe',arguments='-c %PasteDeployINIFile%',maxInstances='%NUMBER_OF_PROCESSORS%',monitorChangesTo='%PasteDeployINIFile%']" /commit:apphost
    > appcmd.exe set config -section:system.webServer/fastCgi /+"[fullPath='%SystemDrive%\Python27\Scripts\iisfcgi.exe'].environmentVariables.[name='PYTHONUNBUFFERED',value='1']" /commit:apphost
    > appcmd.exe set config -section:system.webServer/handlers
    /+"[name='%WSGIAppName%',path='*',verb='*',modules='FastCgiModule',scriptProcessor='%SystemDrive%\Python27\Scripts\iisfcgi.exe|-c
    %PasteDeployINIFile%']" /commit:apphost

See the `IIS FastCGI Reference
<http://www.iis.net/ConfigReference/system.webServer/fastCgi>`_ for
more details on how to configure IIS for FastCGI.
