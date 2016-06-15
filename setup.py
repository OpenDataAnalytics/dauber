from setuptools import setup

setup(name='ansible_coach',
      version='0.0.0',
      description='APACHE licensed project for running ansible playbooks',
      long_description=open('README.md').read().strip(),
      author='Kitware Inc',
      author_email='chris.kotfila@kitware.com',
      url='',
      py_modules=['ansible_coach'],
      test_suite="tests.test_suite",
      install_requires=[],
      license='Apache 2.0',
      zip_safe=False,
      keywords='ansible')
