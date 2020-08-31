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


## The configuration file

The mapper is highly configurable, and as such, most of it's behavior is controlled within the [meta_mapper_config](https://github.com/TheJacksonLaboratory/meta_mapper/blob/master/meta_mapper/meta_mapper_config.cfg) file. Please see the comments in the file for more details.


## Usage
The meta_mapper has a module name MetaMapper, which has two public methods: 
```

     |  create_new_document(self, archive_dir)
     |      Build a new metadata document from jsons in an archive directory.
     |
     |      The document will contain keys in the template, with values populated by searching
     |      the jsons in the given directory.
     |
     |      Parameters: archive_dir (str): Absolute path to a directory in the archive.
     |
     |      Returns: new metadata document as a dict.
     |
     |  get_blank_template(self)
     |      Just return a fresh copy of the template.
     |
     |      Parameters: None
     |
     |      Returns: (dic): A dict with all the keys of the template, but no values
     |
```
