# meta_mapper
Map fields in existing metadata documents to those in a new, standardized template.

## Description
The meta_mapper will take a given directory in the archive and search it for existing metadata files. From the given path, it will attempt to determine the type of data being examined - gt_delivery, faculty, microscopy, etc. When that's established, it will look for specific metadata json files, read them, and try to map their contents to the fields in a provided standardized template. 
