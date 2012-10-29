==================================================
iiswsgi
==================================================
Serving Python WSGI applications natively from IIS
==================================================

The `iiswsgi`_ module implements a FastCGI to `WSGI`_ gateway that
is compatible with `IIS`_'s variation of the `FastCGI protocol`_.  It also
provides `distutils`_ commands for building, distributing and installing
`Microsoft Web Deploy`_ (MSDeploy) packages through the `Web Platform
Installer`_ (WebPI).

.. contents::


Quick Start
===========

Quick Start for Users
---------------------

The ``iiswsgi`` distribution includes two sample IIS apps which can be
installed through WebPI once the custom feed has been added:

#. Install and Launch `Web Platform Installer`_

#. Use the search box in the upper-right to search for `Web Matrix`

#. Click add next to the most recent `Web Matrix` entry, then
   `Install` in the lower-right and follow the instructions

#. Open the `Options` dialog by clicking the link on the lower-right

#. Under `Custom Feeds`, add the URL for latest ``*.webpi.xml`` file
   from the `iiswsgi downloads`_ and click `Add feed`

#. Under `Which Web Server...?`, check `IIS Express` and then click
   `OK`

#. Use the search box in the upper-right to search for `pyramid`

#. Click add next to `Pyramid Application` then `Install` in the
   lower-right and follow the instructions

Quick Start for Distributors
----------------------------

Assuming an existing `Python`_ distribution with a `Setup Script`_ using
`setuptools`_ and a `WSGI`_ ``*.ini`` `Paste config file`_, roughly
the following steps could be used to released to WebPI:

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
            os.environ['WEB_CONFIG_VAR'] = 'foo'
            self.pre_install()
            CUSTOM_SETUP
            self.post_install()
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

#. Install the `Web Platform Installer`_:

#. `Install fciv.exe`_ to generate SHA1 hashes:

   Must be placed on the ``%PATH%``.  The recommended place would be
   ``%ProgramFiles%\Microsoft\Web Platform Installer`` because it's
   placed on the path when WebPI is installed.

#. Build a local `WebPI feed`_::

    >C:\Python27\python.exe setup.py bdist_webpi -u "{msdeploy_package_url}" -m .

#. Test locally:

   #. Launch the Web Platform Installer
   #. Click on the `options` link to the bottom right,
   #. Enter the feed URL below and click `Add Feed`:
      ``file:///C:/Users/%USERNAME%/Documents/GitHub/%DIST_NAME%/dist/%DIST_NAME%-%VERSION%-py2.7-win32.webpi.xml``
   #. Click `OK` and wait for WebPI to parse the feed
   #. Search for your dist and install
   #. Watch WebPI launch Web Matrix and open the site in a browser

#. Upload/Release::

    >C:\Python27\python.exe setup.py bdist_msdeploy bdist_webpi -m . upload

If everything is working correctly, both a MSDeploy zip package and
the WebPI feed should be uploaded to `PyPI`_.  Then you can instruct
users to add the feed to WebPI and they can install your package.


How it Works
============

Releasing a WSGI app on IIS involves several steps and moving pieces.
See the `Web Deploy Package Contents`_ and `IIS WSGI Tools`_ sections
for more technical details.  Here is an overview of the process and
the technologies involved.

A Python Distribution
---------------------

This is a pre-requisite and is not at all specific to IIS, MSDeploy or
WebPI, only Python.  This is just a directory with a ``setup.py``
`Setup Script`_ that defines the distribution and it's metadata and
very little is done differently from the standard Python `distutils`_
and `setuptools`_ ways of doing things.  IOW, wherever possible,
`iiswsgi` tries to re-use ``setup.py`` metadata and where it needs new
metadata it uses `setuptools`_ `entry points`_ to add `setup kwargs`_.

Custom Set Up
-------------

If the app requires extra set up beyond just setting up a
`virtualenv`_ and installing dependencies, this can also be
implemented in ``setup.py`` by subclassing the ``install_msdeploy``
`Install MSDeploy`_ command.  See the `Quick Start`_ and the `Install
MSDeploy`_ command for more details.

The MSDeploy Package
--------------------

