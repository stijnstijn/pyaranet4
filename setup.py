import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyaranet4",
    version="1.0.3",
    author="Stijn Peeters",
    author_email="a4@stijnpeeters.nl",
    description="A cross-platform Python interface for the Aranet4 CO₂ meter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stijnstijn/pyaranet4",
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={'console_scripts': ['pyaranet4=pyaranet4.__main__:main']},
    license="MIT",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)