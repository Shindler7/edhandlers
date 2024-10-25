from setuptools import setup, find_packages


def load_requirements(file_name) -> list[str]:
    with open(file_name, 'r') as file:
        return file.read().splitlines()


setup(
    name='ehandlers',
    version='0.3.2b',
    packages=find_packages(),
    install_requires=load_requirements('requirements.txt'),
    author='Vlad Barmichev',
    author_email='barmichev@gmail.com',
    description='Collection of exception handlers',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Shindler7/ehandler',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)