Microsoft's Web Deploy Tool is what WebPI uses to install an IIS app
and expects a `MSDeploy package`_, simple zip file with some metadata
in it.  There some `special files`_ and three ``iiswsgi`` `distutils`_
commands that help in defining and building a MSDeploy package.  The
commands can also be run indiviually or run all at once by running
just the last step which will run the others first.  Running them
individually is useful to debug packaging problems.

    #. `Build MSDeploy Package`_ ``build_msdeploy`` command
    #. `Install MSDeploy`_ ``install_msdeploy`` command
    #. `Test MSDeploy`_ ``test_msdeploy`` command
    #. `Build MSDeploy Distribution`_ ``bdist_msdeploy`` command

On completion of the last command a MSDeploy zip file will be in the
``dist`` directory just like any other dist command, such as
``sdist``.  You can also upload the package using the ``upload``
command.

Logging output or managing verbosity for building the package is no
different than for any other disutils/setup.py uses, output is on the
console and can be redirected if you wan to capture it.  See
``>C:\Python27\python.exe setup.py --help`` for more details.

The WebPI Feed
--------------

The Web Platform installer can be given additional feeds in it's
options dialog.  This feed can define things that can be installed
along with their metadata including dependencies.  The `bdist_webpi`_
command can build this feed as another dist file, and can thus also be
released using the ``upload`` command.

To test locally, use the ``bdist_webpi -u "{msdeploy_package_url}"``
option to put ``file:///...`` download URLs for the MSDeploy packages
in the feed.  Then use the ``file:///...`` URL for the feed
itself in WebPI's options dialog that is printed to the console when
the ``bdist_webpi`` command is run.

WebPI logs information while processing the feed in the
``%LOCALAPPDATA%\Microsoft/Web Platform Installer/logs/webpi``
diretory.  When debugging feed issues just look at the most recently
modified ``webpi#.txt`` file in that directory.

MSDeploy Package Installation
-----------------------------

Once the feed is included in WebPI, the entries can be searched for
and installed.  After installation, but before WebPI reports
completion, any `runCommand` providers in the `MSDeploy Manifest`_ are
run which is when `iiswsgi_install.exe`_ script is invoked to find the
installed app and to run distutils setup commands, `install_msdeploy`_
and `test_msdeploy`_ by default, in that distribution.  Most apps will
want to use the ``iiswsgi_install.exe -e`` option to setup a
virtualenv before running setup commands.  See `MSDeploy Manifest`_
and `install_msdeploy`_ for more details and considerations.

While installing, WebPI and MSDeploy log output into
``%LOCALAPPDATA%\Microsoft/Web Platform Installer/logs/install``.
When debugging installation issues just look at the ``App Title.txt``
file in the most recently modified date-stamped direstory within that
directory.  Verbosity can be controlled by adding the
``iiswsgi_install.exe -v`` option in your `Manifest.xml`_
``<runCommand path=...`` attribute.  It's also often valuable to run
the `install_msdeploy` command locally in the installed app after an
installation error to debug further.

IIS Hosting
-----------

If installation has completed, there will be a
``<fastCgi><application...`` in the global IIS config, a corresponding
handler in the app's ``web.config`` and when a request comes in for
the app, IIS will invoke the handler specified.  For `iiswsgi`_, the
handler will be an `paster serve`_ invocation that uses the
`egg:iiswsgi#iis`_ FCGI server.  To use a general purpose `PasteDeploy
INI configuration file`_, you can use a handler like ``paster.exe
serve -s "egg:iiswsgi#iis" ...`` to use the `iiswsgi` FCGI server with
a configuration file that doesn't specify it.

IIS swallows all FCGI process output if there are any errors starting
up which can make startup issues really hard to debug.  The first step
should be manually invoking the FCGI process using the ``fullPath``
and ``arguments`` attributes from the ``<application...`` element in
``web.config``.  In case that doesn't reproduce the error, the
`egg:iiswsgi#iis`_ FCGI server tries to be conservative during startup
to ensure that output is logged *somewhere*.  Check the following
locations for output:

    * ``%IIS_USER_HOME%\Logs\%IISEXPRESS_SITENAME%\iiswsgi.log``
    * ``%IIS_USER_HOME%\Logs\iiswsgi.log``
    * ``%TEMP%\iiswsgi.log``
    * ``\iiswsgi.log``

