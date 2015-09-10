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


import re
from os.path import *
import yaml
import shutil
import logging
import os

from project_generator.tool import ToolsSupported
from project_generator.util import PartialFormatter, FILES_EXTENSIONS, VALID_EXTENSIONS, FILE_MAP
from project_generator.settings import ProjectSettings
from project_generator.targets import Targets

class ProjectTemplate:

    @staticmethod
    def get_project_template(name):
        project = {
            'name': name,               # project name
            'linker_file': None,        # linker command file
            'build_dir': 'build',       # Build output path
            'debugger': 'cmsis-dap',    # Debugger
            'includes': [],             # include paths
            'sources': [],              # [internal]
            'macros': [],               # macros (defines)
            'misc': {},                 # misc tools settings, which are parsed by tool
            'output_type': 'exe',       # output type, default - exe
            'target': ''
        }
        return project

class Project:

    """represents a project, which can be formed of many yaml files"""
    def __init__(self, project_dicts, settings_dict, name, ignore):
        self.settings = ProjectSettings()
        if 'settings' in settings_dict:
            self.settings.update(settings_dict['settings'])

        self.name = name
        self.project_dicts = project_dicts
        self.tool = ''
        self.ignore_dirs = ignore
        self.project_data = ProjectTemplate().get_project_template(self.name)
        self.supported_tools = []
        self.project_file_path = ''
        self.rel_path = ''

    def generate(self, copy, tool, target_settings=None, tool_settings=None):
        """ Generates a project file """

        target_settings = join(os.getcwd(),target_settings) if target_settings is not None else None
        tool_settings = join(os.getcwd(),tool_settings) if tool_settings is not None else None

        os.chdir(self.settings.project_root)  # Change to root directory of source
        if self._for_tool(tool) is None:
            return None  # Customizing a project template for tool failed

        #  Targets object
        targets = Targets(self.settings.get_env_settings('definitions'))
        #  Targets keeps a list of available targets in definitions directory

        #  We get the target object with the project's target name
        self.project_data['target'] = targets.get_target(self.project_data['target'])

        # get the settings provided by the two yaml files, flags, macros, etc
        if target_settings is not None:
            target_settings = Project._try_open_file(target_settings)
            if target_settings is None:
                return None
            self.project_data['macros'] = target_settings['macros']
        if tool_settings is not None:
            tool_settings = Project._try_open_file(tool_settings)
            if tool_settings is None:
                return None
            self.project_data['misc'] = tool_settings

        #  Get an instance of a tools class so that we can call its generate function
        generator = ToolsSupported().get_tool(self.tool)

        # None is an error
        if generator is None:
            return None
        if copy:
            logging.info("Copying sources to output directory.")
            self._copy_files()

        self.project_data['rel_path'] = self.rel_path
        if self.project_data['target'] is None:
            return None

        logging.info("Project %s being generated for %s."%(self.project_data['name'],self.tool))
        result = generator(self.project_data).generate_project(self.project_file_path)
        return result

    def build(self, tool, exe_path):
        """build the project"""

        os.chdir(self.settings.project_root)  # Change to root directory of source
        self._set_output_dir_path()  # determines where generated projects will go

        build_tool = ToolsSupported().resolve_alias(tool)
        if build_tool is None:
            return None

        builder = ToolsSupported().get_tool(build_tool)
        # None is an error
        if builder is None:
            return None

        logging.info("Building for tool: %s", build_tool)
        result = builder(self.project_data).build_project(exe_path, self.project_file_path)
        return result

    def _for_tool(self, tool = "default"):
        if tool != "default":
            # will resolve any alias user writes in command line. IE iar => iar_arm
            self.tool = ToolsSupported().resolve_alias(tool)
            if self.tool is None:
                return None
        self.project_data = ProjectTemplate().get_project_template(self.name)  # default dictionary needed for project

        self.supported_tools = []  # tools that project's yaml files define

        for dict in self.project_dicts:  # iterates over the dictionaries defined in yaml file
            self._set_project_attributes(dict, "common")  # self.project dict values according to yaml common section
            self._find_tool_settings(dict)  # get tool specifc settings and supported tools

        # if tool is default, we are just extracting yaml information to see what tools are possible
        if self.tool not in self.supported_tools and tool != "default":
            logging.error("The tool name \"%s\" is not supported in yaml!"%self.tool, exc_info = False)
            return None

        self._set_output_dir_path()  # determines where generated projects will go

        logging.debug("Ignoring the following directories: %s"%", ".join(self.ignore_dirs))

        self._fix_includes_and_sources()

        if self.project_data['linker_file'] is None and tool!="default":
            logging.critical("No linker file found")
            return None

        return 1

    def _find_tool_settings(self, project_file_data):
        """"Looks in yaml file for tool_specific settings"""
        toolchain = ToolsSupported()._get_toolchain(self.tool)
        if 'tool_specific' in project_file_data:
            for tool, settings in project_file_data['tool_specific'].items():
                # Iterates over tool specific info in yaml. Will set corresponding self.project values
                if tool == self.tool or tool == toolchain:
                    self._set_project_attributes(project_file_data['tool_specific'],tool)
                    if tool != toolchain:
                        # Example case. Tool = Sublime, but yaml defines info for GCC
                        # Pgen should pick up the yaml settings for GCC
                        self._set_project_attributes(project_file_data['tool_specific'],toolchain)

                if 'linker_file' in settings and self.project_data['output_type'] == 'exe':
                    # Determine what tools the project can be succesfully generated for
                    self.supported_tools.extend(ToolsSupported().supported_tools(tool))

                elif self.project_data['output_type'] != 'exe':
                    # Output library, linker file not needed
                    self.supported_tools.extend(ToolsSupported().supported_tools(tool))

    def _set_project_attributes(self,project_file_data, section):
        """Set attributes in self.project according to dict and section(key) of that dict"""
        if section in project_file_data:  # make sure the key is valid
            for attribute, data in project_file_data[section].items():  # attribute => key, data => value
                if attribute in self.project_data.keys():  # Is this also a key is self.project?
                    if type(self.project_data[attribute]) is list:
                        if type(data) is list:
                            logging.debug("Setting %s to %s"%(attribute,", ".join(data)))
                            self.project_data[attribute].extend(data)
                        else:
                            logging.debug("Setting %s to %s"%(attribute,data))
                            self.project_data[attribute].append(data)
                    else:
                        logging.debug("Setting %s to %s"%(attribute,data[0]))
                        self.project_data[attribute] = data[0]  # self.project attribute is a string, only room for 1 value

    def _fix_includes_and_sources(self):
        includes = self.project_data['includes']
        source_files = self.project_data['sources']

        self.project_data['includes'] = []
        self.project_data['sources'] = []

        self._process_include_files(includes)

        self.project_data['source_files_c'] = {}     # c source files
        self.project_data['source_files_cpp'] = {}   # c++ source files
        self.project_data['source_files_s'] = {}     # assembly source files
        self.project_data['source_files_obj']= {}   # object files
        self.project_data['source_files_a']= {}     # libraries
        for files in source_files:
            """
            Check if user used a group name when defining sources
            Sources:
                group_name:
                    - source_file1
                    - source_file2
                - source_file_no_group
            """
            if type(files) == dict:
                for group_name, sources in files.items():
                    self._process_source_files(sources, group_name)
            else:
                self._process_source_files(source_files, 'default') # no group defined, put it in the default group

    def _process_include_files(self, include_paths):
        for path in include_paths:
            # include might be set to None - empty yaml list
            if path:
                if isfile(path):
                    # file, add it to the list (for copying or if tool requires it)
                    include = dirname(path)
                else:
                    # its a directory
                    include = path
                if include not in self.project_data['includes']:
                    self.project_data['includes'].append(include)

    def _process_source_files(self, files, group_name):
        """Sorts source files into groups in the form of source_groups[group_name][extension]
            extensions will be mapped to 5 main types 'cpp', 'c', 's', 'obj', 'a'"""
        for source_file in files:
            if any(re.match(ignore,source_file) for ignore in self.ignore_dirs):
                continue
            if isdir(source_file):
                self._process_source_files([join(normpath(source_file), f) for f in os.listdir(
                    source_file) if isfile(join(normpath(source_file), f))], group_name)

            extension = source_file.split('.')[-1]
            if extension not in VALID_EXTENSIONS:
                continue
            source_group = FILE_MAP[extension]

            if group_name not in self.project_data[source_group]:
                self.project_data[source_group][group_name] = []

            self.project_data[source_group][group_name].append(normpath(source_file))

    @staticmethod
    def _try_open_file(filename):
        if exists(filename):
            with open(filename, 'rt') as f:
                logging.info("Settings captured from %s."%filename)
                return yaml.load(f)
        else:
            logging.critical("The file %s doesn't exist." % filename)
            return None

    def _set_output_dir_path(self):
        location_format = self.settings.export_location_format

        try:
            target = self.project_data['target'].name
        except:
            target = self.project_data['target']

        # substitute all of the different dynamic values
        location = PartialFormatter().format(location_format, **{
            'project_name': self.name,
            'tool': self.tool,
            'target': target
        })

        self.project_file_path = normpath(location)
        self.rel_path = relpath(os.getcwd(),self.project_file_path)+sep

        logging.debug("Output directory: %s"%self.rel_path+self.project_file_path)

    def _copy_files(self):
        no_ignore = []
        for key in FILES_EXTENSIONS.keys():
            if type(self.project_data[key]) is dict:
                for k,v in self.project_data[key].items():
                    no_ignore.extend(v)
            elif type(self.project_data[key]) is list:
                no_ignore.extend(self.project_data[key])
            else:
                no_ignore.append(self.project_data[key])
        dst = join(self.project_file_path,"copy")
        if exists(dst):
            shutil.rmtree(dst)
        src = relpath(os.getcwd())
        for item in [x for x in os.listdir(src) if x in no_ignore]:
            s = join(src,item)
            d = join(dst,item)
            if isdir(s):
                shutil.copytree(s,d)
            else:
                shutil.copy2(s,d)