import codecs
import os.path

from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("swep", "\n")
    buf = []
    for fl in filenames:
        with codecs.open(os.path.join(HERE, fl), "rb", encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

def read_requirements(filename):
    reqs_txt = read(filename)
    parsed = reqs_txt.split("\n")
    parsed = [r.split("==")[0] for r in parsed]
    return [r for r in parsed if len(r) > 0]

setup(name='sviit',
    version='0.1',
    description='Spectravideo 328 utilities',
    long_description=read("README.md"),
    classifiers=[
    'Development Status :: 2 - Pre-Alpha',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.8',
    'Topic :: System :: Emulators',
    'Topic :: Utilities',
    ],
    url='https://github.com/Yarin78/sviit',
    author='Jimmy Mårdell',
    author_email='jimmy.mardell@gmail.com',
    license='MIT',
    packages=['sviit'],
    zip_safe=False,
    install_requires=read_requirements("requirements.txt"),
    entry_points = {
        'console_scripts': ['sviit=sviit.cli:main']
    }
)
