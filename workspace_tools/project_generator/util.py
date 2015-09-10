# Copyright 2014-2015 0xc0170
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
import locale
import shutil
import string
import subprocess
import logging

from project_generator.settings import ProjectSettings

FILES_EXTENSIONS = {
    'includes': ['h', 'hpp', 'inc'],
    'source_files_s': ['s','S','asm'],
    'source_files_c': ['c'],
    'source_files_cpp': ['cpp', 'cc'],
    'source_files_a': ['ar', 'a'],
    'source_files_obj': ['o', 'obj'],
    'linker_file': ['sct', 'ld', 'lin', 'icf'],
}
FILE_MAP = {v:k for k,values in FILES_EXTENSIONS.items() for v in values}
SOURCE_KEYS = ['source_files_c', 'source_files_s', 'source_files_cpp', 'source_files_a', 'source_files_obj']
VALID_EXTENSIONS = reduce(lambda x,y:x+y,[FILES_EXTENSIONS[key] for key in SOURCE_KEYS])

def rmtree_if_exists(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)

def unicode_available():
    return locale.getdefaultlocale()[1] == 'UTF-8'

def load_yaml_records(yaml_files):
    dictionaries = []
    for yaml_file in yaml_files:
        if yaml_file is None:
            return None
        if os.path.exists(yaml_file):
            f = open(yaml_file, 'rt')
            dictionaries.append(yaml.load(f))
        else:
            logging.critical("The file %s referenced in main yaml doesn't exist." % yaml_file)
            return None
    return dictionaries

class PartialFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
        except (IndexError, KeyError, AttributeError):
            first, _ = field_name._formatter_field_name_split()
            val = '{' + field_name + '}', first
        return val

def update(settings=ProjectSettings()):
    defdir_exists = True
    if not os.path.exists(settings.paths['definitions']):
        defdir_exists = False
        os.mkdir(settings.paths['definitions'])

    # For default, use up to date repo from github
    if not defdir_exists:
        # ToDo change to project_generaror URL before release
        #  and also make this a command line option
        #  and rethink strategy (git dancing vs tmp clone , rm and rename)
        cmd = ('git', 'clone', '--quiet',
                   'https://github.com/sarahmarshy/pgen_definitions.git', '.')
        subprocess.call(cmd, cwd=settings.paths['definitions'])
    else:
            # rebase only if force, otherwise use the current version
        cmd = ('git', 'pull', '--quiet', 'origin', 'master')
        subprocess.call(cmd, cwd=settings.paths['definitions'])
