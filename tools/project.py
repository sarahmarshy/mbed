import sys
from os.path import join, abspath, dirname, exists, basename
ROOT = abspath(join(dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from shutil import move, rmtree
from os import rename
from optparse import OptionParser

from tools.paths import EXPORT_DIR
from tools.export import EXPORTERS, mcu_ide_matrix
from tools.utils import args_error
from tools.tests import TESTS, TEST_MAP
from tools.targets import TARGET_NAMES
from project_api import get_program, setup_project, perform_export, print_results, get_test_from_name


if __name__ == '__main__':
    # Parse Options
    parser = OptionParser()

    targetnames = TARGET_NAMES
    targetnames.sort()
    toolchainlist = EXPORTERS.keys()
    toolchainlist.sort()

    parser.add_option("-m", "--mcu",
                      metavar="MCU",
                      default='LPC1768',
                      help="generate project for the given MCU (%s)"% ', '.join(targetnames))

    parser.add_option("-i",
                      dest="ide",
                      default='uvision',
                      help="The target IDE: %s"% str(toolchainlist))

    parser.add_option("-c", "--clean",
                      action="store_true",
                      default=False,
                      help="clean the export directory")

    parser.add_option("-p",
                      type="int",
                      dest="program",
                      help="The index of the desired test program: [0-%d]"% (len(TESTS)-1))

    parser.add_option("-n",
                      dest="program_name",
                      help="The name of the desired test program")

    parser.add_option("-b",
                      dest="build",
                      action="store_true",
                      default=False,
                      help="use the mbed library build, instead of the sources")

    parser.add_option("-L", "--list-tests",
                      action="store_true",
                      dest="list_tests",
                      default=False,
                      help="list available programs in order and exit")

    parser.add_option("-S", "--list-matrix",
                      action="store_true",
                      dest="supported_ides",
                      default=False,
                      help="displays supported matrix of MCUs and IDEs")

    parser.add_option("-E",
                      action="store_true",
                      dest="supported_ides_html",
                      default=False,
                      help="writes tools/export/README.md")

    parser.add_option("--source",
                      action="append",
                      dest="source_dir",
                      default=None,
                      help="The source (input) directory")

    parser.add_option("-D", "",
                      action="append",
                      dest="macros",
                      help="Add a macro definition")

    (options, args) = parser.parse_args()

    # Print available tests in order and exit
    if options.list_tests is True:
        print '\n'.join(map(str, sorted(TEST_MAP.values())))
        sys.exit()

    # Only prints matrix of supported IDEs
    if options.supported_ides:
        print mcu_ide_matrix()
        exit(0)

    # Only prints matrix of supported IDEs
    if options.supported_ides_html:
        html = mcu_ide_matrix(verbose_html=True)
        try:
            with open("./export/README.md","w") as f:
                f.write("Exporter IDE/Platform Support\n")
                f.write("-----------------------------------\n")
                f.write("\n")
                f.write(html)
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        exit(0)

    # Clean Export Directory
    if options.clean:
        if exists(EXPORT_DIR):
            rmtree(EXPORT_DIR)

    # Target
    if options.mcu is None :
        args_error(parser, "[ERROR] You should specify an MCU")
    mcus = options.mcu

    # IDE
    if options.ide is None:
        args_error(parser, "[ERROR] You should specify an IDE")
    ide = options.ide

    # Program Number or name
    p, n, src= options.program, options.program_name, options.source_dir

    if src is None:
        if p is not None and n is not None:
            args_error(parser, "[ERROR] specify either '-n' or '-p', not both")
        if n:
            p = get_test_from_name(n)
            if p is None:
                args_error(parser, "[ERROR] Program with name '%s' not found" % n)

        if p is None or (p < 0) or (p > (len(TESTS) - 1)):
            message = "[ERROR] You have to specify one of the following tests:\n"
            message += '\n'.join(map(str, sorted(TEST_MAP.values())))
            args_error(parser, message)

    # Export results
    successes = []
    failures = []

    # source is used to generate IDE files to toolchain directly in the source tree and doesn't generate zip file
    zip = src is None
    clean = src is None

    # source_dir = use relative paths, otherwise sources are copied
    sources_relative = True if options.source_dir else False

    for mcu in mcus.split(','):

        lib_symbols = []
        if options.macros:
            lib_symbols += options.macros
        project_dir, project_name, project_temp = setup_project(mcu,
                      ide,
                      p,
                      src,
                      options.macros,
                      options.build)

        tmp_path, report = perform_export(project_dir, project_name, ide, mcu,
                                          project_temp, clean, zip, lib_symbols,
                                          sources_relative)

        if report['success']:
            if not zip:
                zip_path = join(project_temp, project_name)
            else:
                zip_path = join(EXPORT_DIR, "%s_%s_%s.zip" % (project_name, ide, mcu))
                move(tmp_path, zip_path)

            successes.append("%s::%s\t%s"% (mcu, ide, zip_path))
        else:
            failures.append("%s::%s\t%s"% (mcu, ide, report['errormsg']))

    # Prints export results
    print_results(successes, failures)
