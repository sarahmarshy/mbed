from export import EXPORTERS
from targets import TARGET_NAMES
from tools.paths import EXPORT_DIR, EXPORT_WORKSPACE, EXPORT_TMP
from os.path import join
from tools.export import export, setup_user_prj
from shutil import move
from project_api import get_program, setup_project, perform_export, print_results

class BuildTest():
    def __init__(self):
        desired_ides = ['uvision5','iar','gcc_arm']
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
        print_results(self.success, self.failures)

    def generate_and_build(self, tests):
        for mcu, ides in self.target_ides.items():
            for test in tests:
                for ide in ides:
                    project_dir, project_name, project_temp = setup_project(mcu, ide, test)
                    tmp_path, report = perform_export(project_dir, project_name, ide, mcu, project_temp)
                    if report['success']:

                        zip_path = join(project_temp, project_name)
                        path = join(EXPORT_DIR, "%s_%s_%s" % (project_name, ide, mcu))
                        move(tmp_path, path)
                        self.successes.append("%s::%s\t%s" % (mcu, ide, path))
                    else:
                        self.failures.append("%s::%s\t%s" % (mcu, ide, report['errormsg']))


if __name__ == '__main__':
    b = BuildTest()


