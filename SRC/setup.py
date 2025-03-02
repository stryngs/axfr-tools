#!/usr/bin/python3
# Copyright (C) 2016 stryngs.

from setuptools import setup

setup(
    name = 'axfr-tools',
    version = '1.2.2',
    author = 'stryngs',
    author_email = 'info@127.0.0.1',
    packages = ['axfr_tools', 'axfr_tools.lib'],
    include_package_data = True,
    url = 'https://github.com/stryngs/axfr-tools',
    license ='GNU General Public License v3 or later (GPLv3+)',
    keywords = 'axfr zone-transfer zone transfer dig dns nslookup',
    description='Zonefile Transfer Toolkit'
)
