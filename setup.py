from setuptools import setup, find_packages

setup(
    name="material-compute-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "pandas>=2.2.2",
        "h5py>=3.12.1",
        "openai",
        "docstring_parser",
        "mcp",
        "requests_oauthlib",
        "pymatgen",
        "PyPDF2",
        "tiktoken",
        "sqlalchemy",
        "googlemaps",
        "camel-ai[model_platforms]",
        "colorama",
        "google-adk",
        "litellm"
    ],
    author="Lin Hang",
    author_email="linhang@dp.tech",
    description="Agent demo for scientific computing and analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 
