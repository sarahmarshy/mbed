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

import sys
import logging
from project_generator.tool import ToolsSupported
import os

def run(args):

    if not os.path.exists(args.file):
        logging.critical("The file %s does not exist!" % args.file)
        sys.exit(1)
    extension_dic = {'uvproj': 'uvision', 'uvprojx': 'uvision5', 'ewp': 'iar'}
    extension = args.file.split('.')[-1]
    if extension not in extension_dic:
        options = "\n".join(extension_dic.keys())
        logging.critical("The extension provided does not have an import command. \nChoose from: \n %s" % options)
        sys.exit(1)
    extractor = ToolsSupported().get_tool(extension_dic[extension])
    extractor(None).extract_mcu_definition(args.file,args.mcu)

def setup(subparser):
    subparser.add_argument(
        '-m', '--mcu', action='store', required=True, help='MCU name that setting are being extracted for')
    subparser.add_argument(
        '-f', '--file', action='store', required=True, help='Development tool project file to be parsed. Must be valid')
