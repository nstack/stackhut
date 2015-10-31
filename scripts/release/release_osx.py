# Script to release on OSX
# this is executed from the root toolkit src dir

import os
import sh




# run pyinstaller


# build pkg

"pkgbuild --root root --identifier com.stackhut.toolkit --version 0.6.0 --ownership recommended pkg1/output.pkg"

"productbuild --distribution distribution.xml --resources resources --package-path pkg1 --version 0.6.0 stackhut-toolkit.pkg"
