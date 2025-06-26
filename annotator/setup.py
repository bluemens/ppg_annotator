from setuptools import setup, find_packages

setup(
    name="ppg-annotator",
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
    }, 
    author="Maximilian Comfere", 
    description="A GUI tool for PPG signal annotation", 
    include_package_data=True, 
    zip_safe=False,
)
