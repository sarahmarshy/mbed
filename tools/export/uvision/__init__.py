import os
from os.path import sep, normpath, basename, dirname, realpath, relpath
from itertools import groupby
import ntpath
import copy
from collections import namedtuple

from ArmPackManager import Cache

from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter
from tools.export.cmsis import deviceCMSIS
import yaml

cache_d = False

class Uvision(Exporter):
    """Keil Uvision class

    This class encapsulates information to be contained in a Uvision
    project file (.uvprojx).
    The needed information can be viewed in uvision.tmpl
    """
    NAME = 'cmsis'
    TOOLCHAIN = 'ARM'
    TARGETS = [target for target, obj in TARGET_MAP.iteritems()
               if "ARM" in obj.supported_toolchains]
    #File associations within .uvprojx file
    file_types = {'.cpp': 8, '.c': 1, '.s': 2,
                  '.obj': 3, '.o': 3, '.lib': 4,
                  '.ar': 4, '.h': 5, '.sct': 4}

    def uv_file(self, loc):
        """Return a namedtuple of information about project file
        Positional Arguments:
        loc - the file's location

        .uvprojx XML for project file:
        <File>
            <FileType>{{file.type}}</FileType>
            <FileName>{{file.name}}</FileName>
            <FilePath>{{file.loc}}</FilePath>
        </File>
        """
        UVFile = namedtuple('UVFile', ['type','loc','name'])
        _, ext = os.path.splitext(loc)
        type = self.file_types[ext.lower()]
        name = ntpath.basename(normpath(loc))
        return UVFile(type, loc, name)

    def make_key(self, src):
        """From a source file, extract group name
        Positional Arguments:
        src - the src's location
        """
        key = basename(dirname(src.loc))
        if key == ".":
            key = basename(realpath(self.export_dir))
        return key

    def group_project_files(self, sources):
        """Group the source files by their encompassing directory
        Positional Arguments:
        sources - array of sourc locations

        Returns a dictionary of {group name: list of source locations}
        """
        data = sorted(sources, key=self.make_key)
        return {k: list(g) for k,g in groupby(data, self.make_key)}

    def format_flags(self):
        """Format toolchain flags for Uvision"""
        flags = copy.deepcopy(self.flags)
        asm_flag_string = '--cpreproc --cpreproc_opts=-D__ASSERT_MSG,' + \
                          ",".join(flags['asm_flags'])
        # asm flags only, common are not valid within uvision project,
        # they are armcc specific
        flags['asm_flags'] = asm_flag_string
        # cxx flags included, as uvision have them all in one tab
        flags['c_flags'] = list(set(['-D__ASSERT_MSG']
                                        + flags['common_flags']
                                        + flags['c_flags']
                                        + flags['cxx_flags']))
        # not compatible with c99 flag set in the template
        try: flags['c_flags'].remove("--c99")
        except ValueError: pass
        # cpp is not required as it's implicit for cpp files
        try: flags['c_flags'].remove("--cpp")
        except ValueError: pass
        # we want no-vla for only cxx, but it's also applied for C in IDE,
        #  thus we remove it
        try: flags['c_flags'].remove("--no_vla")
        except ValueError: pass
        flags['c_flags'] =" ".join(flags['c_flags'])
        return flags

    def generate(self):
        """Generate the .uvproj file"""
        cache = Cache(True, False)
        if cache_d:
            cache.cache_descriptors()

        srcs = self.resources.headers + self.resources.s_sources + \
               self.resources.c_sources + self.resources.cpp_sources + \
               self.resources.objects + self.resources.libraries

        srcs = [self.uv_file(src) for src in srcs]
        self.add_config()
        ctx = {
            'name': self.project_name,
            'project_files': self.group_project_files(srcs),
            'linker_script':self.resources.linker_script,
            'include_paths': '; '.join(self.resources.inc_dirs).encode('utf-8'),
            'device': deviceCMSIS(self.target)
        }
        ctx.update(self.format_flags())
        self.gen_file('uvision/uvision.tmpl', ctx, self.project_name+".uvprojx")
