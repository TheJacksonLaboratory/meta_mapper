# meta_mapper
Map fields in existing metadata documents to those in a new, standardized template.

## Description
The meta_mapper will take a given directory in the archive and search it for existing metadata files. From the given path, it will attempt to determine the type of data being examined - gt_delivery, faculty, microscopy, etc. When that's established, it will look for specific metadata json files, read them, and try to map their contents to the fields in a provided standardized template. 

## Setup / Run Environment

To use the meta_mapper, the JAX github repository [system_groups_finder](https://github.com/TheJacksonLaboratory/system_groups_finder) **MUST** be installed in a virtual environment that uses python 3.6+. T On most of our servers, you can do this with the following commands:
```
$ python3 -m venv myenv
$ source myenv/bin/activate
(myenv) $ python -m pip install git+https://<github_username>:<access_token>@github.com/TheJacksonLaboratory/system_groups_finder
```
