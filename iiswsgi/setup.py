import os
import subprocess
import tempfile
import zipfile
import shutil

from xml.dom import minidom

from distutils.command import build
from distutils.command import sdist
from distutils import archive_util
from distutils import log
from distutils import errors

# TODO upload


class MSDeployBuild(build.build):
    """Build an MSDeploy zip package for installation into IIS."""

    manifest_name = 'Manifest.xml'
    msdeploy = os.path.join(
        os.environ['PROGRAMFILES'], 'IIS', 'Microsoft Web Deploy V3',
        'msdeploy.exe')
    dest_name = 'runCommand.zip'

    def initialize_options(self):
        """Be more discriminating about what to prune."""
        build.build.initialize_options(self)
        self.build_base = 'build/'

    def run(self):
        # TODO use sub_commands
        result = build.build.run(self)

        manifest_template = self.manifest_name + '.in'
        if not os.path.exists(manifest_template):
            log.warn('No Web Deploy manifest template found at {0}'.format(
                manifest_template))
            # No manifest template, don't update real manifest
            return result

        manifest = minidom.parse(manifest_template)
        for runcommand in manifest.getElementsByTagName('runCommand'):
            # Collect the attributes that need to be passed as settings
            path = None
            settings_attrs = {}
            for name, value in runcommand.attributes.items():
                if name == 'path':
                    # provider value/key attribute
                    path = value
                    continue
                elif name.startswith('MSDeploy.'):
                    # Leave these alone
                    continue
                settings_attrs[name] = value
                # Remove them from the output XML
                runcommand.removeAttribute(name)
            if path is None:
                raise errors.DistutilsFileError(
                    'No `path` attribute in a <runCommand> element in {0}'
                    .format(manifest_template))

            # Assemble the msdeploy.exe source command line
            settings = ','.join('{0}={1}'.format(*item) for item in
                                settings_attrs.items())
            if settings:
                settings = ',' + settings
            source = '-source:runCommand="{0}"{1}'.format(path, settings)

            tmp = tempfile.mkdtemp()
            package = os.path.join(tmp, 'runCommand.zip')
            try:
                args = (
                    '"{msdeploy}" -verb:sync {source} -dest:package={package}'
                    .format(msdeploy=self.msdeploy, source=source,
                            package=package))
                log.info('Generating runCommand manifest: {0}'.format(args))
                subprocess.check_call(args, shell=True)
                tmp_manifest = minidom.parseString(
                    zipfile.ZipFile(package).read('archive.xml'))
            finally:
                shutil.rmtree(tmp)

            new_runcommands = tmp_manifest.getElementsByTagName('runCommand')
            if not new_runcommands:
                raise errors.DistutilsExecError(
                    'No <runCommand> elements found in {0}:archive.xml'
                    .format(package))
            elif len(new_runcommands) > 1:
                raise errors.DistutilsExecError(
                    'Multiple <runCommand> elements found in {0}:archive.xml'
                    .format(package))

            options = new_runcommands[0].getAttribute(
                'MSDeploy.MSDeployProviderOptions')
            runcommand.setAttribute(
                'MSDeploy.MSDeployProviderOptions', options)

        log.info('Writing Web Deploy manifest to {0}'.format(
            self.manifest_name))
        manifest.writexml(open(self.manifest_name, 'w'))

        return result


def make_zipfile(base_name, base_dir, verbose=0, dry_run=0):
    """Create a zip file from all the files under 'base_dir'.

    The output zip file will be named 'base_name' + ".zip".  Uses either the
    "zipfile" Python module (if available) or the InfoZIP "zip" utility
    (if installed and found on the default search path).  If neither tool is
    available, raises DistutilsExecError.  Returns the name of the output zip
    file.
    """
    import zipfile

    zip_filename = base_name + ".zip"
    archive_util.mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

    archive_util.log.info("creating '%s' and adding '%s' to it",
             zip_filename, base_dir)

    if not dry_run:
        zip = zipfile.ZipFile(zip_filename, "w",
                              compression=zipfile.ZIP_DEFLATED)

        for dirpath, dirnames, filenames in os.walk(base_dir):
            for name in filenames:
                src_path = os.path.normpath(os.path.join(dirpath, name))
                dirpath_split = os.path.split(dirpath)
                dst_dirpath = dirpath_split[1:]
                if dirpath_split[0] == '':
                    dst_dirpath = dirpath_split[2:]
                dst_path = os.path.normpath(os.path.join(*(
                    dst_dirpath + (name,))))
                if os.path.isfile(src_path):
                    zip.write(src_path, dst_path)
                    archive_util.log.info("adding '%s'" % dst_path)
        zip.close()

    return zip_filename


class MSDeploySDist(sdist.sdist):
    """Create an MSDeploy zip package for installation into IIS."""

    def make_archive(self, base_name, format, root_dir=None, base_dir=None,
                     owner=None, group=None):
        """Create a zip file without a top-level directory."""
        make_zipfile(base_name, base_dir,
                     verbose=self.verbose, dry_run=self.dry_run)

# TODO separate actions, msdeploy_package depending on msdeploy_build
cmdclass = dict(build=MSDeployBuild,
                sdist=MSDeploySDist)
