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

import logging

from project_generator.tools.iar import IAREmbeddedWorkbench
from project_generator.tools.uvision import Uvision
from project_generator.tools.uvision5 import Uvision5
from project_generator.tools.eclipse import EclipseGnuARM
from project_generator.tools.gccarm import MakefileGccArm
from project_generator.tools.sublimetext import SublimeTextMakeGccARM

class ToolsSupported:
    """ Represents all tools available """

    TOOLS_ALIAS ={  # The values of each key should correspond to a key in TOOLS_DICT
        'iar':          'iar_arm',
        'make_gcc':     'make_gcc_arm',
        'gcc_arm':      'make_gcc_arm',
        'eclipse':      'eclipse_make_gcc_arm',
        'sublime':      'sublime_make_gcc_arm',
        'sublime_text': 'sublime_make_gcc_arm'
     }

    TOOLS_DICT = {
        'iar_arm':              IAREmbeddedWorkbench,
        'uvision':              Uvision,
        'uvision5':             Uvision5,
        'make_gcc_arm':         MakefileGccArm,
        'eclipse_make_gcc_arm': EclipseGnuARM,
        'sublime_make_gcc_arm': SublimeTextMakeGccARM
    }

    TOOLS = list(set([v for k, v in TOOLS_DICT.items() if v is not None]))

    def get_tool(self, tool):
        try:
            return self.TOOLS_DICT[tool]
        except KeyError:
            return None

    def supported_tools(self,toolchain):
        # Iterate over all possible pgen tools, return only the ones where the toolchain is a valid toolname of a tool
        return [tool for tool in self._all_supported_tools() if toolchain in self._get_toolnames(tool)]

    def resolve_alias(self, alias):
        if alias in self.TOOLS_ALIAS.keys():
            return self.TOOLS_ALIAS[alias]
        elif alias in self.TOOLS_DICT.keys():
            return alias
        options = self._all_supported_tools() + self.TOOLS_ALIAS.keys()
        options.sort()
        logging.error("The tool name \"%s\" is not valid! \nChoose from: \n%s"% (alias, ", ".join(options)),exc_info= False)
        return None

    def _get_toolnames(self, tool):
        try:
            return self.TOOLS_DICT[tool].get_toolnames()
        except KeyError:
            return None

    def _get_toolchain(self, tool):
        try:
            return self.TOOLS_DICT[tool].get_toolchain()
        except KeyError:
            return None

    def _all_supported_tools(self):
        return self.TOOLS_DICT.keys()
