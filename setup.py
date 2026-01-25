from pathlib import Path

from setuptools import setup, find_packages


def load_requirements(file_name: Path) -> list[str]:
    if not file_name.is_file():
        return []

    with file_name.open('r', encoding='utf-8') as file:
        return file.read().splitlines()


setup(
    name='ehandlers',
    version='0.4.0',
    packages=find_packages(),
    install_requires=load_requirements(Path('requirements.txt')),
    author='Vlad Barmichev',
    author_email='barmichev@gmail.com',
    description='Collection of exception handlers',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Shindler7/ehandler',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
