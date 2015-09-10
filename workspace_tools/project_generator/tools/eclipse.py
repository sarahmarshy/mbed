# Copyright 2014 0xc0170
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
from itertools import chain
import ntpath

from project_generator.tools.generator import Generator
from project_generator.tools.builder import Builder
from project_generator.tools.gccarm import MakefileGccArm
from project_generator.util import FILES_EXTENSIONS, SOURCE_KEYS

class EclipseGnuARM(Generator, Builder):
    file_types = {}
    for key in SOURCE_KEYS:
        for extension in FILES_EXTENSIONS[key]:
            file_types[extension] = 1

    def __init__(self, project_data):
        self.exporter = MakefileGccArm(project_data)
        self.project_data = project_data

    @staticmethod
    def get_toolnames():
        return ['eclipse_make_gcc_arm', 'make_gcc_arm']

    @staticmethod
    def get_toolchain():
        return 'make_gcc_arm'

    def build_project(self, exe_path=None):
        self.exporter.build_project()

    def _get_libs(self, data):
        data['lib_paths'] =[]
        data['libraries'] =[]
        data['source_files_a'] = list(chain(*data['source_files_a'].values()))
        for lib in data['source_files_a']:
            head, tail = ntpath.split(lib)
            file = tail
            if (os.path.splitext(file)[1] != ".a"):
                continue
            else:
                file = file.replace(".a","")
                data['lib_paths'].append(head)
                data['libraries'].append(file.replace("lib",''))

    def generate_project(self, project_file_path):
        """ Processes groups and misc options specific for eclipse, and run generator """
        data_for_make = self.project_data.copy()

        self.exporter.process_data_for_makefile(data_for_make)
        self.gen_file_jinja('makefile_gcc.tmpl', data_for_make, 'Makefile', project_file_path)

        project_data = self.project_data.copy()

        project_data ['core'] = project_data ['target'].core.lower()
        project_data['fpu'] = project_data['target'].fpu_convention.lower()
        if project_data['core'] == 'cortex-m4f':
            project_data['core'] = 'cortex-m4'

        # change cortex-m0+ to cortex-m0plus
        if project_data['core'] == 'cortex-m0+':
            project_data['core'] = 'cortex-m0plus'

        self._get_libs(project_data)

        project_data['includes'].append('.')
        # Project file
        self.gen_file_jinja(
            'eclipse_makefile.cproject.tmpl', project_data, '.cproject', project_file_path)
        self.gen_file_jinja(
            'eclipse.project.tmpl', project_data, '.project', project_file_path)
        return 0

