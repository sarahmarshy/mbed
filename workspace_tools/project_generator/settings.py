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
from os.path import expanduser, normpath, join, pardir

class ProjectSettings:
    PROJECT_ROOT = os.environ.get('PROJECT_GENERATOR_ROOT') or join(pardir, pardir)
    DEFAULT_TOOL = os.environ.get('PROJECT_GENERATOR_DEFAULT_TOOL') or 'uvision'

    DEFAULT_EXPORT_LOCATION_FORMAT = join('projectfiles', '{tool}_{project_name}')
    DEFAULT_ROOT = os.getcwd()

    def __init__(self):
        """ This are default enviroment settings for build tools. To override,
        define them in the projects.yaml file. """

        self.paths ={}
        self.paths['definitions'] = join(expanduser('~/.defs'), 'definitions')
        if not os.path.exists(join(expanduser('~/.defs'))):
            os.mkdir(join(expanduser('~/.defs')))

        self.export_location_format = self.DEFAULT_EXPORT_LOCATION_FORMAT
        self.project_root = self.DEFAULT_ROOT

    def update(self, settings):
        if settings:
            if 'root' in settings:
                self.project_root = normpath(settings['root'])

            if 'export_dir' in settings:
                self.export_location_format = normpath(settings['export_dir'])

    def get_env_settings(self, env_set):
        return self.paths[env_set]

