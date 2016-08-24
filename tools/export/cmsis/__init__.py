import os
from itertools import groupby

from ArmPackManager import Cache

from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter

cache_d = False


class CMSIS(Exporter):
    NAME = 'cmsis'
    TOOLCHAIN = 'ARM'
    TARGETS = [target for target, obj in TARGET_MAP.iteritems()
               if "ARM" in obj.supported_toolchains]

    def get_project_files(self, sources):
        """Group the source files by their encompassing directory"""
        class file():
            file_types = {'.cpp': 'sourceCpp', '.c': 'sourceC', '.s': 'sourceAsm',
                          '.obj': 'object', '.o': 'object', '.lib': 'library',
                          '.ar': 'linkerScript', '.h': 'header', '.sct': 'linkerScript'}

            def __init__(self, loc):
                _, ext = os.path.splitext(loc)
                self.type = self.file_types[ext.lower()]
                self.loc = loc

        def make_key(src):
            """turn a source file into it's group name"""
            key = os.path.basename(os.path.dirname(src.loc))
            if not key:
                key = os.path.basename(os.path.normpath(self.export_dir))
            return key

        sources = [file(src) for src in sources]
        data = sorted(sources, key=make_key)
        return {k: list(g) for k, g in groupby(data, make_key)}

    def generate(self):
        cache = Cache(True, False)
        if cache_d:
            cache.cache_descriptors()
        t = TARGET_MAP[self.target]
        for label in t.extra_labels:
            try:
                target_info = cache.index[label]
                targ = label
                break
            except:
                pass
        else:
            raise Exception("Not found")

        srcs = self.resources.headers + self.resources.s_sources + \
               self.resources.c_sources + self.resources.cpp_sources + \
               self.resources.objects + self.resources.libraries + \
               [self.resources.linker_script]
        ctx = {
            'name': self.project_name,
            'project_files': self.get_project_files(srcs),
            'pdsc_url': target_info['pdsc_file'],
            'pdsc_package': '',
            'dendian': target_info['processor']['endianness'],
            'dfpu': target_info['processor']['fpu'],
            'dvendor': target_info['vendor'],
            'debug_interface': 'CMSIS-DAP',
            'debug_protocol': 'jtag',
            'date': '',
            'target': targ
        }
        self.gen_file('cmsis/cpdsc.tmpl', ctx, 'project.cpdsc')
