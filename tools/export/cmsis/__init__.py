import os
from os.path import sep, join, exists
from itertools import groupby
from xml.etree.ElementTree import Element, tostring
import ntpath
import re
import json

from tools.arm_pack_manager import Cache
from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter

class fileCMSIS():
    """CMSIS file class.

    Encapsulates information necessary for files in cpdsc project file"""
    file_types = {'.cpp': 'sourceCpp', '.c': 'sourceC', '.s': 'sourceAsm',
                  '.obj': 'object', '.o': 'object', '.lib': 'library',
                  '.ar': 'linkerScript', '.h': 'header', '.sct': 'linkerScript'}

    def __init__(self, loc, name):
        #print loc
        _, ext = os.path.splitext(loc)
        self.type = self.file_types[ext.lower()]
        self.loc = loc
        self.name = name


class DeviceCMSIS():
    """CMSIS Device class

    Encapsulates target information retrieved by arm-pack-manager"""


    MISSING_DNAME = ("A 'device_name' field for %s in 'targets/targets.json' is required "
                    "to export to this IDE. Please add a valid CMSIS pack "
                    "device name to this target's description. See the 'device_name' "
                    "section of 'docs/mbed_targets.md' "
                    "for more information.")

    DNAME_NOT_IN_CMSIS = ("[WARNING] The 'device_name' %s for %s as listed in targets/targets.json is "
                         "not present in any CMSIS pack. Please check support according "
                         "to the 'device_name' section of docs/mbed_targets.md. "
                         "\nAttempting to resolve target to generic ARM core...")

    CPU_ERROR = "Could not find %s as a CMSIS target."


    CACHE = Cache(True, False)
    def __init__(self, target):
        target_info = DeviceCMSIS.check_supported(TARGET_MAP[target], verbose=False)[1]
        self.url = target_info['pdsc_file']
        self.pack_url, self.pack_id = ntpath.split(self.url)
        self.dname = target_info["_cpu_name"]
        self.core = target_info["_core"]
        self.dfpu = target_info['processor']['fpu']
        self.debug, self.dvendor = self.vendor_debug(target_info['vendor'])
        self.dendian = target_info['processor'].get('endianness','Little-endian')
        self.debug_svd = target_info.get('debug', '')
        self.compile_header = target_info['compile']['header']
        self.target_info = target_info

    @staticmethod
    def check_supported(target, verbose=True):
        """Checks if a target has relevent CMSIS PDSC file

        Positional arguments:
        target - the target to determine support for
        Keyword arguments:
        verbose - print warning/status messages

        On success: Returns (True, target info found in CMSIS packs)
        On fail: Returns (False, reason it is not supported)
        """

        #Check if the target has a devie_name
        if not hasattr(target, "device_name"):
            #It doesn't, so there is no possiblity of finding it in a CMSIS pack
            #Return that it is not supported and message explaining why
            return (False,DeviceCMSIS.MISSING_DNAME%target.name)

        #Get the target's device name
        cpu_name = target.device_name
        try:
            #Check if it has information in the cache
            target_info = DeviceCMSIS.CACHE.index[cpu_name]
        # Target does not have device name or pdsc file
        except:
            if verbose:
                #We can't find the device information in CMSIS PDSC
                print DeviceCMSIS.DNAME_NOT_IN_CMSIS%(cpu_name,target.name,)
            #We will now try to find the target's core in CMSIS Packs

            #Format the core in the way CMSIS packs lists them
            cpu_name = DeviceCMSIS.cpu_cmsis(target.core)
            try:
                # Try to find the core as a CMSIS target
                target_info = DeviceCMSIS.CACHE.index[cpu_name]
            except:
                #The core does not have information either
                #Return that this target is conclusively not supported, and
                #a message explaining why
                return (False, DeviceCMSIS.CPU_ERROR%cpu_name)
            else:
                #We have found the core as a CMSIS device
                if verbose:
                    print "SUCCESS! Setting %s as target."%cpu_name
        target_info["_cpu_name"] = cpu_name
        target_info["_core"] = target.core
        return (True,target_info)

    def vendor_debug(self, vendor):
        reg = "([\w\s]+):?\d*?"
        m = re.search(reg, vendor)
        vendor_match = m.group(1) if m else None
        debug_map ={
            'STMicroelectronics':'ST-Link',
            'Silicon Labs':'J-LINK',
            'Nuvoton':'NULink'
        }
        return debug_map.get(vendor_match, "CMSIS-DAP"), vendor_match

    @staticmethod
    def cpu_cmsis(cpu):
        #Cortex-M4F => ARMCM4_FP, Cortex-M0+ => ARMCM0P
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
        srcs = [fileCMSIS(src, src) for src in srcs if src]
        ctx = {
            'name': self.project_name,
            'project_files': tostring(self.group_project_files(srcs, Element('files'))),
            'device': DeviceCMSIS(self.target),
            'date': ''
        }
        # TODO: find how to keep prettyxml from adding xml version to this blob
        #dom = parseString(ctx['project_files'])
        #ctx['project_files'] = dom.toprettyxml(indent="\t")

        self.gen_file('cmsis/cpdsc.tmpl', ctx, 'project.cpdsc')
