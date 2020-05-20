#APIs
import re
import os

from functools import reduce
import operator
import zipfile


def unzip_zipfile(zip_file, local_path):

    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(local_path)
    zip_ref.close()

    return zip_file.split('.')[0]


#Sub-functions of read_config_file
def get_by_path(root, items):
    """
    Access a nested object in root by item sequence.
    ref: https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    """
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """
    Set a value in a nested object in root by item sequence.
    ref: https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    """
    get_by_path(root, items[:-1])[items[-1]] = value


#Read the metadata file of Landsat
def read_config_file(zip_file, local_path):
    """
    Read a LandSat MTL config file to a Python dict
    """
    tile_path = unzip_zipfile(zip_file, local_path)

    # Read config
    r = re.compile("^(.*?)MTL.txt$")
    matches = list(filter(r.match, os.listdir(tile_path)))
    if matches:
        mtl_path = os.path.join(tile_path, matches[0])
    else:
        raise ValueError('No MTL config file found.')

    print('xml_path: {}'.format(mtl_path))

    f = open(mtl_path)

    group_path = []
    config = {}

    for line in f:
        line = line.lstrip(' ').rstrip() #remove leading whitespaces and trainling newlines

        if line.startswith('GROUP'):
            group_name = line.split(' = ')[1]
            group_path.append(group_name)
            set_by_path(root=config, items=group_path, value={})

        elif line.startswith('END_GROUP'):
            del group_path[-1]

        elif line.startswith('END'):
            continue

        else:
            key, value  = line.split(' = ')
            try:
                set_by_path(root=config, items=group_path + [key], value=json.loads(value))
            except Exception:
                set_by_path(root=config, items=group_path + [key], value=value)
    f.close()

    return config
