import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="git-dummy",
    version="0.0.5",
    author="Jacob Stopak",
    author_email="jacob@initialcommit.io",
    description="Generate dummy Git repositories populated with the desired number of commits, branches, and structure.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://initialcommit.com/tools/git-dummy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "gitpython",
        "typer",
        "pydantic",
    ],
    keywords="git dummy generate populate repo repository",
    project_urls={
        "Homepage": "https://initialcommit.com/tools/git-dummy",
        "Source": "https://github.com/initialcommit-com/git-dummy",
    },
    entry_points={
        "console_scripts": [
            "git-dummy=git_dummy.__main__:app",
        ],
    },
    include_package_data=True,
)
