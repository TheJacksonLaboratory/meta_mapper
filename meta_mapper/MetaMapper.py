"""
    Given a metadata file in an old format, and an archived.json file,
    populate a document in a new format.
"""

import configparser
from datetime import datetime
import dateutil.parser as date_parser
import json
import os
from pathlib import Path
import re
import subprocess

from system_groups_finder import SystemGroupsFinder

class MetaMapper:

    """
    Given a metadata file in an old format, and an archived.json file,
    populate a document in a new format.
    """

    def __init__(self):

        """

        Load new document example and get field mapping from config file.

        """

        # Get the source directory where this script resides. Look for a config file in it.
        root_dir = os.path.dirname(os.path.realpath(__file__))
        config_filename = str(Path(root_dir, "meta_mapper_config.cfg"))
        assert os.path.isfile(config_filename)

        self.config = configparser.ConfigParser()
        self.config.read(config_filename)

        # Get all the keys in the new format, discarding the values in the template's example file.
        template_filename = str(Path(root_dir, self.config["format"]["template"]))
        assert os.path.isfile(template_filename)
        with open (template_filename) as f:
            self.template = dict.fromkeys(json.load(f).keys(), None)
        self.user_metadata_key = self.config["format"]["user_metadata_key"]        
        self.defaults_tag = self.config["format"]["defaults_tag"]

        # The categories section of the config maps file path patterns to the various 
        # kinds of metadata. Patterns to be excluded are found in a comma-delimited list in the config.
        self.categories = self.config["categories"]
        self.exclude_patterns = self.categories["exclude_patterns"].split(',')

        # The dates section tells uys how to recognize date fields and how to format them.
        self.date_key_pattern = self.config["dates"]["date_key_pattern"]
        self.date_format = self.config["dates"]["date_format"]
 
        # Get an instance of the SystemGroupsFinder
        self.system_groups_finder = SystemGroupsFinder.SystemGroupsFinder()
        self.system_groups_key = self.config["format"]["system_groups_key"]

        # Save the name of the user_id and manager_user_id key
        self.manager_user_id_key = self.config["format"]["manager_user_id_key"]
        self.user_id_key = self.config["format"]["user_id_key"]
        self.sgf_manager_userid = self.config["format"]["sgf_manager_user_id_key"]

        # Save the name of the date key
        self.date_key = self.config["format"]["date_key"]        

        # Save the name of the archive root
        self.archive_path_key = self.config["format"]["archive_path_key"]
        self.archive_root = self.config["format"]["archive_root"]
        
        # Save the name of the archived_size key
        self.archived_size_key = self.config["format"]["archived_size_key"]

        # Save the name of the archival status key and success message
        self.archival_status_key = self.config["format"]["archival_status_key"]
        self.archival_status_done_msg = self.config["format"]["archival_status_done_msg"]

        # Save the name of the source_path key
        self.source_path_key = self.config["format"]["source_path_key"]

        # Save the name of the directory name key
        self.dirname_key = self.config["format"]["dirname_key"]


    def create_new_document(self, archive_dir):

        """

        Build a new metadata document from jsons in an archive directory.

        The document will contain keys in the template, with values populated by searching 
        the jsons in the given directory.

        Parameters: archive_dir (str): Absolute path to a directory in the archive.

        Returns: new metadata document as a dict.

        """

        # Copy the template into the new doc that will be returned after it's populated. 
        new_doc = self.get_blank_template()

        # Find which kind of metadata to expect from the directory path.
        category_tag = self.__get_category_tag(archive_dir)
        if not category_tag:
            return # This kind of metadata is not yet handled.

        # Track whether we found a useable metadata document
        self.useable_doc_found = False

        # Seek and read any metadata docs in the directory named in the config file.
        for doc_tag, doc_filename in self.config["doc_names"].items():
            
            # If the directory name is part of the metadata filename, expand it.
            doc_filename = self.__expand_dirname_for_filename(doc_filename, archive_dir)

            # Load json doc with keys converted to snake_case.
            curr_doc = self.__get_curr_doc(archive_dir, doc_filename)
            if not curr_doc:
                # doc not found in this directory
                continue

            # Get the section of the config file to seek by combining the category and doc tags.
            section_tag = category_tag + '_' + doc_tag
            if section_tag not in self.config:
                # This kind of metadata doc is not yet handled for this category
                continue

            # We have found a useable doc
            self.useable_doc_found = True

            # Add vals from curr doc to new doc
            try:
                self.__add_vals_from_curr_doc(new_doc, section_tag, curr_doc)
            except ValueError as e:
                print(f"Key error for {archive_dir}:new_doc {str(e)}")
             
            # Tuck curr doc into user_data field, if specified in the config file.
            self.__add_user_metadata(new_doc, section_tag, curr_doc)

            # Add the system groups
            self.__add_groups_from_doc(new_doc, curr_doc)

        # Do nothing if the archive dir had no useable metadata document
        if not self.useable_doc_found:
            return None

        # Add archive_path if needed
        self.__add_archive_path(new_doc, archive_dir)

        # Add the archived size
        self.__add_archived_size(new_doc, archive_dir)

        # Add the archival status
        self.__add_archival_status(new_doc, archive_dir)

        # Add date if needed
        self.__add_date(new_doc, archive_dir)

        # Add system groups if needed
        self.__add_groups_from_path(new_doc, archive_dir)

        # For now, limit any docs with multiple source paths to just the first one
        srcs = new_doc[self.source_path_key]
        if type(srcs) == list and len(srcs) > 0:
            new_doc[self.source_path_key] = srcs[0]

        # Add any known constants
        self.__add_default_vals(new_doc)

        return new_doc


    def get_blank_template(self):

        """

        Just return a fresh copy of the template.

        Parameters: None
        
        Returns: (dic): A dict with all the keys of the template, but no values

        """

        return self.template.copy()        



    """
    
    PRIVATE METHODS

    """

    def __add_archive_path(self, new_doc, archive_dir):

        """

        Add a given archive directory to the doc if it doesn't already have an archive_path
        
        Parameters:
            new_doc (dict): The new dictionary being populated.
            archive_dir (str): A directory in the archive

        Returns: None
        
        """

        # If the doc already has an archive_path, do nothing
        if new_doc[self.archive_path_key]:
            return

        # If the directory doesn't start with the archive root or isn't a valid directory, do nothing.
        if not archive_dir.startswith(self.archive_root) or not os.path.isdir(archive_dir):
            return
        # Clear any saved sub-dictionaries from previous documents
        self.sub_dicts = {}

        new_doc[self.archive_path_key] = archive_dir


    def __add_archived_size(self, new_doc, archive_dir):

        """

        Add the given archive directory's disk usage size in bytes to the doc.

        Parameters:
            new_doc (dict): The new dictionary being populated.
            archive_dir (str): A directory in the archive

        Returns: None

        """

        # If the directory doesn't start with the archive root or isn't a valid directory, do nothing.
        if not archive_dir.startswith(self.archive_root) or not os.path.isdir(archive_dir):
            return

        archived_size= int(subprocess.check_output(
            ["du", "-sb", archive_dir]).split()[0].decode("utf-8"))

        new_doc[self.archived_size_key] = archived_size


    def __add_archival_status(self, new_doc, archive_dir):

        """

        Mark the archival_status completed if this directory is already in the archive and has metadata.

        Parameters:
            new_doc (dict): The new dictionary being populated.
            archive_dir (str): A directory in the archive

        Returns: None

        """

        # If the directory doesn't start with the archive root or isn't a valid directory, do nothing.
        if not archive_dir.startswith(self.archive_root) or not os.path.isdir(archive_dir):
            return

        # If it doesn't have metadata, do nothing (technically, if it doesn't have metadata, control flow
        # won't reach this point, but that could potentially change in the future.)
        if not self.useable_doc_found:
            return

        new_doc[self.archival_status_key] = self.archival_status_done_msg


    def __add_date(self, new_doc, archive_dir):

        """

        If the doc doesn't have a date, use the last modified date of the given archive dir.

        Parameters:
            new_doc (dict): The new dictionary being populated.
            archive_dir (str): A directory in the archive

        Returns: None

        """

        # If the doc already has a date, do nothing
        if new_doc[self.date_key]:
            return        

        # If the directory doesn't start with the archive root or isn't a valid directory, do nothing.
        if not archive_dir.startswith(self.archive_root) or not os.path.isdir(archive_dir):
            return

        # Get the directory's lat modified, convert to datetime as a string
        mod_date = str(datetime.fromtimestamp(os.path.getmtime(archive_dir)))

        # Convert the date to the desired format and assign it to the new_doc's date key
        new_doc[self.date_key] = self.__get_converted_date(mod_date)
        

    def __add_default_vals(self, new_doc):

        """

        Parse defaults from config, add to new doc.

        Parses the default values in the "default_vals" section of the config file. Values in that section are
        actually pairs delimited by a colon, in the form type:val. E.g., "int:0" means the value would
        be zero as an integer, while "str:None" means the value is the string "None", not just None.
        Will not add the value if the doc aalready has one.

        Parameters:
            new_doc (dict): The new dictionary being populated.

        Returns: None

        """

        for curr_key, packed_val in self.config[self.defaults_tag].items():

            # Don't add the vaule if the doc already has a value for this key.
            if curr_key in new_doc and new_doc[curr_key]:
                continue

            val_type,val = packed_val.split(':')

            if val_type == "int":
                new_doc[curr_key] = int(val)

            if val_type == "float":
                new_doc[curr_key] = float(val)

            if val_type == "str":
                new_doc[curr_key] = str(val)

            if val_type == None:
                new_doc[curr_key] = None

            if val_type == "list":
                new_doc[curr_key] = []

            if val_type == "dict":
                new_doc[curr_key] = dict()

            if val_type == bool:
                if val.lower() == "true":
                    new_doc[curr_key] = True
                else:
                    new_doc[curr_key] = False


    def __add_groups_from_doc(self, new_doc, curr_doc):

        """

        Try to determine system_groups from the current document.

        Parameters:
            new_doc (dict): The new dictionary being populated.
            curr_doc (dic)): 

        Returns: None

        """

        # Scan the whole doc to find info about groups.
        groups = self.system_groups_finder.get_groups_from_entire_doc(curr_doc)

        # If we found None, check any sub-dicts we may have saved.
        if not groups and self.sub_dicts:
            for key, sub_dict in self.sub_dicts.items():
                groups = self.system_groups_finder.get_groups_from_entire_doc(sub_dict)
                if groups:
                    break 

        # Assign whatever we found, even if it's None.
        new_doc[self.system_groups_key] = groups


    def __add_groups_from_path(self, new_doc, archive_dir):

        """

        If the doc doesn't have a val for system_groups, try to find one from the archive path
        Parameters:
            new_doc (dict): The new dictionary being populated.
            archive_dir (str): A directory in the archive

        Returns: None

        """

        # If the doc already has groups, do nothing
        if new_doc[self.system_groups_key]:
            return

        # If the directory doesn't start with the archive root or isn't a valid directory, do nothing.
        if not archive_dir.startswith(self.archive_root) or not os.path.isdir(archive_dir):
            return

        new_doc[self.system_groups_key] = self.system_groups_finder.search_archived_path_for_group_name(archive_dir, "system_groups")


    def __add_user_metadata(self, new_doc, section_tag, curr_doc):

        """
        
        Tuck an old metadata doc into the user_metadata field of the new doc.

        Parameters:
            new_doc (dict). The new document being created.
            old_doc (dict). The old document being scanned.

        Returns: None

        """

        # If the user_data field is set to True in the config section for the old metadata
        # file, tuck its contents into the user_data field of the new doc.
        try:
            if self.config[section_tag][self.user_metadata_key].lower() == "true":
                new_doc[self.user_metadata_key] = curr_doc
        except KeyError as e:
            # user_metadata key not found in the section of the config for this doc. Do nothing.
            pass


    def __add_vals_from_curr_doc(self, new_doc, section_tag, curr_doc):

        """ALL_CT_ARCHIVE
        Add values to the new doc from fields in the current doc specified in the config file.

        Parameters:
            new_doc: (dict):     The new document being created.
            category_tag: (str): The category of metadata this document matches.
            doc_tag: (str):      The section tag in the config file for this document.
            curr_doc: (dict):    The current document loaded from a json file.

        Returns: new_doc as dict, with vals added, if any.

        """

        # Check this doc's section in the config file to determine which of its keys we want.
        for template_key, doc_keys in self.config[section_tag].items():
            # Document keys can be a comma-separated list. Split and strip off whitespace.
            for doc_key in [x.strip() for x in doc_keys.split(',')]:
                # Hack: we don't want to process the user_metadata key here.
                if template_key == self.user_metadata_key:
                    continue

                # Get the value of the doc_key in the current document. If None, skip.
                curr_doc_val = self.__get_curr_doc_val(curr_doc, doc_key)
                if not curr_doc_val:
                    continue

                # If the new doc already has a value for this key, but the curr doc has a different
                # value, and both are not None, raise a ValueError (To be caught and logged, not to
                # crash the program.) 
                if ((template_key in new_doc and new_doc[template_key] != None) and
                    curr_doc_val != None and 
                    new_doc[template_key] != curr_doc_val):
                    raise ValueError(f"Warning: conflicting values for {template_key}")
 
                # If the new doc doesn't already have a value for this key, use the value from the
                # current doc.

                if template_key in new_doc and new_doc[template_key] == None:

                    # Any dates must converted into a uniform format
                    if re.match(self.date_key_pattern, template_key):
                        curr_doc_val = self.__get_converted_date(curr_doc_val)

                    # Manager user_id must be looked up in the SystemGroupsFinder
                    if template_key == self.manager_user_id_key or template_key == self.user_id_key:
                        target_key = self.sgf_manager_userid

                        new_doc[template_key] = self.system_groups_finder.get_other_info_from_group(
                            target_key, curr_doc_val, target_key)

                    else:

                        new_doc[template_key] = curr_doc_val


    def __expand_dirname_for_filename(self, doc_filename, archive_dir):

        """

        If the filename has the "dirname" string in it, expand it with the actual directory name.

        Parameters:
            doc_filename: (str): The filename of the metadata document.
            archive_dir: (str): 

        Returns:
            doc_filename: (str):  The filename of the metadata document, expanded if needed

        """

        if not doc_filename.startswith(self.dirname_key):
            return doc_filename

        # Get the last part of the directory path, replace in filename
        basedir = os.path.basename(os.path.normpath(archive_dir))
        doc_filename = doc_filename.replace(self.dirname_key, basedir)
        return doc_filename


    def __get_category_tag(self, archive_dir):

        """

        Match the directory path to category of metadata.

        Match the directory path against each pattern in the categories map to
        determine which kind of metadata we should expect.

        Parameters: archive_dir (str):         

        Returns: category_tag as a string, or None if no match.

        """

        # Ignore any directory that matches any of the exclude patterns
        for exclude_pattern in self.exclude_patterns:
            if re.search(exclude_pattern, archive_dir):
                return None

        for pattern, category_tag in self.categories.items():
            # Config parser loads keys as lowercase by default. Easiest fix is a 
            # case-insensitive match.
            if re.match(pattern, archive_dir, re.IGNORECASE):
                return category_tag

        return None
      

    def __get_converted_date(self, init_date):

        """

        Convert date strings into a uniform format.

        Parameters:
            init_date (str): The date string we're starting with.

        Returns:
            new_date (str): The date string in the desired format.

        """

        new_dt = date_parser.parse(init_date).replace(hour=12, minute=0, second=0, microsecond=0)
        new_dt_str = new_dt.strftime(self.date_format)
        return new_dt_str


    def __get_curr_doc(self, archive_dir, doc_filename):

        """"
        
        Seek the given file and load it as json with snake_case keys.

        Parameters:
            archive_dir (str): Absolute path of the directory being searched.
            doc_filename (str): Name of metadata json file to look for in the directory.

        Returns: dict of file contents with keys in snake_case, or None if not found.

        """

        # Clear any saved sub-dictionaries from previous documents
        self.sub_dicts = {}

        # Look for doc
        doc_filepath = os.path.join(archive_dir, doc_filename)
        if not os.path.isfile(doc_filepath):
            # Directory does not have a metadata doc with this name.
            return None

        # Load as json
        try:
            with open(doc_filepath) as f:
                curr_doc = json.load(f)
        except:
            # A rare few of the jsons in the archive were hand-made and malformed. Skip them.
            return None

        # Convert keys to snake_case using list comprehension
        curr_doc = { self.__to_snake_case(k): v for k, v in curr_doc.items() }

        return curr_doc
        

    def __get_curr_doc_val(self, curr_doc, doc_key):

        """

        Get the value for a key in a given document.

        Parameters:
            curr_doc (dict): The current document.







            doc_key (str): The document key from the config file.

        Returns: Value of the key in the doc as a str, or None if key not in doc.

        """

        # If the key we want is nested in a sub-dictionary within the document, this will
        # be denoted by a '>' symbol in the doc_key. 

        if '>' not in doc_key:
            # No nesting involved, just get the value.
            try:
                return curr_doc[doc_key]
            except KeyError:
                # doc_key not in current document
                return None            

        # From here we're dealing with a nested dict. For now, we'll only handle one
        # level of nesting. Split on the '>' and trim any whitespace.
        top_key, sub_key = [val.strip() for val in doc_key.split('>')]
        
        # If the curr doc doesn't actually have the top_key, or it does but the value isn't
        # a dictionary, stop.
        if top_key not in curr_doc or type(curr_doc[top_key]) != dict:
            return None

   
        # We'll need to load the sub-dict with alll its keys in snake_case. Also, we may need
        # this sub_dict on subsequent calls, so we want to save the results.
        if top_key not in self.sub_dicts:
            self.sub_dicts[top_key] = { self.__to_snake_case(k): v for k, v in curr_doc[top_key].items() }        

        val = self.sub_dicts[top_key][sub_key]
        return val


    def __to_snake_case(self, val):

        """

        Convert a string to snake_case.

        Parameters: val (str): string to be converted.

        Returns: input string in snake_case.

        """

        # Insert an underscore after every lower case letter that is immediately followed
        # by an uppercase letter. 
        new_val = val[0].lower()
        for i in range(1, len(val)):
            if val[i].isupper() and val[i-1].islower():
                new_val += '_'
            new_val += val[i].lower()
        
        return new_val
