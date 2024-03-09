"setup.py - py2exe setup script for Pyro"

# Run "setup.py py2exe" to build the executable distribution.
# CMPM 146 | we can possibly try creating an executable for our finished product 
import shutil
import os
from distutils.core import setup
import py2exe

setup(console=["pyro.py"])

# Copy additional files:
additional_files = ["pyro-license.txt", "readme.txt"]
print("\nCopying additional files...")
for file in additional_files:
    print("\t%s" % file)
    shutil.copyfile(file, "dist/%s" % file)

# Copy source files:
print("\nCopying source files...")
source_files = [file for file in os.listdir('.')
                if file[-3:] == ".py"]
additional_source_files = ["install.nsi", "pyro-license.txt", "readme.txt"]
source_files.extend(additional_source_files)
try:
    os.mkdir("dist/source")
except OSError:
    pass
for file in source_files:
    print("\t%s" % file)
    shutil.copyfile(file, "dist/source/%s" % file)
