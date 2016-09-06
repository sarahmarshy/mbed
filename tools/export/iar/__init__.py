import os
from os.path import sep, join
from collections import namedtuple

from tools.targets import TARGET_MAP
from tools.export.exporters import Exporter
import json
class IAR(Exporter):
    NAME = 'iar'
    TOOLCHAIN = 'IAR'

    def_loc = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
        'tools','export', 'iar', 'iar_definitions.json')

    with open(def_loc, 'r') as f:
        IAR_DEFS = json.load(f)
    TARGETS = [target for target, obj in TARGET_MAP.iteritems()
               if hasattr(obj, 'device_name') and
               obj.device_name in IAR_DEFS.keys()]

    SPECIAL_TEMPLATES = {
        'rz_a1h'  : 'iar/iar_rz_a1h.ewp.tmpl',
        'nucleo_f746zg.ewp.tmpl' : 'iar/iar_rz_a1h.ewp.tmpl'
    }

    def iar_groups(self, grouped_src):
        """Return a namedtuple of group info
        Positional Arguments:
        grouped_src: dictionary mapping a group(str) to sources
            within it (list of file names)
        Relevant part of IAR template
        {% for group in groups %}
	    <group>
	        <name>group.name</name>
	        {% for file in group.files %}
	        <file>
	        <name>$PROJ_DIR${{file}}</name>
	        </file>
	        {% endfor %}
	    </group>
	    {% endfor %}
        """
        IARgroup = namedtuple('IARgroup', ['name','files'])
        groups = []
        for name, files in grouped_src.items():
            groups.append(IARgroup(name,files))
        return groups

    def iar_device(self):
        device_name =  TARGET_MAP[self.target].device_name
        device_info = self.IAR_DEFS[device_name]
        iar_defaults ={
            "OGChipSelectEditMenu": "",
            "CoreVariant": '',
            "GFPUCoreSlave": '',
            "GFPUCoreSlave2": 40,
            "GBECoreSlave": 35
        }

        iar_defaults.update(device_info)
        IARdevice = namedtuple('IARdevice', iar_defaults.keys())
        return IARdevice(**iar_defaults)

    def format_file(self, file):
        return join('$PROJ_DIR$',file)

    def format_src(self, srcs):
        grouped = self.group_project_files(srcs)
        for group, files in grouped.items():
            grouped[group] = [self.format_file(src) for src in files]
        return grouped

    def get_ewp_template(self):
        return self.SPECIAL_TEMPLATES.get(self.target.lower(), 'iar/ewp.tmpl')

    def generate(self):
        """Generate the .ww and .ewp files"""

        srcs = self.resources.headers + self.resources.s_sources + \
               self.resources.c_sources + self.resources.cpp_sources + \
               self.resources.objects + self.resources.libraries
        flags = self.flags
        flags['c_flags'] = list(set(flags['common_flags']
                                    + flags['c_flags']
                                    + flags['cxx_flags']))
        flags['c_flags'].remove('--vla')
        ctx = {
            'name': self.project_name,
            'groups': self.iar_groups(self.format_src(srcs)),
            'linker_script': self.format_file(self.resources.linker_script),
            'include_paths': [self.format_file(src) for src in self.resources.inc_dirs],
            'device': self.iar_device(),
            'ewp': sep+self.project_name + ".ewp"
        }
        ctx.update(flags)

        self.gen_file('iar/eww.tmpl', ctx, self.project_name+".eww")
        self.gen_file(self.get_ewp_template(), ctx, self.project_name + ".ewp")
