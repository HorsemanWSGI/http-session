import os
from setuptools import setup, find_packages


version = '0.1'


install_requires = [
    'biscuits',
    'itsdangerous',
]

tests_require = [
    'pytest',
]


setup(name='roughrider.session',
      version=version,
      description="Server-side session components for WSGI applications.",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='WSGI, Session',
      author='Souheil Chelfouh',
      author_email='trollfot@gmail.com',
      url='https://github.com/HorsemanWSGI/roughrider.session',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['roughrider',],
      include_package_data=True,
      zip_safe=False,
      tests_require=tests_require,
      install_requires=install_requires,
      extras_require={
          'test': tests_require,
      },
)
