"""IIS WSGI Application support"""

from iiswsgi import build_msdeploy
from iiswsgi import install_msdeploy
from iiswsgi import bdist_msdeploy


cmdclass = dict(build_msdeploy=build_msdeploy.build_msdeploy,
                install_msdeploy=install_msdeploy.install_msdeploy,
                bdist_msdeploy=bdist_msdeploy.bdist_msdeploy)
