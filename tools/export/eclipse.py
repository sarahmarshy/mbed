from os.path import join, dirname, exists, realpath, relpath, basename
from os import makedirs

from tools.export.gccarm import GccArm
from distutils.spawn import find_executable

class Eclipse(GccArm):
    def generate(self):
        ctx = {
            'name': self.project_name,
            'elf_location': join('.build',self.target,
                                 'GCC_ARM',self.project_name)+'.elf',
            'c_symbols': self.toolchain.get_symbols(),
            'asm_symbols': self.toolchain.get_symbols(True),
            'pyocd_gdb_exe_loc': find_executable('pyocd-gdbserver.exe'),
            'target': self.target
        }
        for f,bp in self.resources.file_basepath.items():
            self.resources.file_basepath[realpath(f)] = realpath(bp)
        ctx['include_paths'] = []
        for inc in self.resources.inc_dirs:
            i = realpath(join(self.export_dir,inc))
            bp = self.resources.file_basepath[realpath(i)]
            res_path = join(basename(bp), relpath(i, bp))
            ctx['include_paths'].append(res_path)

        if not ctx['pyocd_gdb_exe_loc']:
            raise Exception("Could not find pyocd-gdbserver.exe")

        if not exists(join(self.export_dir,'extras')):
            makedirs(join(self.export_dir,'extras'))


        self.gen_file('py_ocd_settings.tmpl', ctx,
                      join('extras',self.target+'_py_ocd_settings.launch'))
        self.gen_file('necessary_software.tmpl', ctx,
                      join('extras','necessary_software.p2f'))

        cproj = relpath('.cproject',self.export_dir)
        self.gen_file('.cproject.tmpl', ctx,
                      cproj)
        proj = relpath('.project',self.export_dir)
        self.gen_file('.project.tmpl', ctx,
                      proj)





