import os

from distutils.command import build
from distutils.command import sdist
from distutils import archive_util


class MSDeployBuild(build.build):
    """Build an MSDeploy zip package for installation into IIS."""

    def initialize_options(self):
        """Be more discriminating about what to prune."""
        build.build.initialize_options(self)
        self.build_base = 'build/'


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

cmdclass = dict(build=MSDeployBuild,
                sdist=MSDeploySDist)
