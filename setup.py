from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(name='tdlink',
      version='0.2',
      description='Python Library for TDAmeritrade API',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/ysriram1/tdlink',
      author='Sriram Yarlagadda',
      author_email='ysriram@umich.edu',
      license='MIT',
      packages=['tdlink'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        ])
