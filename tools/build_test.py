from export import EXPORTERS
from targets import TARGET_NAMES
from os import environ
from project_api import get_program, setup_project, perform_export, print_results

class BuildTest():
    def __init__(self):

        #environ["IARBUILD"] = ""
        desired_ides = ['iar', 'uvision5']
        self.target_ides = {}
        for target in sorted(TARGET_NAMES):
            self.target_ides[target] =[]
            for ide in desired_ides:
                if target in EXPORTERS[ide].TARGETS:
                    self.target_ides[target].append(ide)
            if len(self.target_ides[target]) == 0:
                del self.target_ides[target]

        self.successes = []
        self.failures = []
        self.generate_and_build([0])
        print_results(self.successes, self.failures)

    def generate_and_build(self, tests):
        for mcu, ides in self.target_ides.items():
            for test in tests:
                for ide in ides:
                    project_dir, project_name, project_temp = setup_project(mcu, ide, test)
                    tmp_path, report = perform_export(project_dir, project_name, ide, mcu, project_temp,
                                                      progen_build = True)
                    if report['success']:
                        self.successes.append("%s::%s\t%s" % (mcu, ide, project_name))
                    else:
                        self.failures.append("%s::%s\t%s" % (mcu, ide, report['errormsg']))


if __name__ == '__main__':
    b = BuildTest()


