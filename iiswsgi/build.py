import os
import subprocess
import tempfile
import shutil
import zipfile

from xml.dom import minidom

from distutils import cmd
from distutils.command import build
from distutils import log
from distutils import errors


class build_msdeploy(cmd.Command):
    """Build an MSDeploy zip package for installation into IIS."""

    manifest_name = 'Manifest.xml'
    stamp_template = 'iis_install.stamp.in'

    msdeploy = None
    if 'PROGRAMFILES' in os.environ:
        msdeploy = os.path.join(
            os.environ['PROGRAMFILES'], 'IIS', 'Microsoft Web Deploy V3',
            'msdeploy.exe')

    dest_name = 'runCommand.zip'

    def initialize_options(self):
        """Be more discriminating about what to prune."""
        cmd.Command.initialize_options(self)
        self.build_base = 'build/'

    def run(self):
        self.write_manifest()

        if os.path.exists(self.stamp_template):
            stamp_path = os.path.splitext(self.stamp_template)[0]
            if os.path.exists(stamp_path):
                log.info('Deleting existing stamp file: {0}'.format(
                    stamp_path))
                os.remove(stamp_path)
            log.info('Copying stamp file template to {0}'.format(
                stamp_path))
            shutil.copyfile(self.stamp_template, stamp_path)

    def write_manifest(self):
        manifest_template = self.manifest_name + '.in'
        if not os.path.exists(manifest_template):
            log.warn('No Web Deploy manifest template found at {0}'.format(
                manifest_template))
            # No manifest template, don't update real manifest
            return

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
                if self.msdeploy and os.path.exists(self.msdeploy):
                    subprocess.check_call(args, shell=True)
                else:
                    log.error('msdeploy.exe does not exist: {0}'.format(
                                  self.msdeploy))
                    continue
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


def has_msdeploy_manifest(self):
    return os.path.exists(self.msdeploy_manifest)

build.build.sub_commands.append(('build_msdeploy', has_msdeploy_manifest))
