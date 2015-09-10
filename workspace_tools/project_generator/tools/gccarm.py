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
import ntpath
import shutil
from itertools import chain

from project_generator.util import SOURCE_KEYS
from project_generator.tools.builder import Builder
from project_generator.tools.generator import Generator


class MakefileGccArm(Generator, Builder):

    # http://www.gnu.org/software/make/manual/html_node/Running.html
    ERRORLEVEL = {
        0: 'no errors',
        1: 'targets not already up to date',
        2: 'errors'
    }

    SUCCESSVALUE = 0
    WARNVALUE = 1

    optimization_options = ['O0', 'O1', 'O2', 'O3', 'Os']

    def __init__(self, project_data):
        self.project_data = project_data

    @staticmethod
    def get_toolnames():
        return ['make_gcc_arm']

    @staticmethod
    def get_toolchain():
        return 'make_gcc_arm'

    def _parse_specific_options(self, data):
        """ Parse all uvision specific setttings. """
        data['compiler_options'] = []
        data['linker_options'] = []
        for k, v in data['misc'].items():
            if type(v) is list:
                if k not in data:
                    data[k] = []
                data[k].extend(v)
            else:
                if k not in data:
                    data[k] = ''
                data[k] = v

    def _get_libs(self, project_data):
        project_data['lib_paths'] =[]
        project_data['libraries'] =[]
        for lib in project_data['source_files_a']:
            head, tail = ntpath.split(lib)
            file = tail
            if (os.path.splitext(file)[1] != ".a"):
                continue
            else:
                file = file.replace(".a","")
                project_data['lib_paths'].append(head)
                project_data['libraries'].append(file.replace("lib",''))

    def generate_project(self, project_file_path):
        """ Processes misc options specific for GCC ARM, and run generator. """
        self.fix_paths()
        self.process_data_for_makefile(self.project_data)
        self.gen_file_jinja('makefile_gcc.tmpl', self.project_data, 'Makefile', project_file_path)
        return 0

    def get_generated_project_files(self):
        return {'path': self.project_data['path'], 'files': [self.project_data['files']['makefile']]}

    def process_data_for_makefile(self, project_data):
        #Flatten our dictionary, we don't need groups
        project_data['source_paths'] = []
        for key in SOURCE_KEYS:
            project_data[key] = list(chain(*project_data[key].values()))
            project_data['source_paths'].extend([ntpath.split(path)[0] for path in project_data[key]])
        project_data['source_paths'] = set(project_data['source_paths'])

        self._get_libs(project_data)

        self._parse_specific_options(project_data)
        if 'instruction_mode' not in project_data:
            project_data['instruction_mode']= 'thumb'

        project_data['core'] = project_data['target'].core.lower()
        project_data['fpu'] = project_data['target'].fpu_convention.lower()
        # gcc arm is funny about cortex-m4f.
        # gcc arm is funny about cortex-m4f.
        if project_data['core'] == 'cortex-m4f':
            project_data['core'] = 'cortex-m4'

        # change cortex-m0+ to cortex-m0plus
        if project_data['core'] == 'cortex-m0+':
            project_data['core'] = 'cortex-m0plus'

        # set default values
        if 'optimization_level' not in project_data:
            project_data['optimization_level'] = self.optimization_options[0]

    def build_project(self, exe_path, project_file_path):
        # cwd: relpath(join(project_path, ("gcc_arm" + project)))
        # > make all
        os.chdir(project_file_path)
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("bin"):
            shutil.rmtree("bin")

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            args = ['make', 'all']
        else:
            args =['make','-s','all']

        ret = Builder.build_command(args, self, "GCC", project_file_path.split(os.path.sep)[-1])
        return ret
