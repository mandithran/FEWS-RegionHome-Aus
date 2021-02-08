# http://go.chriswarrick.com/entry_points

from setuptools import setup

setup(
    name="importSurge",
    version="0.1.0",
    packages=["importSurge"],
    install_requires=[
        "numpy","pandas"
    ],
    entry_points={
        "console_scripts": [
            "importSurge = importSurge.__main__:main"
        ]
    },
)