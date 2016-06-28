import sys
from os.path import join, abspath, dirname, exists, basename
ROOT = abspath(join(dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from os import path

from tools.paths import EXPORT_WORKSPACE, EXPORT_TMP
from tools.paths import MBED_BASE, MBED_LIBRARIES
from tools.export import export, setup_user_prj
from tools.utils import mkdir
from tools.tests import Test, TEST_MAP
from tools.libraries import LIBRARIES


def get_program(n):
    p = TEST_MAP[n].n
    return p


def get_test(p):
    return Test(p)


def setup_project(mcu, ide, program = None, source_dir= None, macros = None, build = None):
    lib_symbols = []
    if macros:
        lib_symbols += macros
    if source_dir is not None:
        project_dir = source_dir
        project_name = program if program else "Unnamed_Project"
        project_temp = path.join(source_dir[0], 'projectfiles', '%s_%s' % (ide, mcu))
        mkdir(project_temp)
    else:
        test = get_test(program)
        for lib in LIBRARIES:
            if lib['build_dir'] in test.dependencies:
                lib_macros = lib.get('macros', None)
                if lib_macros is not None:
                    lib_symbols.extend(lib_macros)

        if not build:
            # Substitute the library builds with the sources
            # TODO: Substitute also the other library build paths
            if MBED_LIBRARIES in test.dependencies:
                test.dependencies.remove(MBED_LIBRARIES)
                test.dependencies.append(MBED_BASE)

        project_name = test.id
        project_dir = [join(EXPORT_WORKSPACE, project_name)]
        project_temp = EXPORT_TMP
        setup_user_prj(project_dir[0], test.source_dir, test.dependencies)

    return project_dir, project_name, project_temp


def perform_export(dir, name, ide, mcu, temp, clean = True, zip = True, lib_symbols = '',
                   sources_relative = False, progen_build = False):
    tmp_path, report = export(dir, name, ide, mcu, dir[0], temp, clean=clean,
                              make_zip=zip, extra_symbols=lib_symbols, sources_relative=sources_relative,
                              progen_build = progen_build)
    return tmp_path, report


def print_results(successes, failures):
    print
    if len(successes) > 0:
        print "Successful exports:"
        for success in successes:
            print "  * %s" % success
    if len(failures) > 0:
        print "Failed exports:"
        for failure in failures:
            print "  * %s" % failure

