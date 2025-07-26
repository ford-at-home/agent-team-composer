from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="github-backlog-generator",
    version="1.0.0",
    author="Ford",
    author_email="ford@flyingpig.ai",
    description="CLI tool to transform GitHub repo READMEs into ordered project backlogs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ford-at-home/agent-team-composer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.20.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
        "PyGithub>=2.1.1",
        "pydantic>=2.5.0",
        "requests>=2.31.0",  # Added from requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "github-backlog=github_backlog_generator.cli:cli",
            "github-backlog-generator=github_backlog_generator.cli:cli",  # Alternative name
        ],
    },
    keywords="github backlog project-management cli developer-tools",
    project_urls={
        "Bug Reports": "https://github.com/ford-at-home/agent-team-composer/issues",
        "Source": "https://github.com/ford-at-home/agent-team-composer",
    },
)