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

import yaml
from os.path import join, splitext
from os import listdir
import logging

class Target:
    def __init__(self, name, tools, config):
        self.name = name # name of the target
        self.supported_tools = tools # list of tools supported (defined in MCU definition)
        self.config = config # entire dictionary
        self.core = self.mcu_data('core') # name of core i.e. cortex-m4f
        self.vendor = self.mcu_data('vendor') # vendor of target i.e. Freescale
        self.fpu = self.core[-1] == 'f' # boolean, true if target has an FPU
        self.fpu_convention = ''
        if self.fpu:
            self.fpu_convention = self.mcu_data('fpu_convention')

    def get_tool_configuration(self, tool):
        if not(tool in self.supported_tools):
            logging.critical("Target %s does not support %s." % (self.name,tool))
            return None
        return self.config['tool_specific'][tool]

    def get_device_configuration(self):
        return self.config['mcu']

    def mcu_data(self, section):
        if section in self.config['mcu']:
            return self.config['mcu'][section]
        return ''

class Targets:

    def __init__(self, directory=None):
        if directory:
            logging.debug("Target definitions captured from %s."%directory)
            self.definitions_directory = directory
            self.targets = [Target(splitext(f)[0],self._find_tools(f),self._load_record(f)) for f in listdir(directory)
                            if splitext(f)[1] == '.yaml' ]

    def _load_record(self, file):
        project_file = open(join(self.definitions_directory,file))
        config = yaml.load(project_file)
        project_file.close()
        return config

    def _find_tools(self,file):
        config = self._load_record(file)
        return config['tool_specific'].keys()

    def get_target(self, alias):
        targs = filter(lambda x: alias.lower() in x.name.lower(),self.targets)
        if len(targs) == 1:
            return targs[0]
        elif len(targs) > 1:
            print("Multiple targets contain %s"%alias)
            for i, target in enumerate(targs):
                print(str(i) + ": " + target.name)
            answer = raw_input('\nWhich target do you want? ')
            while int(answer) not in range(0,len(targs)):
                answer = raw_input('Answer not in list. Which target do you want? ')
            return targs[int(answer)]
        targets = [target.name for target in self.targets]
        logging.critical("\n%s must be contained in one of these strings: \n%s" % (alias,"\n".join(targets)))
        return None