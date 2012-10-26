==================================================
iiswsgi
==================================================
Serving Python WSGI applications natively from IIS
==================================================

The `iiswsgi`_ module implements a FastCGI to WSGI gateway that is
compatible with IIS's variation of the FastCGI protocol.  It also
provides distutils commands for building, distributing and installing
`Microsoft Web Deploy`_ (MSDeploy) packages through the `Web Platform
Installer`_ (WebPI).


Quick Start
===========

Assuming an existing Python distribution with a ``setup.py`` file and
a WSGI ``*.ini`` config file, roughly the following steps could be
used to released to WebPI:

#. Install `iiswsgi`_ into the Python environment used to build releases::

   >C:\Python27\Scripts\easy_install.exe -U iiswsgi

#. Copy the following to the dist root and adjust as appropriate:

   * ``examples/pyramid.msdeploy/Manifest.xml.in``
   * ``examples/pyramid.msdeploy/Parameters.xml``
   * ``examples/pyramid.msdeploy/iis_install.stamp.in``
   * ``examples/pyramid.msdeploy/web.config.in``

#. Add custom setup to ``setup.py``::

   ...
   from iiswsgi import install_msdeploy
   ...
   class install_custom_msdeploy(install_msdeploy.install_msdeploy):
       def run(self):
           """Perform custom tasks."""
           self.install()
           CUSTOM_SETUP
           self.test()
   ...
   setup(
   ...
         cmdclass=dict(install_msdeploy=install_custom_msdeploy),
   ...

#. Build a MSDeploy package::

   >C:\Python27\python.exe setup.py bdist_msdeploy

#. Add WebPI dependencies to ``setup.py``::

   ...
   setup(
   ...
         extras_require=dict(install_msdeploy=['virtualenv'],
                             webpi_eggs=['virtualenv', 'iiswsgi']),
   ...

#. Add WebPI feed metadata to ``setup.py``:

   See ``examples/pyramid.msdeploy/setup.py`` for an example.  

#. Build a local WebPI feed::

   >C:\Python27\python.exe setup.py bdist_webpi -u "{msdeploy_package_url}" -m .

#. Test locally:

   #. Install and launch the Web Platform Installer
   #. Click on the `options` link to the bottom right,
   #. Enter the feed URL below and click `Add Feed`:
      ``file:///C:/Users/%USERNAME%/Documents/GitHub/%DIST_NAME%/dist/%DIST_NAME%-%VERSION%-py2.7-win32.webpi.xml``
   #. Click `OK` and wait for WebPI to parse the feed
   #. Search for your dist and install
   #. Watch WebPI launch Web Matrix and open the site in a browser

#. Upload/Release

   >C:\Python27\python.exe setup.py bdist_msdeploy bdist_webpi -m . upload

If everything is working correctly, both a MSDeploy zip package and
the WebPI feed should be uploaded to PyPI.  Then you can instruct
users to add the feed to WebPI and they can install your package.


Web Deploy Package Contents
===========================

A developer releasing a MSDeploy package of a Python web app,
interacts with ``iiswsgi`` though the following files in a Python
distribution:

``setup.py``

    As with other Python build, distribute, and install tasks, this is
    where to control how the MSDeploy package is built, what is
    distributed, and how it's installed.

``MANIFEST.in``

    Use Python's source distribution manifest format to declare what
    will be in the package.

``Manifest.xml.in``

    A template used to generate the MSDeploy manifest.  When using `iiswsgi`_,
    it contains a ``runCommand`` provider that invokes
    `iiswsgi_install.exe`_.  Most packages will want to install into a
    virtualenv by including a ``-e`` option to `iiswsgi_install.exe`_.

``Parameters.xml``

    Defines the parameters WebPI will prompt the user for when
    installing.  See ``examples/pyramid.msdeploy/Parameters.xml`` for
    an example of using parameters to influence custom setup.

``web.config.in``

    A template used to generate the IIS site configuration file.  When
    using `iiswsgi`_, it contains a ``fastCgi`` application that
    invokes the `iiswsgi.exe`_ server.  Most packages will want to
    adjust the ``<application...`` attributes that control process
    behavior.  This is also where the ``*.ini`` config file or
    `entry_point`_ that define the WSGI app to run are specified.

``iis_install.stamp.in``

    A template copied into place to serve as the ``iis_install.stamp``
    stamp file used by ``>iiswsgi_install.exe`` to find the right
    ``APPL_PHYSICAL_PATH`` at install time.

``setup.cfg``

    This is only necessary if your ``setup.py`` is not using
    ``setuptools``.  IOW, under ``setuptools`` the commands are
    automatically available is ``iiswsgi`` is installed and there's no
    need for this file.  Without ``setuptools``, use the following to
    make the ``iiswsgi`` distutils commands available to your
    package::

        [global]
        command_packages = iiswsgi

Aside from these files, a Web Deploy package using ``iiswsgi`` is no
different than any other Python distribution or project nor should any
of the ``iiswsgi`` pieces interfere with any other uses of the same
distribution.  In particular, it should be possible to build and
upload MSDeploy package and WebPI feed dists in the same command as
building and uploading any other dist.


IIS WSGI Tools
==============

The moving parts of ``iiswsgi`` are as follows:

``>iiswsgi.exe``

    This console script is the FastCGI to WSGI gateway.  IIS invokes
    this script to start a Python WSGI app as a FastCGI process.  This
    can be used independently of the `distutils` commands.

``>python.exe setup.py build_msdeploy``

    This distutils command compiles a MSDeploy ``Manifest.xml``
    converting any ``runCommand`` attributes into the necessary hash.
    It will also copy into place the ``iis_install.stamp`` stamp file
    used by ``>iiswsgi_install.exe`` to find the right
    ``APPL_PHYSICAL_PATH`` at install time.

``>python.exe setup.py install_msdeploy``

    This distutils command performs common actions needed to deploy
    Python web apps on IIS: install dependencies, do variable
    substitution in ``web.config``, and install the FastCGI
    application into the IIS global config.

    The latter should be possible to do in the ``web.config`` file but
    that doesn't work.  Hence ``install_msdeploy`` works around this
    by reading the ``web.config`` and using ``appcmd.exe`` to do the
    actually FCGI app installation.  It would be much better if
    ``web.config`` worked as it should.  Anyone with a MS support
    contract, please submit a request about this.

``>python.exe setup.py bdist_msdeploy``

    This distutils command assembles an actual MSDeploy package: It
    starts by running ``build_msdeploy``.  Then it runs
    ``install_msdeploy`` in case your package needs any of the results
    of the installation process and to test the installation process.
    Finally, it creates a MSDeploy package zip file with the contents
    contolled by the same tools that `distutils` provides for
    ``sdist`` distributions, including ``MANIFEST.in``.

``>iiswsgi_install.exe``

    Bootstrap the MSDeploy package install process optionally setting
    up a virtualenv first.  It finds the correct
    ``APPL_PHYSICAL_PATH``, changes to that directory and invokes
    ``setup.py`` with arguments.

    This console script attempts to workaround the fact that WebPI and
    MSDeploy don't provide any context to the app being installed.
    Specifically, when using the ``runCommand`` MSDeploy provider in the
    ``Manifest.xml``, the process started by ``runCommand`` has no way
    to know which app it's being invoked for on install: not the
    current working directory, not in an argument, nor in any
    environment variable.

    As such this script has to search for the app before calling it's
    ``setup.py`` script.  It uses ``appcmd.exe`` to look in virtual
    directories whose site matches the app name and which contain a
    stamp file still in place.  See ``>Scripts\iiswsgi_install.exe
    --help`` for more details.  This is far too fragile and it would
    be vastly preferable if MSDeploy or WebPI set the
    APPL_PHYSICAL_PATH environment variable for ``runCommand``.
    Anyone with a MS support contract, please submit a request about
    this.

``>python.exe setup.py bdist_webpi``

    This distutils command assembles a WebPI feed from one or more
    MSDeploy packages with dependencies.  It can also include entries
    for normal Python dists.

``>python.exe setup.py clean_webpi``

    This distutils command clears the WebPI caches for one or more
    MSDeploy packages and the feed itself.


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

Debugging
=========

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
