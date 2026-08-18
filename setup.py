from pathlib import Path

from setuptools import find_packages, setup

import ehandlers

REQUIREMENTS: Path = Path('requirements.txt')
README: Path = Path('README.md')


def read_file(file: Path) -> str:
    """Загрузка данных из переданного файла."""
    return file.read_text(encoding='utf-8')


setup(
    name='ehandlers',
    version=ehandlers.__version__,
    author=ehandlers.__author__,
    author_email=ehandlers.__email__,
    packages=find_packages(),
    install_requires=read_file(REQUIREMENTS).splitlines(),
    description='Структурированная обработка исключений с логированием',
    long_description=read_file(README),
    long_description_content_type='text/markdown',
    url='https://github.com/Shindler7/edhandlers',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)
