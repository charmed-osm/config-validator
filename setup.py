"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import os.path
import re


import setuptools


def get_long_description():
    with open("README.md", "r") as fh:
        return fh.read()


def get_version():
    with open(os.path.join("config_validator", "__init__.py"), "r") as fh:
        pkg = fh.read()

    LIBAPI = int(re.search(r"""(?m)^LIBAPI\s*=\s*(\d+)""", pkg).group(1))
    LIBPATCH = int(re.search(r"""(?m)^LIBPATCH\s*=\s*(\d+)""", pkg).group(1))
    return f"{LIBAPI}.{LIBPATCH}"


with open("requirements.txt") as f:
    install_requires = [req for req in f.read().splitlines() if "==" in req]

    setuptools.setup(
        name="config-validator",
        version=get_version(),
        author="David García",
        author_email="david.garcia@canonical.com",
        maintainer="Canonical",
        description="Lightweight config validator",
        long_description=get_long_description(),
        long_description_content_type="text/markdown",
        url="https://github.com/charmed-osm/config-validator",
        packages=["config_validator"],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
        ],
        keywords="charm osm",
        project_urls={
        },
        python_requires=">=3.8",
        install_requires=install_requires,
    )
