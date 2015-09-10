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
import os, tempfile
from os.path import join, exists, basename, dirname
from shutil import copytree, rmtree, copy
import yaml

from workspace_tools.utils import mkdir
from workspace_tools.export import zip
from workspace_tools.export.exporters import Exporter, zip_working_directory_and_clean_up
from workspace_tools.export import uvision4, gccarm,iar
from workspace_tools.targets import TARGET_NAMES, EXPORT_MAP



EXPORTERS = {
    'uvision': uvision4.Uvision4,
    'gcc_arm': gccarm.GccArm,
    'iar': iar.IAREmbeddedWorkbench
}



ERROR_MESSAGE_UNSUPPORTED_TOOLCHAIN = """
Sorry, the target %s is not currently supported on the %s toolchain.
Please refer to <a href='/handbook/Exporting-to-offline-toolchains' target='_blank'>Exporting to offline toolchains</a> for more information.
"""

ERROR_MESSAGE_NOT_EXPORT_LIBS = """
To export this project please <a href='http://mbed.org/compiler/?import=http://mbed.org/users/mbed_official/code/mbed-export/k&mode=lib' target='_blank'>import the export version of the mbed library</a>.
"""

def online_build_url_resolver(url):
    # TODO: Retrieve the path and name of an online library build URL
    return {'path':'', 'name':''}


def export(project_path, project_name, ide, target, destination='/tmp/',
           tempdir=None, clean=True, extra_symbols=None, build_url_resolver=online_build_url_resolver):
    # Convention: we are using capitals for toolchain and target names

    if tempdir is None:
        tempdir = tempfile.mkdtemp()

    report = {'success': False}

    if ide not in EXPORTERS:
        report["errormsg"] = "Unsupported toolchain"
    else:
        Exporter = EXPORTERS[ide]

    exporter = Exporter(target, build_url_resolver, extra_symbols)
    exporter.scan_and_copy_resources(project_path, tempdir)

    macro_yaml = {'macros':[]}
    macro_yaml['macros'].extend(exporter.get_symbols())

    macro_file_path = os.path.join(tempdir, "%s_macros.yaml"%target)
    with open(macro_file_path, 'w+') as f:
        f.write(yaml.dump(macro_yaml))

    current = os.getcwd()
    pgen_path = os.path.relpath("project_generator/main.py",tempdir)
    os.chdir(tempdir)
    pgen_command = "create -p %s -m %s"%(project_name, target)
    cmdline = "python %s %s"%(pgen_path,pgen_command)
    if os.system(cmdline) != 0:
        report["errormsg"] = "Could not create yaml"

    pgen_command = "-v generate -p %s -d %s -t %s"%(project_name, ide, macro_file_path)

    ide_settings = exporter.toolchain.yaml_options()
    if ide_settings is not None:
        settings_file_path = os.path.join(tempdir, "ide_settings.yaml")
        with open(settings_file_path, 'w+') as f:
            f.write(yaml.dump(ide_settings))

        pgen_command += " -s %s"%settings_file_path

    cmdline = "python %s %s"%(pgen_path,pgen_command)
    print cmdline
    if os.system(cmdline) != 0:
        report["errormsg"] = "Could not generate project file"
    report["success"] = True
    os.chdir(current)

    #copy(".project.yaml",tempdir)
    #copy(".projects.yaml",tempdir)

    #os.remove(".project.yaml")
   # os.remove(".projects.yaml")

    zip_path = None
    if report["success"]:
        # add readme file to every offline export.
        open(os.path.join(tempdir, 'GettingStarted.htm'),'w').write('<meta http-equiv="refresh" content="0; url=http://mbed.org/handbook/Getting-Started-mbed-Exporters#%s"/>'% (ide))
        # copy .hgignore file to exported direcotry as well.
        copy(os.path.join(dirname(__file__),'.hgignore'),tempdir)
        zip_path = zip_working_directory_and_clean_up(tempdir, destination, project_name, clean)

    return zip_path, report


###############################################################################
# Generate project folders following the online conventions
###############################################################################
def copy_tree(src, dst, clean=True):
    if exists(dst):
        if clean:
            rmtree(dst)
        else:
            return

    copytree(src, dst)


def setup_user_prj(user_dir, prj_path, lib_paths=None):
    """
    Setup a project with the same directory structure of the mbed online IDE
    """
    mkdir(user_dir)

    # Project Path
    copy_tree(prj_path, join(user_dir, "src"))

    # Project Libraries
    user_lib = join(user_dir, "lib")
    mkdir(user_lib)

    if lib_paths is not None:
        for lib_path in lib_paths:
            copy_tree(lib_path, join(user_lib, basename(lib_path)))

def mcu_ide_matrix(verbose_html=False, platform_filter=None):
    """  Shows target map using prettytable """
    supported_ides = []
    for key in EXPORTERS.iterkeys():
        supported_ides.append(key)
    supported_ides.sort()
    from prettytable import PrettyTable, ALL # Only use it in this function so building works without extra modules

    # All tests status table print
    columns = ["Platform"] + supported_ides
    pt = PrettyTable(columns)
    # Align table
    for col in columns:
        pt.align[col] = "c"
    pt.align["Platform"] = "l"

    perm_counter = 0
    target_counter = 0
    for target in sorted(TARGET_NAMES):
        target_counter += 1

        row = [target]  # First column is platform name
        for ide in supported_ides:
            text = "-"
            if target in EXPORTERS[ide].TARGETS:
                if verbose_html: 
                    text = "&#10003;" 
                else: 
                    text = "x"
                perm_counter += 1
            row.append(text)
        pt.add_row(row)

    pt.border = True
    pt.vrules = ALL
    pt.hrules = ALL
    # creates a html page suitable for a browser
    # result = pt.get_html_string(format=True) if verbose_html else pt.get_string()
    # creates a html page in a shorter format suitable for readme.md
    result = pt.get_html_string() if verbose_html else pt.get_string()
    result += "\n"
    result += "Total IDEs: %d\n"% (len(supported_ides))
    if verbose_html: result += "<br>"
    result += "Total platforms: %d\n"% (target_counter)
    if verbose_html: result += "<br>"
    result += "Total permutations: %d"% (perm_counter)
    if verbose_html: result = result.replace("&amp;", "&")
    return result
