"""
mbed SDK
Copyright (c) 2011-2013 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from os.path import splitext, basename
from os import curdir

from exporters import Exporter
from tools.targets import TARGET_MAP


class GccArm(Exporter):
    NAME = 'GccArm'
    TOOLCHAIN = 'GCC_ARM'

    TARGETS = []
    for target in TARGET_MAP.keys():
        if TOOLCHAIN in TARGET_MAP[target].supported_toolchains:
            TARGETS.append(target)

    DOT_IN_RELATIVE_PATH = True

    MBED_CONFIG_HEADER_SUPPORTED = True

    def generate(self):
        # "make" wants Unix paths
        self.resources.win_to_unix()
        self.resources.relative_to(curdir)

        to_be_compiled = []
        for r_type in ['s_sources', 'c_sources', 'cpp_sources']:
            r = getattr(self.resources, r_type)
            if r:
                for source in r:
                    base, ext = splitext(source)
                    to_be_compiled.append(base + '.o')

        libraries = []
        for lib in self.resources.libraries:
            l, _ = splitext(basename(lib))
            libraries.append(l[3:])

        ctx = {
            'name': self.program_name,
            'to_be_compiled': to_be_compiled,
            'object_files': self.resources.objects,
            'include_paths': self.resources.inc_dirs,
            'library_paths': self.resources.lib_dirs,
            'linker_script': self.resources.linker_script,
            'libraries': libraries,
            'symbols': self.get_symbols(),
            'cpu_flags': self.toolchain.cpu
        }
        ctx.update(self.progen_flags)
        self.gen_file('gcc_arm_%s.tmpl' % self.target.lower(), ctx, 'Makefile')