Verbosity is controlled by giving the ``paster serve -v...`` option to
`PasteScript`_ in the `web.config.in`_ template.


Web Deploy Package Contents
===========================

A developer releasing a MSDeploy package of a Python web app,
interacts with `iiswsgi`_ though the following files in a Python
distribution.  Aside from these files, a Web Deploy package using
``iiswsgi`` is no different than any other Python distribution or
project nor should any of the ``iiswsgi`` pieces interfere with any
other uses of the same distribution.  In particular, it should be
possible to build and upload MSDeploy package and WebPI feed dists in
the same command as building and uploading any other dist.

Setup Script
------------

As with other Python build, distribute, and install tasks, the
``setup.py`` script is where to control how the MSDeploy package is
built, what is distributed, and how it's installed.

Python Manifest
---------------

Use Python's source distribution `MANIFEST.in`_ template format to
declare what will be in the package.

MSDeploy Manifest
-----------------

Use the ``Manifest.xml.in`` template to generate the `Web Deploy
manifest`_.  When using `iiswsgi`_, it contains a `runCommand`_
provider that invokes the ``iswsgi_install.exe`` `MSDeploy Install
Bootstrap`_ script.  Most packages will want to install into a
`virtualenv`_ by including a ``-e`` option to ``iiswsgi_install.exe``.

The `build_msdeploy`_ command can be used to write `runCommand option
attributes`_ into the hash that MSDeploy uses when processing the
manifest during installation.  Most apps will want to include the
``successReturnCodes="0x0"`` attribute to ensure that failures in the
command are reported back to the user.  Many apps will also want to
adjust the ``waitAttempts="5"`` and/or ``waitInterval="1000"``
attributes to give the commands enough time to complete.

MSDeploy Parameters
-------------------

The `Parameters.xml`_ file defines the parameters WebPI will prompt
the user for when installing.  See
``examples/pyramid.msdeploy/Parameters.xml`` for an example of using
parameters to influence custom setup.

IIS Web Config
--------------

