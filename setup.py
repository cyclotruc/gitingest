from setuptools import setup, find_packages

setup(
    name="gitingest",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
    ],
    entry_points={
        "console_scripts": [
            "gitingest=src.cli:main",
        ],
    },
    python_requires=">=3.6",
    author="Your Name",
    description="A tool to analyze and create text dumps of git repositories",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
) 