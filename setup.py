from setuptools import find_packages, setup

with open('fan_tools/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break

with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

SANIC = 'sanic'

setup(
    name='fan_tools',
    packages=find_packages(exclude=('tests', 'django_tests.*', 'django_tests')),
    version=version,
    description='Various python stuff: testing, aio helpers, etc',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='cybergrind',
    author_email='cybergrind@gmail.com',
    url='http://github.com/micro-fan/fan_tools',
    keywords=['testing', 'asyncio'],
    install_requires=['pyyaml>=3.12', 'python-json-logger>=0.1.5'],
    extras_require={
        'doc_utils': [
            'rest_framework_dyn_serializer>=1.3.*',
            'docutils',
            'djangorestframework==3.12.*',
        ],
        'logging': ['safe-logger>=1.2.1', 'python-json-logger==0.1.7'],
        'aio_utils': ['aiopg', 'psycopg2-binary'],
        'monitoring': [SANIC, 'starlette'],
        's3_backup': ['boto3'],
        'gcloud_backup': ['google-cloud-storage'],
        'gitlab_monitoring': ['python-gitlab==1.0.2', SANIC],
        'image_utils': ['Pillow'],
    },
    tests_require=['pytest==3.1.3'],
    entry_points={
        'console_scripts': [
            'fan_env_yaml=fan_tools.scripts.fan_env_yaml:main',
            'fan_ci_script=fan_tools.scripts.fan_ci_script:main',
            'fan_wait=fan_tools.scripts.fan_tools_wait:main',
            'run_filebeat=fan_tools.scripts.run_filebeat:main',
            'doc_serializer=fan_tools.doc_utils.fan_sphinx.dyn:main',
            'fan_s3_backup=fan_tools.backup.s3:main',
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
)
