from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mkdocs-redoc-tag",
    version="0.1.0",
    author="Blueswen",
    author_email="blueswen.tw@gmail.com",
    url="https://blueswen.github.io/mkdocs-redoc-tag",
    project_urls={
        "Source": "https://github.com/Blueswen/mkdocs-redoc-tag",
    },
    keywords=["mkdocs", "plugin", "redoc", "openapi"],
    packages=find_packages(),
    license="MIT",
    description="A MkDocs plugin supports for add Redoc in page.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["beautifulsoup4>=4.11.1"],
    include_package_data=True,
    entry_points={
        "mkdocs.plugins": [
            "redoc-tag = mkdocs_redoc_tag.plugin:RedocPlugin",
        ]
    },
)
