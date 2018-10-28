from setuptools import setup

setup(
    name='imapscan',
    version='0.1.0',
    description='Scan an IMAP folder for statistics',
    url='https://github.com/r1tger/imapscan',
    author='Ritger Teunissen',
    author_email='github@ritger.nl',
    packages=['imapscan'],
    # setup_requires=['pytest-runner'],
    # tests_require=['pytest>=3.0.0', 'freezegun'],
    install_requires=[
        'pandas'
    ],
    entry_points={'console_scripts': [
        'imapscan = imapscan.__main__:main',
    ]},
    zip_safe=False
)
