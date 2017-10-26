from setuptools import find_packages, setup

with open('tipsi_tools/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break


setup(
    name='tipsi_tools',
    packages=find_packages(exclude=('tests', 'django_tests.*', 'django_tests')),
    version=version,
    description='Various python stuff: testing, aio helpers, etc',
    author='cybergrind',
    author_email='cybergrind@gmail.com',
    url='http://github.com/tipsi/tipsi_tools',
    keywords=['testing', 'asyncio'],
    install_requires=[
        'pyyaml>=3.12',
        'python-json-logger>=0.1.5',
    ],
    tests_require=[
        'pytest==3.1.3',
    ],
    entry_points={
        'console_scripts': [
            'tipsi_env_yaml=tipsi_tools.scripts.tipsi_env_yaml:main',
            'tipsi_ci_script=tipsi_tools.scripts.tipsi_ci_script:main',
            'tipsi_wait=tipsi_tools.scripts.tipsi_tools_wait:main',
            'run_filebeat=tipsi_tools.scripts.run_filebeat:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
)
