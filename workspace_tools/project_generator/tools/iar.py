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

import xmltodict
import logging
import os
from os.path import join

from project_generator.tools.builder import Builder
from project_generator.tools.generator import Generator
from project_generator.tools.extractor import Extractor
from project_generator.util import SOURCE_KEYS


class IAREmbeddedWorkbench(Builder, Generator, Extractor):

    SUCCESSVALUE = 0
    ERRORVALUE = 1
    WARNVALUE = 0 #undetermined

    ERRORLEVEL = {
        0: '(0 warnings, 0 errors)',
        1: 'errors'
    }

    source_files_dic = [
        'source_files_c', 'source_files_s', 'source_files_cpp', 'source_files_a', 'source_files_obj']

    def __init__(self, project_data):
        self.project_data = project_data

    @staticmethod
    def get_toolnames():
        return ['iar_arm']

    @staticmethod
    def get_toolchain():
        return 'iar'

    def _parse_specific_options(self, project_data):
        """ Parse all IAR specific settings. """
        for dic in project_data['misc']:
            # for k,v in dic.items():
            self._set_specific_settings(dic, project_data)

    def _set_specific_settings(self, value_list, data):
        #not implemted
        return

    def _normalize_mcu_def(self, mcu_def):
        for k,v in mcu_def['OGChipSelectEditMenu'].items():
            # hack to insert tab as IAR using tab for MCU definitions
            v = v.replace(' ', '\t', 1)
            mcu_def['OGChipSelectEditMenu'][k] = v

    def _fix_iar_paths(self, data):
        """ All paths needs to be fixed - add PROJ_DIR prefix + normalize """
        data['includes'] = [join('$PROJ_DIR$', path) for path in data['includes']]
            
        if data['linker_file']:
            data['linker_file'] = join('$PROJ_DIR$', data['linker_file'])

        data['groups'] = {}
        for attribute in SOURCE_KEYS:
            for k, v in data[attribute].items():
                if k not in data['groups']:
                    data['groups'][k] = []
                data['groups'][k].extend([join('$PROJ_DIR$', file) for file in v])

    def _get_option(self, settings, find_key):
        for option in settings:
            if option['name'] == find_key:
                return settings.index(option)

    def build_project(self, exe_path, project_file_path):
        """ Build IAR project. """
        # > IarBuild [project_path] -build [project_name]
        proj_path = join(project_file_path,self.project_data['name'])
        if proj_path.split('.')[-1] != 'ewp':
            proj_path += '.ewp'
        if not os.path.exists(proj_path):
            logging.debug("The file: %s does not exist. You must call generate before build." % proj_path)
            return None
        logging.debug("Building IAR project: %s" % proj_path)
        proj_name = proj_path.split(os.path.sep)[-1]

        args = [exe_path, proj_path, '-build', os.path.splitext(os.path.basename(proj_path))[0]]
        Builder().build_command(args,self,"IAR",proj_name)

    def generate_project(self, output_path):
        """ Processes groups and misc options specific for IAR, and run generator """
        self.fix_paths()
        project_data = self.project_data.copy()
        self._fix_iar_paths(project_data)

        project_data['iar_settings'] = {}
        self._parse_specific_options(project_data)

        mcu_def_dic = project_data['target'].get_tool_configuration('iar')
        if mcu_def_dic is None:
            return None

        if project_data['target'].fpu:
            project_data['iar_settings']['fpu'] = True
        self._normalize_mcu_def(mcu_def_dic)
        logging.debug("Mcu definitions: %s" % mcu_def_dic)
        project_data['iar_settings'].update(mcu_def_dic)

        self.gen_file_jinja('iar.ewp.tmpl', project_data, '%s.ewp' %
            self.project_data['name'], output_path)
        self.gen_file_jinja('iar.eww.tmpl', project_data, '%s.eww' %
            self.project_data['name'], output_path)
        return 0

    def extract_mcu_definition(self, project_file, name):
        """ Parse project file to get mcu definition """
        mcu = self.MCU_TEMPLATE
        ewp_dic = xmltodict.parse(file(project_file), dict_constructor=dict)

        # we take 0 configuration or just configuration, as multiple configuration possibl
        # debug, release, for mcu - does not matter, try and adjust
        try:
            index_general = self._get_option(ewp_dic['project']['configuration'][0]['settings'], 'General')
            configuration = ewp_dic['project']['configuration'][0]
        except KeyError:
            index_general = self._get_option(ewp_dic['project']['configuration']['settings'], 'General')
            configuration = ewp_dic['project']['configuration']
        index_option = self._get_option(configuration['settings'][index_general]['data']['option'], 'OGChipSelectEditMenu')
        OGChipSelectEditMenu = configuration['settings'][index_general]['data']['option'][index_option]

        mcu['tool_specific']['iar'] = {
            'OGChipSelectEditMenu' : {
                'state' : OGChipSelectEditMenu['state'].replace('\t', ' ', 1),
            },
            'OGCoreOrChip' : {
                'state' : 1,
            }
        }

        self.save_mcu_data(mcu,name)
