from setuptools import setup
from packagename.version import Version


setup(name='ansible_coach',
      version=Version('0.0.0').number,
      description='APACHE licensed project for running ansible playbooks',
      long_description=open('README.md').read().strip(),
      author='Kitware Inc',
      author_email='chris.kotfila@kitware.com',
      url='',
      py_modules=['ansible_coach'],
      install_requires=[],
      license='Apache 2.0',
      zip_safe=False,
      keywords='ansible')
