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

import os
import logging
import xmltodict
import copy
import re

from os.path import basename, join
from project_generator.tools.generator import Generator
from project_generator.tools.builder import Builder
from project_generator.tools.extractor import Extractor
from project_generator.util import FILES_EXTENSIONS,SOURCE_KEYS

class uVisionDefinitions():
    debuggers = {
        'cmsis-dap': {
            'TargetDlls': {
                'Driver' : 'BIN\CMSIS_AGDI.dll',
            },
        },
        'j-link': {
            'TargetDlls': {
                'Driver' : 'Segger\JL2CM3.dll',
            },
        }
    }

    uvision_settings = {
        # C/C++ settings
        'Cads': {
            'Optim':[0],
            'MiscControls': [],  # Misc controls
        },

        # Assembly settings
        'Aads': {
            'MiscControls': [],    # Misc controls
            'IncludePath': [],     # Include paths
        },
        'TargetDlls': {

        },
    }

class Uvision(Builder, Generator, Extractor):

    optimization_options = ['O0', 'O1', 'O2', 'O3']
    file_types = {}

    #file_types = {'cpp': 8, 'c': 1, 's': 2, 'S':2,'obj': 3,'o':3, 'lib': 4, 'ar': 4}
    for key in SOURCE_KEYS:
        for extension in FILES_EXTENSIONS[key]:
            type = key.split("_")[-1]
            if type == 'cpp':
                file_types[extension] = 8
            if type == 'c':
                file_types[extension] = 1
            if type == 's':
                file_types[extension] = 2
            if type == 'a':
                file_types[extension] = 4
            if type == 'obj':
                file_types[extension] = 3

    ERRORLEVEL = {
        0: '(0 warnings, 0 errors)',
        1: 'warnings',
        2: 'errors',
        3: 'fatal errors',
        11: 'cant write to project file',
        12: 'device error',
        13: 'error writing',
        15: 'error reading xml file',
    }

    SUCCESSVALUE = 0
    WARNVALUE = 1

    def __init__(self, project_data):
        self.definitions = uVisionDefinitions()
        # workspace or project
        self.project_data = project_data

    @staticmethod
    def get_toolnames():
        return ['uvision']

    @staticmethod
    def get_toolchain():
        return 'uvision'

    def _expand_data(self, source_file, project_data, group):
        """ data expansion - uvision needs filename and path separately. """
        extension = source_file.split(".")[-1]
        new_file = {"FilePath": source_file, "FileName": basename(source_file),
                                "FileType": self.file_types[extension]}
        project_data['groups'][group].append(new_file)

    def _iterate(self, data, project_data):
        """ Iterate through all data, store the result expansion in extended dictionary. """
        for attribute in SOURCE_KEYS:
            for k, v in data[attribute].items():
                for source_file in v:
                    self._expand_data(source_file, project_data, k)

    def _parse_specific_options(self, project_data):
        """ Parse all uvision specific setttings. """
        default_set = copy.deepcopy(self.definitions.uvision_settings)
        project_data['uvision_settings'].update(default_set)  # set specific options to default values
        for section, controls in project_data['misc'].items():
            for k,v in controls.items():
                for setting in v:
                    if section == "C" and k == 'MiscControls':
                        project_data['uvision_settings']['Cads']['MiscControls'].append(str(setting))
                    if section == "ASM" and k == 'MiscControls':
                        project_data['uvision_settings']['Aads']['MiscControls'].append(str(setting))

    def _get_groups(self, project_data):
        """ Get all groups defined. """
        groups = []
        for attribute in SOURCE_KEYS:
            if project_data[attribute]:
                groups.extend(filter(lambda k:k not in groups,project_data[attribute].keys()))
        return groups

    def _append_mcu_def(self, project_data, mcu_def):
        """ Get MCU definitons as Flash algo, RAM, ROM size , etc. """
        try:
            project_data['uvision_settings'].update(mcu_def['TargetOption'])
        except KeyError:
            # does not exist, create it
            project_data['uvision_settings'] = mcu_def['TargetOption']

    def _parse_data(self, tool, project_data):
        groups = self._get_groups(self.project_data)
        project_data['groups'] = {}
        for group in groups:
            project_data['groups'][group] = []

        self._iterate(self.project_data, project_data)

        project_data['uvision_settings'] = {}
        self._parse_specific_options(project_data)

        project_data['build_dir'] = '.\\' + project_data['build_dir'] + '\\'
        # set target only if defined, otherwise use from template/default one

        mcu_def_dic = project_data['target'].get_tool_configuration(tool)
        if mcu_def_dic is None:
            return None
        logging.debug("Mcu definitions: %s" % mcu_def_dic)
        self._append_mcu_def(project_data, mcu_def_dic)

        # load debugger
        driver = self.definitions.debuggers[project_data['debugger']]['TargetDlls']['Driver']
        project_data['uvision_settings']['TargetDlls']['Driver'] = driver
        # optimization set to correct value, default not used
        project_data['uvision_settings']['Cads']['Optim'][0] = 1

        project_data ['core'] = project_data ['target'].core

        #Target has f postfix, IE cortex-m4f
        if project_data['target'].fpu:
            #Remove the f from the end
            project_data['core'] = project_data['core'][:-1]
            project_data['uvision_settings']['Cpu'] = "CPUTYPE(\""+project_data['core']+"\")"
            #Add FPU option to CPU info
            project_data['uvision_settings']['Cpu'] += " FPU2"
        else:
            project_data['uvision_settings']['Cpu'] = "CPUTYPE(\""+project_data['core']+"\")"

    def generate_file(self,tmpl,data,ext,destination):
        self.gen_file_jinja(
            tmpl, data, '%s.%s'%(self.project_data['name'],ext), destination)

    def generate_project(self, project_file_path):
        self.fix_paths()
        project_dic = self.project_data.copy()
        self._parse_data('uvision',project_dic) #broken out so uvision5 can call super with uvision5 as parameter
        # Project file
        self.generate_file('uvision4.uvproj.tmpl',project_dic,'uvproj', project_file_path)
        return 0

    def build_project(self, exe_path, project_file_path):
        # > UV4 -b [project_path]
        path = ''
        pattern = str(self.project_data['name']) + r"\.uvproj[x]?"
        for project_file in os.listdir(project_file_path):
            if re.match(pattern,project_file):
                path = join(project_file_path,project_file)
                break

        if not os.path.exists(path):
            logging.critical("The file: %s does not exist. You must call generate before build." % path)
            return None

        proj_name = path.split(os.path.sep)[-1]
        build_path = join('.', self.project_data['build_dir'], 'build_log.txt')

        args = [exe_path,'-r', path, '-o', build_path, '-j0']

        ret = Builder.build_command(args, self, "Uvision", proj_name)

        if ret != 0 and logging.getLogger().isEnabledFor(logging.DEBUG):
            build_path = join(project_file_path, self.project_data['build_dir'], 'build_log.txt')
            if os.path.exists(build_path):
                with open(build_path, 'r+') as f:
                    logging.debug(" BUILD LOG\n" + "\n".join(f.readlines()))
        return ret

    def extract_mcu_definition(self, project_file,name):
        """ Parse project file to get target definition """
        mcu = self.MCU_TEMPLATE

        uvproj_dic = xmltodict.parse(file(project_file), dict_constructor=dict)
        # Generic Target, should get from Target class !

        core = uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Cpu']
        regex = r"CPUTYPE\(\"([\w-]+)\"\)\s*(FPU2)?"
        match = re.search(regex,core)
        if match:
            mcu['mcu']['core'] = match.group(1)
            if match.group(2):
                mcu['mcu']['core']+='f'

        mcu['tool_specific']['uvision'] = {
                'TargetOption' : {
                    'Device' : uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['Device'],
                    'DeviceId' : int(uvproj_dic['Project']['Targets']['Target']['TargetOption']['TargetCommonOption']['DeviceId']),
                }
        }

        self.save_mcu_data(mcu,name)
