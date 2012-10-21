import os
import zipfile

from distutils.command import bdist_dumb
from distutils import archive_util

# TODO upload

from iiswsgi import build


class bdist_msdeploy(bdist_dumb.bdist):
    """Create an MSDeploy zip package for installation into IIS."""

    msdeploy_files = (build.build_msdeploy.manifest_name, 'Parameters.xml')

    def make_distribution(self):
        """Minimize path lenght to avoid windows issues."""
        # Copied from distutils.command.sdist.sdist.make_distribution

        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_version()
        base_name = os.path.join(
            self.dist_dir, self.distribution.get_fullname())

        self.make_release_tree(base_dir, self.filelist.files)
        archive_files = []              # remember names of files we create
        # tar archive must be created last to avoid overwrite and remove
        if 'tar' in self.formats:
            self.formats.append(self.formats.pop(self.formats.index('tar')))

        for fmt in self.formats:
            file = self.make_archive(base_name, fmt, base_dir=base_dir,
                                     owner=self.owner, group=self.group)
            archive_files.append(file)
            self.distribution.dist_files.append(('sdist', '', file))

        self.archive_files = archive_files

        if not self.keep_temp:
            bdist_dumb.dir_util.remove_tree(base_dir, dry_run=self.dry_run)

    def make_archive(self, base_name, format, root_dir=None, base_dir=None,
                     owner=None, group=None):
        """Don't inlcude the version number for MSDeploy packages."""
        dry_run = self.dry_run
        dist_name = self.distribution.get_name()

        # Copied from distutils.command.sdist.sdist.make_archive
        zip_filename = base_name + ".zip"
        base_len = len(base_dir)
        archive_util.mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

        archive_util.log.info("creating '%s' and adding '%s' to it",
                 zip_filename, base_dir)

        if not dry_run:
            zip = zipfile.ZipFile(zip_filename, "w",
                                  compression=zipfile.ZIP_DEFLATED)

            for filename in self.msdeploy_files:
                archive_util.log.info("adding '%s'" % filename)
                zip.write(filename, filename)

            for dirpath, dirnames, filenames in os.walk(base_dir):
                for name in filenames:
                    src_path = os.path.normpath(os.path.join(dirpath, name))
                    dst_path = dist_name + src_path[base_len:]
                    if os.path.isfile(src_path):
                        zip.write(src_path, dst_path)
                        archive_util.log.info("adding '%s'" % dst_path)
            zip.close()

        return zip_filename
