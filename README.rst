==================================================
iiswsgi
==================================================
Serving Python WSGI applications natively from IIS
==================================================

The ``iiswsgi`` module implements a FastCGI to WSGI gateway that is
compatible with IIS's variation of the FastCGI protocol.  It also
provides distutils commands for building, distributing and installing
`Microsoft Web Deploy`_ (MSDeploy) packages through the `Web Platform
Installer`_ (WebPI).

``iiswsgi.exe``

    This console script is the FastCGI to WSGI gateway.  IIS invokes
    this script to start a Python WSGI app as a FastCGI process.

``iiswsgi_install.exe``

    This console script attempts to workaround the fact that WebPI and
    MSDeploy don't provide any context to the app being installed.
    Specifically, when using the ``runCommand`` MSDeploy provider in the
    ``Manifest.xml``, the process started by ``runCommand`` has no way
    to know which app it's being invoked for on install: not the
    current working directory, not in an argument, nor in any
    environment variable.

    As such this script has to search for the app before calling it's
    ``setup.py`` script.  It looks in ``IIS_SITES_HOME`` for
    directories with the right app name and a stamp file still in
    place.  See ``> Scripts\iiswsgi_install.exe --help`` for more
    details.  This is far too fragile and it would be vastly
    preferable if MSDeploy or WebPI set the APPL_PHYSICAL_PATH
    environment variable for ``runCommand``.  Anyone with a MS support
    contract, please submit a request about this.



Quick Start
===========

#. Copy the ``examples\pyramid.msdeploy`` package

#. Add dependencies to ``requirements.txt``

#. Add a WSGI PasteConfig in ``development.ini``

#. Search and replace IISWSGISampleApp in:

   * ``setup.py``
   * ``MANIFEST.in``
   * ``Manifest.xml.in``
   * ``Parameters.xml``


Overview
========

Deploying a Python WSGI application on IIS using the ``iiswsgi``
toolchain consists of three phases:

* building
* deploying
* serving

Building
--------

The ``iiswsgi_webpi.exe`` console script can be used to automate most of
the repetitive tasks involved:

* build Microsoft Web Deploy packages
* add them to a Web Platform Installer feed
* clear any relevant caches so changes take effect

Because of the ``Could not find file '\\?\C:\...`` error described below
in `Known Issues`_, it's not advisable to exit and re-launch WebPI.
As such, the best way to get feed changes to take effect in WebPI may
be to:

* Click on the `options` link in the bottom right of WebPI
* Click the `X` next to your feed to remove it
* Click `OK` and wait for WebPI to finish updating the remaining feeds
* Run `iiswsgi_webpi.exe`
* Click on the `options` link again in WebPI
* Enter the feed URL and click `Add Feed` to restore the feed
* Click `OK` and wait for WebPI again

Now your feed changes should be reflected in WebPI.

Sample Package
==============

The `examples\sample.msdeploy` sub-directory can be used to build a
sample MSDeploy package to be used with the `web-pi.xml` file as a
custom `Web Platform Installer feed
<http://blogs.iis.net/kateroh/archive/2009/10/24/web-pi-extensibility-custom-feeds-installing-custom-applications.aspx>`_
to test or as a basis for building your own packages and custom feeds.

  #. Exit the Web Platform Installer

     To make sure it uses the current version of the package and feed.

  #. Build the package
 
     A script is provided to make this easier.  Change to the directory
     containing this file in a `cmd.exe` prompt and run the following
     command::
 
       >C:\Python27\python.exe build_package.py
 
     That will build the package, clear the WebPI caches, and update
     the custom feed.
 
  #. Point WebPI to the local feed

     Skip this if you've already done it before.
   
     Force WebPI to use the modified feed.  Use the WebPI options
     screen to remove any previous Plone installer feeds and adding
     ``file:///C:/.../iiswsgi/examples/web-pi.xml`` replacing ``...``
     with the appropriate path.

  #. Install the package in WebPI

     Use the search box in WebPI to search for `iiswsgi`, click `Add`
     then click the `Install` button below and follow the
     instructions.

IIS FastCGI
===========

IIS' implementation of the FastCGI protocol is not fully compliant.
Most significantly, what is passed in on `STDIN_FILENO`_ is not a
handle to an open socket but rather to a `Windows named pipe`_.  This
names pipe does not support socket-like behavior, at least under
Python.  As such, the `iiswsgi.server` module extends `flup's WSGI to
FCGI gateway` to support using ``STDIN_FILENO`` opened twice, once
each approximating the `recv` and `send` end of a socket as is
specified in FastCGI.

IIS FastCGI Applications
------------------------

The ``iiswsgi.install`` package provides helpers which can be using an
an application's `Manifest.xml`_ file to automate the installation of
an IIS FastCGI application.  For those needing more control, the
following may help understand what's involved.

You can use IIS's `AppCmd.exe`_ to install new FastCGI applications.
You can find it at ``%ProgramFiles%\IIS Express\appcmd.exe`` for
WebMatrix/IIS Express or ``%systemroot%\system32\inetsrv\AppCmd.exe``
for IIS.  Note that you need to replace
``%SystemDrive%\Python27\Scripts\test.ini`` with the full path to a
`Paste Deploy INI configuration file`_
that defines the WSGI app and ``IISWSGI-Test`` with the name of your
app as IIS will see it::

    > appcmd.exe set config -section:system.webServer/fastCgi /+"[fullPath='%SystemDrive%\Python27\python.exe',arguments='-u %SystemDrive%\Python27\Scripts\iiswsgi-script.py -c %SystemDrive%\Python27\Scripts\test.ini',maxInstances='%NUMBER_OF_PROCESSORS%',monitorChangesTo='C:\Python27\Scripts\test.ini']" /commit:apphost

See the `IIS FastCGI Reference`_ for
more details on how to configure IIS for FastCGI.  Note that you
cannot use environment variable in the `monitorChangesTo` argument,
IIS will return an opaque 500 error.

Known Issues
============

`System.IO.FileNotFoundException: Could not find file '\\?\C:\...`

    I've run into this error on Windows 7 on two different machines
    and multiple installs, one OEM and one vanilla Windows 7 Extreme.
    When this happens, it seems to happen when the "Web Platform
    Installer" has been run, then exited, and then run again without
    rebooting the machine in between.  To workaround this, you may
    have to reboot the machine.  See the stack overflow question `MS
    WebPI package runCommand not working in Manifest.xml`_ for more
    information.

TODO building a MSDeploy package from an existing project

.. _MS WebPI package runCommand not working in Manifest.xml: http://stackoverflow.com/questions/12485887/ms-webpi-package-runcommand-not-working-in-manifest-xml/12820574#12820574
.. _Windows named pipe: http://msdn.microsoft.com/en-us/library/windows/desktop/aa365590(v=vs.85).aspx
.. _STDIN_FILENO: http://www.fastcgi.com/drupal/node/6?q=node/22#S2.2
.. _Microsoft Web Deploy: http://www.iis.net/downloads/microsoft/web-deploy
.. _Web Platform Installer: http://www.microsoft.com/web/downloads/platform.aspx
.. _AppCmd.exe: http://learn.iis.net/page.aspx/114/getting-started-with-appcmdexe
.. _IIS FastCGI Reference: http://www.iis.net/ConfigReference/system.webServer/fastCgi
.. _Paste Deploy INI configuration file: http://pythonpaste.org/deploy/index.html?highlight=loadapp#introduction
