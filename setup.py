from setuptools import setup, find_packages

def parse_requirements(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line and not line.startswith("#")]
requirements = parse_requirements('requirements.txt')

setup(
    name='pyalma',
    version='0.1.0',
    packages=find_packages(where='src'),  # Tells setuptools to find packages under 'src'
    package_dir={'': 'src'},  # Tells setuptools that the source code is in 'src'
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pyalma-cli = pyalma.cli:main',  # Entry point for the CLI command
        ],
    },
)
