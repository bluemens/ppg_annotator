from setuptools import setup, find_packages

setup(
    name="annotator-tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "matplotlib",
        "pandas",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "annotator=annotatorkit.main:main"
        ]
    }
)
