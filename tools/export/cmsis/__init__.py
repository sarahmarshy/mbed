import os
from os.path import sep
from itertools import groupby
from xml.etree.ElementTree import Element, tostring
from xml.dom.minidom import parseString
import ntpath

from ArmPackManager import Cache

from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter

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

class deviceCMSIS():
    def __init__(self, target, use_generic_cpu=False):
        cache = Cache(True, False)
        if cache_d:
            cache.cache_descriptors()

        t = TARGET_MAP[target]
        cpu_name = t.cmsis_device
        target_info = cache.index[cpu_name]
        if use_generic_cpu:
            cpu_name = self.cpu_cmsis(t.core)
            cpu_info = cache.index[cpu_name]
        else:
            cpu_info = target_info

        self.url = cpu_info['pdsc_file']
        self.pack_url, self.pack_id = ntpath.split(self.url)
        self.dname = cpu_name
        self.dfpu = cpu_info['processor']['fpu']
        self.dvendor = cpu_info['vendor']
        self.dendian = cpu_info['processor']['endianness']
        algo = target_info['algorithm']
        self.algorithm = {
            'name': algo['name'], 
            'start': algo['start'],
            'size': algo['size'],
            'RAMstart': algo['RAMstart'],
            'RAMsize' : algo['RAMsize']
        }
        target_info['debug'] = target_info.get('debug', '')
        self.svd = deviceCMSIS.format_debug(cpu_name, target_info['debug'])
        self.reg_file = deviceCMSIS.format_reg_file(cpu_name,
                                                    target_info['compile']['header'])


    @staticmethod
    def format_debug(device_name=None, debug_file=None):
        if debug_file == '': return ''
        sfd = "$$Device:{0}${1}"
        return sfd.format(device_name, debug_file)

    @staticmethod
    def format_reg_file(device_name, include_file):
        reg_file = "$$Device:{0}${1}"
        return reg_file.format(device_name, include_file)

    def cpu_cmsis(self, cpu):
        cpu = cpu.replace("Cortex-","ARMC")
        cpu = cpu.replace("+","P")
        cpu = cpu.replace("F","_FP")
        return cpu

class CMSIS(Exporter):
    NAME = 'cmsis'
    TOOLCHAIN = 'ARM'
    TARGETS = [target for target, obj in TARGET_MAP.iteritems()
               if "ARM" in obj.supported_toolchains]

    def make_key(self, src):
        """turn a source file into its group name"""
        key = src.name.split(sep)[0]
        if key == ".":
            key = os.path.basename(os.path.realpath(self.export_dir))
        return key

    def group_project_files(self, sources, root_element):
        """Recursively group the source files by their encompassing directory"""

        data = sorted(sources, key=self.make_key)
        for group, files in groupby(data, self.make_key):
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

        srcs = self.resources.headers + self.resources.s_sources + \
               self.resources.c_sources + self.resources.cpp_sources + \
               self.resources.objects + self.resources.libraries + \
               [self.resources.linker_script]
        srcs = [fileCMSIS(src, src) for src in srcs]
        ctx = {
            'name': self.project_name,
            'project_files': tostring(self.group_project_files(srcs, Element('files'))),
            'device': deviceCMSIS(self.target),
            'debug_interface': 'CMSIS-DAP',
            'debug_protocol': 'jtag',
            'date': ''
        }
        dom = parseString(ctx['project_files'])
        ctx['project_files'] = dom.toprettyxml(indent="\t")


        self.gen_file('cmsis/cpdsc.tmpl', ctx, 'project.cpdsc')
