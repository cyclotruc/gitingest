from setuptools import find_packages, setup

setup(
    name="gitingest",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "tiktoken",
    ],
    entry_points={
        "console_scripts": [
            "gitingest=gitingest.cli:main",
        ],
    },
    python_requires=">=3.6",
    author="Romain Courtois",
    author_email="romain@coderamp.io",
    description="CLI tool to analyze and create text dumps of codebases for LLMs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cyclotruc/gitingest",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
