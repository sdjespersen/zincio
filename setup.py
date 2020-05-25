from setuptools import setup  # type: ignore

setup(
    name='pyzinc',
    url='https://github.com/sdjespersen/pyzinc',
    description='Parsing/dumping for Project Haystack Zinc file format',
    version='0.0.1',
    author='Scott Jespersen',
    license='MIT',
    packages=[
        'pyzinc',
    ],
    requires=[
        'numpy',
        'pandas',
    ],
)