Use the ``web.config.in`` template to generate the `IIS site
configuration file`_.  When using `iiswsgi`_, it contains a `fastCgi`_
application that invokes the ``egg:iiswsgi#iis`` `iiswsgi FCGI
Gateway`_.  Most packages will want to adjust the `<application...`_
attributes that control process behavior.  This is also where the
``*.ini`` config file or `app_factory entry point`_ that define the
WSGI app to run are specified.

IIS Install Stamp File
----------------------

The ``iis_install.stamp.in`` template copied into place to serve as
the ``iis_install.stamp`` stamp file used by the
``iiswsgi_install.exe`` `MSDeploy Install Bootstrap`_ script to find
the right ``APPL_PHYSICAL_PATH`` at install time.

Setup Congig
------------

The `setup.cfg`_ file is only necessary if your `Setup Script`_ is not
using `setuptools`.  IOW, under ``setuptools`` the commands are
automatically available is ``iiswsgi`` is installed and there's no
need for this file.  Without ``setuptools``, use the following to make
the ``iiswsgi`` distutils commands available to your package::

    [global]
    command_packages = iiswsgi


IIS WSGI Tools
==============

The moving parts of ``iiswsgi`` are as follows:

iiswsgi FCGI Gateway
--------------------

The ``egg:iiswsgi#iis`` `paste.server_runner`_ or
`paste.server_factory`_ is the FastCGI to WSGI gateway.  IIS invokes
the `paster`_ script from `PasteScript`_ with a `PasteDeploy INI
configuration file`_ to start a Python WSGI app as a FastCGI process.
Tell ``paster`` to use the IIS FCGI gateway with ``paster.exe serve -s
"egg:iiswsgi#iis" ...`` or in the `PasteDeploy INI configuration
file`_::

    [server:iis]
    use = egg:iiswsgi#iis

This is not intrinsically related to the `distutils`_ commands and can
be used independently of them if a project should need to.

IIS' implementation of the FastCGI protocol is not fully compliant.
Most significantly, what is passed in on `STDIN_FILENO`_ is not a
handle to an open socket but rather to a `Windows named pipe`_.  This
names pipe does not support socket-like behavior, at least under
Python.  As such, the ``egg:iiswsgi#iis`` gateway extends `flup's WSGI
to FCGI gateway`_ to support using ``STDIN_FILENO`` opened twice, once
each approximating the ``recv`` and ``send`` end of a socket as is
specified in FastCGI.

Build MSDeploy Package
----------------------

The ``build_msdeploy`` distutils command compiles a MSDeploy
``Manifest.xml`` converting any `runCommand`_ attributes into the
necessary hash.  It will also copy into place the `IIS Install Stamp
File`_ ``iis_install.stamp`` stamp file used by the `MSDeploy Install
Bootstrap`_ ``iiswsgi_install.exe`` script to find the right
``APPL_PHYSICAL_PATH`` at install time.

Install MSDeploy
----------------

The ``install_msdeploy`` distutils command performs common actions
needed to deploy Python web apps on IIS: install dependencies, do
variable substitution in `web.config`_, and install the FastCGI
application into the IIS global config.

Since most apps will require path or parameter specific bits in the
``web.config`` file, the `install_msdeploy`_ command will perform
variable substitution while writing the ``web.config.in`` template to
``web.config``.  To add variables to the substitution, just use
`Custom Set Up`_ to put them into `os.environ`_ before calling the
base class's ``run()`` method.

Since ``<fastCgi><application...`` elements don't take effect in the
``web.config``, the `install_msdeploy`_ command will use.  For
reference or debugging here's an example::

    > appcmd.exe set config -section:system.webServer/fastCgi /+"[fullPath='%SystemDrive%\Python27\python.exe',arguments='-u %SystemDrive%\Python27\Scripts\iiswsgi-script.py -c %HOMEDRIVE%%HOMEPATH%\Documents\My Web Sites\FooApp\test.ini',maxInstances='%NUMBER_OF_PROCESSORS%',monitorChangesTo='C:\Users\Administrator\Documents\My Web Sites\FooApp\test.ini']" /commit:apphost

See the `IIS FastCGI Reference`_ for
more details on how to configure IIS for FastCGI.  Note that you
cannot use environment variable in the `monitorChangesTo` argument,
IIS will return an opaque 500 error.

This is also where to `Custom Set Up`_ by subclassing the
``install_msdeploy`` `Install MSDeploy`_ command in the ``setup.py``
`Setup Script`_ and using the distutils `cmdclass`_ kwarg to
``setup()``.  See `Quick Start`_ for a small example or
``examples\pyramid.msdeploy\setup.py`` for a working example.

Test MSDeploy
-------------

The ``test_msdeploy`` distutils command uses `paster request`_ with a
`PasteDeploy INI configuration file`_ to simulate sending a request to
the app.  If it fails, the command fails, making this useful to run
during `MSDeploy Package Installation`_ to ensure the user sees an
error in WebPI if the app isn't working even though the rest of the
install succeeded.  See ``>C:\Python27\python.exe setup.py
test_msdeploy --help`` for more details.


Build MSDeploy Distribution
---------------------------

The ``bdist_msdeploy`` distutils command assembles an actual MSDeploy
package: It starts by running the ``build_msdeploy`` `Build MSDeploy
Package`_ command.  Then it runs the ``install_msdeploy`` `Install
MSDeploy`_ command in case your package needs any of the results of
the installation process and to test the installation process.
Finally, it creates a `MSDeploy package`_ zip file with the contents
contolled by the same tools that `distutils`_ provides for ``sdist``
distributions, including ``MANIFEST.in``.

MSDeploy Install Bootstrap
--------------------------

The ``iiswsgi_install.exe`` script bootstraps the MSDeploy package
install process optionally setting up a virtualenv first.  It finds
the correct ``APPL_PHYSICAL_PATH``, changes to that directory and
invokes the `Setup Script`_ with arguments.

This console script attempts to workaround the fact that WebPI and
MSDeploy don't provide any context to the app being installed.
Specifically, when using the `runCommand`_ MSDeploy provider in the
`Manifest.xml`_, the process started by ``runCommand`` has no way to
know which app it's being invoked for on install: not the current
working directory, not in an argument, nor in any environment
variable.

As such this script has to search for the app before calling it's
`Setup Script`_.  It uses `appcmd.exe`_ to look in virtual directories
whose site matches the app name and which contain a stamp file still
in place.  See ``>Scripts\iiswsgi_install.exe --help`` for more
details.

Build WebPI Feed Distribution
-----------------------------

The ``bdist_webpi`` distutils command assembles a WebPI feed from one
or more MSDeploy packages with dependencies.  The MSDeploy packages to
include are defined by passing paths to distrubutions with
``setup.py`` files whose MSDeploy dist zip files have previously been
built in the ``--msdeploy-bdists`` command option separated by
`shlex.split`_.  The download URLs for the MSDeploy zip files is
determined by expanding the ``msdeploy_url_template`` ``setup()``
kwarg with `Python string.format()`_.


The global feed metadata is taken from the distribution the command is
being run for.  Entries are added to the feed for the distributions
lited in the ``--msdeploy-bdists`` command option and the
``webpi_eggs`` depdencies in `extras_require`_. The WebPI dependencies
and related products are taken from the lists given in the
``install_msdeploy`` and ``install_webpi`` ``setup()`` kwargs
respectivels.  The metadata for those entries is taken from the
corresponding distributions.  The following are additional ``setup()``
kwargs that are used in the feed if defined for a given distrubution:

    * title
    * author_url
    * license_url
    * display_url
    * help_url
    * published
    * icon_url
    * screenshot_url
    * discovery_file
            
Clean WebPI Caches
------------------

The ``clean_webpi`` distutils command clears the `WebPI caches`_ for
one or more MSDeploy package downloads and the feed itself.  The
MSDeploy packages to be cleared from the cache are taken from the same
``--msdeploy-bdists`` command option.


Debugging
=========

One of the more important goals of `iiswsgi`_ is to bring some greater
transparency and introspection to the process of integrating with
IIS.  It's a very common experience for developers in the
non-Window/UNIX world that developing and even deploying on Windows is
much more fragile and opaque than on any other OS.  Here's some of
what `iiswsgi` does to try and address that.

Graceful Degredation on non-Windows
    Fist and foremost, `iiswsgi` tries to degrade gracefully when run
    on non-windows platforms.  Specifically, when some executable,
    environment variable, or other Windows specific piece of the
    environment is missing, the `iiswsgi` operation will not raise an
    exception but only log an error.  This allows developing and, to a
    limited extent, testing MSDeploy packages on *NIX platforms.  A
    side-effect of this is that some errors may be missed when there
    is a lot of console output from one of the `distutils`_ commands
    when running *on Windows*, so check your output carefully.

Logging
    Finding information about what went wrong when some part of the
    process fails can be a lot more difficult on Windows than it is on
    other platforms.  See the sections of `How it Works`_ for where to
    look for log files for each part of the process.


Known Issues
============

FCGI Process not launching under IIS
    The sample app will deploy just fine to IISExpress/Web Matrix, but
    when switched over to full IIS, it reports that the FCGI process
    exited prematurely.  Even after instrumenting the very top of the
    script with writes to a file followed by ``flush()`` and
    ``fsync()`` the file still has nothing in it.  So it seems like
    IIS is never actually launching the processs.  If anyone can test
    this and give some insight, it would be greatly appreciated.

Can't access ``APPL_PHYSICAL_PATH`` in ``runCommand`` provider
    The current method of searching for the  is far too fragile and it would
    be vastly preferable if MSDeploy or WebPI set the
    APPL_PHYSICAL_PATH environment variable for ``runCommand``.
    Anyone with a MS support contract, please submit a request about
    this.

``<fastCgi><application>`` doesn't take effect in ``web.config``
    It should be possible to `register a FCGI application in the
    web.config`_ file but that doesn't work.  Hence
    ``install_msdeploy`` works around this by reading the
    ``web.config`` and using `AppCmd.exe`_ to do the actually FCGI app
    installation.  It would be much better if ``web.config`` worked as
    it should.  Anyone with a MS support contract, please submit a
    request about this.

``System.IO.FileNotFoundException: Could not find file '\\?\C:\...``
    I've run into this error on Windows 7 on two different machines
    and multiple installs, one OEM and one vanilla Windows 7 Extreme.
    When this happens, it seems to happen when the "Web Platform
    Installer" has been run, then exited, and then run again without
    rebooting the machine in between.  To workaround this, you may
    have to reboot the machine.  See the stack overflow question `MS
    WebPI package runCommand not working in Manifest.xml`_ for more
    information.  As such, it's not advisable to exit and re-launch
    WebPI.  As such, the best way to get feed changes to take effect
    in WebPI may be to:

        #. Click on the `options` link in the bottom right of WebPI
        #. Click the `X` next to your feed to remove it
        #. Click `OK` and wait for WebPI to finish updating the remaining feeds
        #. Run `iiswsgi_webpi.exe`
        #. Click on the `options` link again in WebPI
        #. Enter the feed URL and click `Add Feed` to restore the feed
        #. Click `OK` and wait for WebPI again

    Now your feed changes should be reflected in WebPI.

``System.IO.FileNotFoundException: Could not load file or assembly``
    This error happens when using WebPI to install on full IIS, IOW
    when not using IIS Express and Web Matrix.  It can be worked
    around by installing the "Web Deploy Tool" in WebPI.  The
    `bdist_webpi`_ command works around this by adding it as a
    dependency for all MSDeploy packages.  Here's the error from the
    logs::

        DownloadManager Error: 0 : System.IO.FileNotFoundException: Could not load file or assembly 'Microsoft.Web.Deployment, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35' or one of its dependencies. The system cannot find the file specified.
        File name: 'Microsoft.Web.Deployment, Version=9.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35'
           at Microsoft.Web.PlatformInstaller.MSDeployProxy.GetDeclaredParameters()
           at Microsoft.Web.PlatformInstaller.MSDeployPackage.get_DeclaredParameters()
           at Microsoft.Web.PlatformInstaller.UI.AppSitePage.GetApplicationName(MSDeployPackage package, String& appName)
           at Microsoft.Web.PlatformInstaller.UI.AppSitePage.InitializeComponent()

``retrieving the com class factory for remote component CLSID 2b72133b-3f5b-4602-8952-803546CE3344 error 80040154``
    This error happens when using WebPI to install on full IIS, IOW
    when not using IIS Express and Web Matrix.  It can be worked
    around by installing the "IIS Management Console" in WebPI
    dependency

WebPI Errors May be Burried
    On occasion, WebPI may burry error messages behind the WebPI
    window.  So if WebPI has been hung for a long time, try using
    ``Alt-TAB`` to see if there's an error window hidden behind the
    WebPI window.

WebPI getting cached feeds and MSDeploy packages
    Despite the `clean_webpi`_ helper and manually clearing all the
    caches under ``%LOCALAPPDATA%\Microsoft/Web Platform Installer``,
    there have been several times when WebPI has still gotten stale
    content causing validation errors against the SHA1 in the feed and
    other problems.  When this happens, a workaround may be to
    download the stale WebPI resources in IE.


.. _`special files`: `Web Deploy Package Contents`_
.. _`bdist_webpi`: `Build WebPI Feed Distribution`_
.. _`clean_webpi`: `Clean WebPI Caches`_
.. _`iiswsgi_install.exe`: `MSDeploy Install Bootstrap`_
.. _`install_msdeploy`: `Install MSDeploy`_
.. _`test_msdeploy`: `Test MSDeploy`_
.. _`egg:iiswsgi#iis`: `iiswsgi FCGI Gateway`_
.. _`build_msdeploy`: `Build MSDeploy Package`_
.. _`web.config.in`: `IIS Web Config`_

