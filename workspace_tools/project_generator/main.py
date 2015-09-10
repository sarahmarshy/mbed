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

import argparse
import logging
import pkg_resources

from project_generator.commands import build, generate, create, tools, extract
from util import update

subcommands = {
    'create': create,
    'generate': generate,
    'build': build,
    'tools': tools,
    'extract': extract
}
help = {
    'create': "Create a yaml file describing a given directory. If no directory is specified, the current working "
              "directory will be used.",
    'generate': "Generate a project for a given tool, according to a specified yaml file. If no file is specified, "
                ".projects.yaml will be used",
    'build': "Build a generated project for a specified tool. `generate` must be run before a call to `build`.",
    'tools': "List all tools supported by a given yaml file and given project. If no project is specified, `tools` "
             "will list all possible tools for all projects in a yaml file.",
    'extract': "Create an MCU record for a tool given a valid project file."
}

def main():
    # Parse Options
    parser = argparse.ArgumentParser(
        description = 'Generate and build project files for many different tools.'
    )

    parser.add_argument('-v', dest='verbosity', action='count', default=0,
                        help='Increase the verbosity of the output (repeat for more verbose output)')
    parser.add_argument('-q', dest='quietness', action='count', default=0,
                        help='Decrease the verbosity of the output (repeat for less verbose output)')
    parser.add_argument('-u', dest='update', action='store_true',
                        help='Update pgen\'s mcu definitions')

    parser.add_argument("--version", action='version',
                        version=pkg_resources.require("project_generator")[0].version, help="Display version")

    subparsers = parser.add_subparsers(help='commands')

    for name, module in subcommands.items():
        subparser = subparsers.add_parser(name, description=help[name])
        module.setup(subparser)  # calls module's setup function
        subparser.set_defaults(func=module.run)  # set's func to call module's run function

    args = parser.parse_args()

    if args.update:
        update()

    # set the verbosity
    verbosity = args.verbosity - args.quietness
    logging_level = max(logging.WARNING - (10 * verbosity), 0)
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging_level)

    args.func(args)

if __name__ == '__main__':
    main()
