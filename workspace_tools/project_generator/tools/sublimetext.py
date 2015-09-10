# Copyright 2014-2015 sg-, 0xc0170
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

from project_generator.tools.gccarm import MakefileGccArm


class SublimeTextMakeGccARM(MakefileGccArm):
    def __init__(self, project_data):
        super(SublimeTextMakeGccARM, self).__init__(project_data)

    @staticmethod
    def get_toolnames():
        return ['sublime_make_gcc_arm', 'make_gcc_arm', 'sublime']

    @staticmethod
    def get_toolchain():
        return 'make_gcc_arm'

    def _fix_sublime_paths(self, data):
        fixed_paths = []
        for path in data['source_paths']:
            # TODO - fix, using only posix paths
            fixed_paths.append(path.replace('\\', '/'))
        data['source_paths'] = fixed_paths

    def generate_project(self):
        """ Processes misc options specific for GCC ARM, and run generator. """
        self.process_data_for_makefile(self.project_data)
        self._fix_sublime_paths(self.project_data)
        self.project_data['linker_options'] =[]

        self.gen_file_jinja('makefile_gcc.tmpl', self.project_data, 'Makefile', self.project_data['output_dir']['path'])

        self.gen_file_jinja('sublimetext.sublime-project.tmpl', self.project_data,
                            '%s.sublime-project' % self.project_data['name'], self.project_data['output_dir']['path'])
        return 0