.. _`iiswsgi downloads`: https://github.com/rpatterson/iiswsgi/downloads

.. _`Python`: http://python.org
.. _`os.environ`: http://docs.python.org/2/library/os.html#os.environ
.. _`shlex.split`: http://docs.python.org/2/library/shlex.html#shlex.split
.. _`distutils`: http://docs.python.org/distutils/
.. _`setup.cfg`: http://docs.python.org/distutils/configfile.html
.. _`cmdclass`: http://docs.python.org/distutils/extending.html#integrating-new-commands
.. _`Python string.format()`: http://docs.python.org/2/library/string.html#formatstrings
.. _`PyPI`: http://pypi.python.org/pypi
.. _`setuptools`: http://packages.python.org/distribute
.. _`entry points`: http://packages.python.org/distribute/setuptools.html#entry-points
.. _`setup kwargs`: http://packages.python.org/distribute/setuptools.html#adding-setup-arguments
.. _`extras_require`: http://packages.python.org/distribute/setuptools.html#declaring-extras-optional-features-with-their-own-dependencies
.. _`MANIFEST.in`: http://docs.python.org/distutils/sourcedist.html#the-manifest-in-template
.. _`WSGI`: http://wsgi.readthedocs.org/en/latest/
.. _`Paste config file`: http://pythonpaste.org/deploy/#config-format
.. _`PasteDeploy INI configuration file`: http://pythonpaste.org/deploy/index.html?highlight=loadapp#introduction
.. _`PasteScript`: http://pythonpaste.org/script/#paster-serve
.. _`paster`: `PasteScript`_
.. _`paster serve`: `PasteScript`_
.. _`paster request`: http://pythonpaste.org/modules/request.html
.. _`app_factory entry point`: http://pythonpaste.org/deploy/#paste-app-factory
.. _`paste.server_runner`: http://pythonpaste.org/deploy/#paste-server-runner
.. _`paste.server_factory`: http://pythonpaste.org/deploy/#paste-server-factory
.. _`flup's WSGI to FCGI gateway`: http://trac.saddi.com/flup/wiki/FlupServers
.. _`virtualenv`: http://www.virtualenv.org

