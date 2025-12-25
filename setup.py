"""
Setup script for BASE ORM

For backward compatibility with older pip versions.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="base-orm",
    version="3.0.0",
    author="BASE ORM Contributors",
    description="A professional, production-ready ORM for Python with SQLite support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/BASE_FRAMEWORK",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "base=base.cli:main",
        ],
    },
)
