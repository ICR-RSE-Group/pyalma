from setuptools import setup, find_packages

setup(
    name='sshconnection',
    version='0.1.0',
    packages=find_packages(where='src'),  # Tells setuptools to find packages under 'src'
    package_dir={'': 'src'},  # Tells setuptools that the source code is in 'src'
    install_requires=[
        #todo
    ],
    entry_points={
        'console_scripts': [
            'sshconnection-cli = sshconnection.cli:main',  # Entry point for the CLI command
        ],
    },
)
