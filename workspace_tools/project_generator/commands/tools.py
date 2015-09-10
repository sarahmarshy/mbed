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

from project_generator.generate import *

def run(args):
    logging.debug("Finding tools.")
    if os.path.exists(args.file):
        generator = Generator(args.file)
        for project in generator.generate(args.project):
            if project._for_tool() is None:
                sys.exit(1)
            tools = set(project.supported)
            tools = ", ".join(tools)
            print("%s supports: %s\n"%(project.project['name'], tools))
    else:
        # not project known by pgen
        logging.warning("%s not found." % args.file)

def setup(subparser):
        subparser.add_argument(
            "-f", "--file", help="YAML projects file", default='.projects.yaml')
        subparser.add_argument(
            "-p", "--project", help="Name of project to list development tools for", default='')
