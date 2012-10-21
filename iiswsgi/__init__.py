"""IIS WSGI Application support"""

from iiswsgi import build
from iiswsgi import bdist


cmdclass = dict(build_msdeploy=build.build_msdeploy,
                bdist_msdeploy=bdist.bdist_msdeploy)
