# Copyright 2015 0xc0170
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

from project_generator.tools.uvision import *

class Uvision5(Uvision):
    def __init__(self, project_data):
        super(Uvision5,self).__init__(project_data)

    @staticmethod
    def get_toolnames():
        return ['uvision5','uvision']

    @staticmethod
    def get_toolchain():
        return 'uvision'

    def generate_project(self, project_file_path):
        self.fix_paths()
        data = self.project_data.copy()
        self._parse_data('uvision5',data)
        data ['vendor'] = data ['target'].vendor
        # Project file
        self.generate_file('uvision5.uvprojx.tmpl',data,'uvprojx', project_file_path)
        return 0

    def extract_mcu_definition(self, project_file, name):
        """ Parse project file to get target definition """
        mcu = self.MCU_TEMPLATE

        uvproj_dic = xmltodict.parse(file(project_file), dict_constructor=dict)

        core = uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Cpu']
        regex = r"CPUTYPE\(\"([\w-]+)\"\)\s*(FPU2)?"
        match = re.search(regex,core)
        if match:
            mcu['mcu']['core'] = match.group(1)
            if match.group(2):
                mcu['mcu']['core']+='f'

        # Generic Target, should get from Target class !
        vendor = uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Vendor']
        mcu['mcu']['vendor'] = vendor
        mcu['tool_specific']['uvision'] = {
            'TargetOption' : {
                'Device' : uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Device'],
            }
        }

        self.save_mcu_data(mcu,name)