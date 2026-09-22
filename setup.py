import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="git-dummy",
    version="0.2.0",
    author="Jacob Stopak",
    author_email="jacob@initialcommit.io",
    description="Generate Git repositories with the history, remote and working-tree state you ask for: commits, branches, merges, tags, conflicts, stashes, a remote that is ahead or behind, and named scenarios.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://initialcommit.com/tools/git-dummy",
    packages=setuptools.find_packages(exclude=("tests",)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer",
        "pydantic_settings",
    ],
    extras_require={
        "yaml": ["pyyaml"],
    },
    keywords="git dummy generate populate repo repository fixture scenario",
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
