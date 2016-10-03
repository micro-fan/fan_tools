from setuptools import setup, find_packages

setup(
    name='tipsi_tools',
    packages=find_packages(),
    version='0.10.0',
    description='Various python stuff: testing, aio helpers, etc',
    author='cybergrind',
    author_email='cybergrind@gmail.com',
    keywords=['testing', 'asyncio'],
    classifiers=[],
    install_requires=[
        'pyyaml>=3.12',
    ],
    entry_points={
        'console_scripts': [
            'tipsi_env_yaml=tipsi_tools.scripts.tipsi_env_yaml:main',
        ]
    },
)
