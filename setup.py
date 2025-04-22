from setuptools import setup, find_packages

setup(
    name="science-agent-framework",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=2.0.0",
        "scipy>=1.14.1",
        "pandas>=2.2.2",
        "h5py>=3.12.1",
        "openai",
        "docstring_parser",
        "mcp",
        "requests_oauthlib",
        "pymatgen",
        "PyPDF2",
        "tiktoken",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Science Agent Framework for scientific computing and analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/science-agent-framework",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 