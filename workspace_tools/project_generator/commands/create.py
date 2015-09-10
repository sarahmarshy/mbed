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

from project_generator.create import create_yaml

def run(args):
    print "create"
    root = os.getcwd()
    directory = root if not args.dir else os.path.normpath(os.path.join(root, args.dir))
    output = directory if not args.output else args.output
    logging.info("Generating the yaml records for %s."%directory)
    name = os.path.split(directory)[1] if not args.project else args.project
    create_yaml(os.path.normpath(directory), name, args.mcu.lower(), output)
    logging.info("Yaml files generated.")

def setup(subparser):
    subparser.add_argument(
        '-p', '--project', help='Project name')
    subparser.add_argument(
        '-m', '--mcu', action='store', help='Microcontroller part name', default="cortex-m0")
    subparser.add_argument(
        '-d', '--dir', action='store', help='Source directory', default=None)
    subparser.add_argument(
        '-o', '--output', action='store', help='Generated project files directory')
