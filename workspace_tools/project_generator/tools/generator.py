   # Copyright 2014-2015 0xc0170
#
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
import logging
from os.path import join, dirname
from jinja2 import Template
from os.path import normpath

from project_generator.util import FILES_EXTENSIONS

class Generator(object):

    """Just a template for subclassing"""

    TEMPLATE_DIR = join(dirname(__file__), '..', 'templates')

    def gen_file_jinja(self, template_file, data, output, dest_path):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        output = join(dest_path, output)
        logging.debug("Generating: %s" % output)

        """ Fills data to the project template, using jinja2. """
        template_path = join(self.TEMPLATE_DIR, template_file)
        template_text = open(template_path).read()
        template = Template(template_text)
        target_text = template.render(data)
        open(output, "w").write(target_text)
        return dirname(output), output

    def fix_paths(self):
        norm_func = lambda path : normpath(join(self.project_data['rel_path'],path))
        for key in FILES_EXTENSIONS.keys():
            if type(self.project_data[key]) is dict:
                for k,v in self.project_data[key].items():
                    self.project_data[key][k] = map(norm_func,v)
            elif type(self.project_data[key]) is list:
                self.project_data[key] = map(norm_func,self.project_data[key])
            else:
                self.project_data[key] = norm_func(self.project_data[key])
