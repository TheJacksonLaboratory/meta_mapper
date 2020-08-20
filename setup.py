
# Setup file needed for packaging

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="meta_mapper",
    version="1.0",
    author="Neil Kindlon",
    author_email="Neil.Kindlon@jax.org",
    description="Map keys and values from existing metadata docs to new template and populate it.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "system_groups_finder"
    ],
    dependency_links=[
        'git+https://github.com/TheJacksonLaboratory/system_groups_finder.git@master#egg=system_groups_finder-1.1'
    ],
    url="https://github.com/TheJacksonLaboratory/meta_mapper", 
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
