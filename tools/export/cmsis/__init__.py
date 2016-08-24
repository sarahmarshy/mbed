import os
from os.path import sep
from itertools import groupby
from xml.etree.ElementTree import Element, tostring

from ArmPackManager import Cache

from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter
import yaml

cache_d = False


class fileCMSIS():
    file_types = {'.cpp': 'sourceCpp', '.c': 'sourceC', '.s': 'sourceAsm',
                  '.obj': 'object', '.o': 'object', '.lib': 'library',
                  '.ar': 'linkerScript', '.h': 'header', '.sct': 'linkerScript'}

    def __init__(self, loc, name):
        _, ext = os.path.splitext(loc)
        self.type = self.file_types[ext.lower()]
        self.loc = loc
        self.name = name

class CMSIS(Exporter):
    NAME = 'cmsis'
    TOOLCHAIN = 'ARM'
    TARGETS = [target for target, obj in TARGET_MAP.iteritems()
               if "ARM" in obj.supported_toolchains]

    def group_project_files(self, sources, root_element):
        """Recursively roup the source files by their encompassing directory"""
        def make_key(src):
            """turn a source file into it's group name"""
            key = src.name.split(sep)[0]
            if key == ".":
                key = os.path.basename(os.path.realpath(self.export_dir))
            return key

        data = sorted(sources, key=make_key)
        for group, files in groupby(data, make_key):
            new_srcs = []
            for f in list(files):
                spl = f.name.split(sep)
                if len(spl)==2:
                    file_element = Element('file',
                                           attrib={
                                               'category':f.type,
                                               'name': f.loc})
                    root_element.append(file_element)
                else:
                    f.name = os.path.join(*spl[1:])
                    new_srcs.append(f)
            if new_srcs:
                group_element = Element('group',attrib={'name':group})
                root_element.append(self.group_project_files(new_srcs,
                                                        group_element))
        return root_element

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
        srcs = [fileCMSIS(src, src) for src in srcs]
        ctx = {
            'name': self.project_name,
            'project_files': tostring(self.group_project_files(srcs, Element('files'))),
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
