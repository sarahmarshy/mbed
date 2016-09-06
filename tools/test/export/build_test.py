#!/usr/bin/env python
"""
mbed SDK
Copyright (c) 2011-2016 ARM Limited

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

import sys
from os import path
ROOT = path.abspath(path.join(path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
import argparse
import sys


from tools.paths import EXPORT_DIR
from tools.targets import TARGET_NAMES
from tools.tests import TESTS, TEST_MAP
from tools.test_api import find_tests
from tools.project import export
from Queue import Queue
from threading import Thread, Lock
from tools.project_api import print_results
from tools.tests import test_name_known, test_known, Test
from tools.export.exporters import FailedBuildException, \
                                   TargetNotSupportedException
from tools.utils import argparse_force_lowercase_type, \
                        argparse_many, columnate
from argparse import ArgumentTypeError

print_lock = Lock()


def do_queue(Class, function, interable) :
    q = Queue()
    threads = [Class(q, function) for each in range(20)]
    for thing in interable :
        q.put(thing)
    for each in threads :
        each.setDaemon(True)
        each.start()
    q.join()


class Reader (Thread) :
    def __init__(self, queue, func) :
        Thread.__init__(self)
        self.queue = queue
        self.func = func

    def start(self) :
        sys.stdout.flush()
        while not self.queue.empty() :
            test = self.queue.get()
            self.func(test)
            self.queue.task_done()


class TestCase():
    """Object to encapsulate a test case"""
    def __init__(self, ide, mcu, name, test_num=None, src=None):
        """
        Initialize an instance of class TestCase
        Args:
            ide: ide for test
            mcu: mcu for test
            name: name of test
            test_num: Test.n of Test object class from tools.tests
            src: location of source for test
        """
        self.ide = ide
        self.mcu = mcu
        self.name = name
        self.id = test_num
        self.src = src


class ProgenBuildTest(object):
    """Object to encapsulate logic for progen build testing"""
    def __init__(self, tests, clean=False):
        """
        Initialize an instance of class ProgenBuildTest
        Args:
            tests: array of TestCase instances
            clean: clean up the tests' project files and logs
        """
        self.total = len(tests)
        self.counter  = 0
        self.successes = []
        self.failures = []
        self.skips = []
        self.tests = tests
        self.clean=clean
        self.build_queue = Queue()

    def batch_tests(self):
        """Performs all exports of self.tests
        Peroform_exports will fill self.build_queue.
        This function will empty self.build_queue and call the test's
        IDE's build function."""
        do_queue(Reader, self.perform_exports, self.tests)
        self.counter = 0
        while not self.build_queue.empty():
            build = self.build_queue.get()
            self.counter +=1
            exporter = build[0]
            test_case = build[1]
            self.display_counter("Building test case  %s::%s\t%s"
                                 % (test_case.mcu,
                                    test_case.ide,
                                    test_case.name))
            try:
                exporter.build()
            except FailedBuildException:
                self.failures.append("%s::%s\t%s" % (test_case.mcu,
                                                     test_case.ide,
                                                     test_case.name))
            else:
                self.successes.append("%s::%s\t%s" % (test_case.mcu,
                                                      test_case.ide,
                                                      test_case.name))

    def display_counter (self, message) :
        with print_lock:
            sys.stdout.write("{}/{} {}".format(self.counter, self.total,
                                               message) +"\n")
            sys.stdout.flush()

    def perform_exports(self, test_case):
        """
        Generate the project file for test_case and fill self.build_queue
        Args:
            test_case: object of type TestCase
        """
        sys.stdout.flush()
        self.counter += 1
        name_str = ('%s_%s_%s') % (test_case.mcu, test_case.ide, test_case.name)
        self.display_counter("Exporting test case  %s::%s\t%s" % (test_case.mcu,
                                                                  test_case.ide,
                                                                  test_case.name))

        try:
            exporter = export(test_case.mcu, test_case.ide,
                              project_id=test_case.id, zip_proj=None,
                              clean=self.clean, src=test_case.src,
                              export_path=path.join(EXPORT_DIR,name_str),
                              silent=True)
            self.build_queue.put((exporter,test_case))
        except TargetNotSupportedException:
            self.skips.append("%s::%s\t%s" % (test_case.mcu, test_case.ide,
                                              test_case.test_name))

def main():
    """Entry point"""
    all_os_tests = find_tests(ROOT, "K64F", "ARM")
    #Check if the specified name is in all_os_tests
    def check_valid_mbed_os(test):
        """Check if the specified name is in all_os_tests
        args:
            test: string name to index all_os_tests
        returns: tuple of test_name and source location of test,
            as given by find_tests"""
        if test in all_os_tests.keys():
            return (test, all_os_tests[test])
        else:
            raise ArgumentTypeError("Program with name '{0}' not found. "
                                    "Supported tests are: \n{1}".format(test,
                                     columnate([t for t in all_os_tests.keys()])))

    ide_list = ["iar", "uvision", "uvision5"]

    default_tests = [test_name_known("MBED_BLINKY")]
    mbed_os_default = [check_valid_mbed_os('tests-mbedmicro-rtos-mbed-basic')]

    targetnames = TARGET_NAMES
    targetnames.sort()

    parser = argparse.ArgumentParser(description=
                                     "Test progen builders. Leave any flag off"
                                     " to run with all possible options.")
    parser.add_argument("-i",
                        dest="ides",
                        default=ide_list,
                        type=argparse_many(argparse_force_lowercase_type(
                            ide_list, "toolchain")),
                        help="The target IDE: %s"% str(ide_list))

    parser.add_argument( "-p",
                        type=argparse_many(test_known),
                        dest="programs",
                        help="The index of the desired test program: [0-%d]"
                             % (len(TESTS) - 1),
                        default=default_tests)

    parser.add_argument("-n",
                        type=argparse_many(test_name_known),
                        dest="programs",
                        help="The name of the desired test program",
                        default=default_tests)

    parser.add_argument("-m", "--mcus",
                        nargs='+',
                        dest="targets",
                        default=[])

    parser.add_argument("-os-tests",
                        type=argparse_many(check_valid_mbed_os),
                        dest="os_tests",
                        help="Mbed-os tests",
                        default=mbed_os_default)

    parser.add_argument("-c", "--clean",
                        dest="clean",
                        action="store_true",
                        help="clean up the exported project files",
                        default=False)

    options = parser.parse_args()

    tests = []
    for mcu in options.targets:
        for ide in options.ides:
            # add each test case to the tests array
            for test in options.programs:
                tests.append(TestCase(ide, mcu, TESTS[test]["id"],
                                      test_num=test))
            for test in options.os_tests:
                tests.append(TestCase(ide, mcu, test[0], src=[test[1],ROOT]))
    test = ProgenBuildTest(tests, clean=options.clean)
    test.batch_tests()
    print_results(test.successes, test.failures, test.skips)
    sys.exit(len(test.failures))

if __name__ == "__main__":
    main()