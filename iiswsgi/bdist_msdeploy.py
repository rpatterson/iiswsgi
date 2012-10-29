"""Create an MSDeploy zip package for installation into IIS."""

import os
import zipfile
import sysconfig

from distutils.command import sdist
from distutils import archive_util
from distutils import dir_util
from distutils import log
from distutils import errors

from iiswsgi import build_msdeploy
from iiswsgi import options


class bdist_msdeploy(sdist.sdist):
    description = __doc__ = __doc__

    user_options = [opt for opt in sdist.sdist.user_options
                    if not opt[0].startswith('formats')]

    manifest_filename = build_msdeploy.manifest_filename
    msdeploy_files = (manifest_filename, 'Parameters.xml')

    def initialize_options(self):
        sdist.sdist.initialize_options(self)
        self.install = self.distribution.get_command_obj('install_msdeploy')
        self.install.skip_fcgi_app_install = True

    def finalize_options(self):
        sdist.sdist.finalize_options(self)
        self.formats = ['zip']
        self.install.ensure_finalized()
        options.ensure_verbosity(self)

    def run(self):
        self.run_command('build_msdeploy')
        if not os.path.exists(self.manifest_filename):
            raise errors.DistutilsFileError(
                'No Web Deploy manifest found at {0}'.format(
                    self.manifest_filename))

        if self.install not in self.distribution.have_run:
            self.install.run()
            self.distribution.have_run[self.install] = 1

        sdist.sdist.run(self)

    def make_distribution(self):
        """Minimize path lenght to avoid windows issues."""
        # Copied from distutils.command.sdist.sdist.make_distribution

        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_version()
        base_name = os.path.join(
            self.dist_dir,
            options.get_egg_name(self.distribution) + '.msdeploy')

        self.make_release_tree(base_dir, self.filelist.files)
        archive_files = []              # remember names of files we create

        file = self.make_archive(base_name, 'zip', base_dir=base_dir,
                                 owner=self.owner, group=self.group)
        archive_files.append(file)
        pyversion = sysconfig.get_python_version()
        self.distribution.dist_files.append(('bdist_dumb', pyversion, file))

        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, dry_run=self.dry_run)

    def make_archive(self, base_name, format, root_dir=None, base_dir=None,
                     owner=None, group=None):
        """Don't inlcude the version number for MSDeploy packages."""
        dry_run = self.dry_run
        dist_name = self.distribution.get_name()

        # Copied from distutils.command.sdist.sdist.make_archive
        zip_filename = base_name + ".zip"
        base_len = len(base_dir)
        archive_util.mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

        log.info("creating '%s' and adding '%s' to it",
                 zip_filename, base_dir)

        if not dry_run:
            zip = zipfile.ZipFile(zip_filename, "w",
                                  compression=zipfile.ZIP_DEFLATED)

            for filename in self.msdeploy_files:
                log.info("adding '%s'" % filename)
                zip.write(filename, filename)

            for dirpath, dirnames, filenames in os.walk(base_dir):
                for name in filenames:
                    src_path = os.path.normpath(os.path.join(dirpath, name))
                    dst_path = dist_name + src_path[base_len:]
                    if os.path.isfile(src_path):
                        zip.write(src_path, dst_path)
                        log.info("adding '%s'" % dst_path)
            zip.close()

        return zip_filename
