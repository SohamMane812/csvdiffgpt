from setuptools import setup, find_packages

setup(
    name="csvdiffgpt",
    version="0.1.0",
    description="A package for analyzing CSV files using LLMs",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Soham Mane",
    author_email="sohammane01@gmail.com",
    url="https://github.com/SohamMane812/csvdiffgpt",
    project_urls={
        "Homepage": "https://github.com/SohamMane812/csvdiffgpt",
        "Bug Tracker": "https://github.com/SohamMane812/csvdiffgpt/issues",
    },
    license="Apache-2.0",
    packages=find_packages(include=["csvdiffgpt", "csvdiffgpt.*"]),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "gemini": ["google-generativeai>=0.8.5"],
        "claude": ["anthropic>=0.5.0"],
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "isort>=5.9.1",
            "mypy>=0.812",
            "types-PyYAML",
        ],
        "all": [
            "openai>=1.0.0",
            "google-generativeai>=0.8.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "csvdiffgpt=csvdiffgpt.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
