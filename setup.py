#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil 
import os
from setuptools import setup, find_packages

import FERG
 
setup(
    name='FERG',
    version=FERG.__version__,
    packages=find_packages(),
    author="FredThx",
    author_email="FredThx@gmail.com",
    description="Une bibliotheque pour Gerer - analyse les energies d'un maison individuelle",
    long_description=open('README.md').read(),
    install_requires=[], #TODO
    include_package_data=True,
    url='',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7"
    ],
    # entry_points = {
        # 'console_scripts': [
            # 'proclame-sm = sm_lib.core:proclamer',
        # ],
    # },
    license="WTFPL",
)
try:
	os.mkdir('/opt/FERG')
except OSError:
	pass
shutil.copy('comptage.py', '/opt/FERG')
if not os.path.exists('/opt/FERG/config.py'):
	shutil.copy('config.py', '/opt/FERG')
shutil.copy('comptage', '/etc/init.d')
shutil.copy('comptage.sh', '/usr/bin')
os.system('sudo chmod +x /etc/init.d/comptage')
os.system('sudo chmod +x /usr/bin/comptage.sh')
os.system('sudo update-rc.d comptage defaults 99')

shutil.copy('rf_temp_io.py', '/opt/FERG')
shutil.copy('rf_temp_io', '/etc/init.d')
shutil.copy('rf_temp_io.sh', '/usr/bin')
os.system('sudo chmod +x /etc/init.d/rf_temp_io')
os.system('sudo chmod +x /usr/bin/rf_temp_io.sh')
#os.system('sudo update-rc.d rf_temp_io defaults 99')

shutil.copy('chk_alertes.py', '/opt/FERG')
os.system('sudo chmod +x /opt/FERG/chk_alertes.py')