.. _`IIS`: http://www.iis.net
.. _`Microsoft Web Deploy`: http://www.iis.net/downloads/microsoft/web-deploy
.. _`Web Platform Installer`: http://www.microsoft.com/web/downloads/platform.aspx
.. _`WebPI feed`: http://technet.microsoft.com/en-us/library/ee424348(v=ws.10).aspx
.. _`WebPI caches`: http://www.iis.net/learn/troubleshoot/web-platform-installer-issues/troubleshooting-problems-with-microsoft-web-platform-installer
.. _`Install fciv.exe`: http://support.microsoft.com/kb/841290
.. _`Web Deploy manifest`: http://www.iis.net/learn/develop/windows-web-application-gallery/reference-for-the-web-application-package
.. _`Manifest.xml`: `Web Deploy manifest`_
.. _`Parameters.xml`: `Web Deploy manifest`_
.. _`MSDeploy package`: `Web Deploy manifest`_
.. _`runCommand`: http://technet.microsoft.com/en-us/library/ee619740(v=ws.10).aspx
.. _`runcommand option attributes`: `runCommand`_
.. _`IIS site configuration file`: http://technet.microsoft.com/en-us/library/cc754617(v=ws.10).aspx
.. _`web.config`: `IIS site configuration file`_
.. _`fastCgi`: http://www.iis.net/configreference/system.webserver/fastcgi
.. _`<application...`: http://www.iis.net/configreference/system.webserver/fastcgi/application
.. _`MS WebPI package runCommand not working in Manifest.xml`: http://stackoverflow.com/questions/12485887/ms-webpi-package-runcommand-not-working-in-manifest-xml/12820574#12820574
.. _`register a FCGI application in the web.config`: http://stackoverflow.com/questions/12525508/system-webserver-fastcgi-application-not-working-in-web-config

.. _`AppCmd.exe`: http://learn.iis.net/page.aspx/114/getting-started-with-appcmdexe
.. _`IIS FastCGI Reference`: http://www.iis.net/ConfigReference/system.webServer/fastCgi
.. _`FastCGI protocol`: http://www.fastcgi.com/drupal/
.. _`STDIN_FILENO`: http://www.fastcgi.com/drupal/node/6?q=node/22#S2.2
.. _`Windows named pipe`: http://msdn.microsoft.com/en-us/library/windows/desktop/aa365590(v=vs.85).aspx

