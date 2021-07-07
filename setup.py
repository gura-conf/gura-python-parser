from setuptools import setup
import gura

with open("README.md") as readme_file:
    readme_string = readme_file.read()

setup(
    name='gura',
    packages=['gura'],
    version=gura.__version__,
    license='MIT',
    description='A Gura format parser',
    long_description=readme_string,
    long_description_content_type='text/markdown',
    author='JWare',
    author_email='jware.organization@gmail.com',
    url='https://github.com/gura-conf/gura-python-parser',
    download_url='https://github.com/gura-conf/gura-python-parser/archive/refs/tags/1.2.0.tar.gz',
    keywords=['Gura', 'parser', 'loads', 'dumps', 'encode', 'decode'],
    install_requires=[
        'wheel'
    ],
    classifiers=[
        # Options: "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
