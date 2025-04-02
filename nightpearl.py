import argparse
import importlib
import inspect
import sys
import gc
import re
from pathlib import Path
from utils.config_parser import ConfigManager
from utils.log import LoggerManager
from loguru import logger
import traceback
from pprint import pprint

global_config = ConfigManager('config.cfg')
log = LoggerManager()

class TestExecutor:
    def __init__(self, continue_on_error=False):
        self.continue_on_error = continue_on_error
        self.testcases_path = Path(__file__).parent / "testcase"
        sys.path.insert(0, str(self.testcases_path))
        self.global_config = global_config
    
    def pre_run_setup(self, case_name):
        self.global_config.set_exec_case_name(case_name)
        #pprint(log.__dict__)

    def load_testcase(self, case_name, relative_path=None):
        try:
            module_name = ".".join(relative_path.parts + (case_name.rstrip('.py'),))
            module = importlib.import_module(module_name)
            required_methods = ['setup', 'start_run', 'teardown']

            if not hasattr(module, 'UnitTest'):
                raise AttributeError(f"Module {module_name} does not contain UnitTest class")

            UnitTestClass = getattr(module, 'UnitTest')
            class_methods = [name for name, _ in inspect.getmembers(UnitTestClass, inspect.isfunction)]
            log.debug(class_methods)

            for method in required_methods:
                if not method in class_methods:
                    raise AttributeError(f"UnitTest class missing required method: {method}")

            self.pre_run_setup(case_name)

            return module
        except Exception as e:
            log.error(f"Load {case_name} failed: {str(e)}")
            raise

    def run_single_case(self, case_module, case_name, exec_times):
        methods = ['setup', 'start_run', 'teardown']
        result = {'passed': True, 'errors': []}
        teardown_executed = False

        try:
            test_class = getattr(case_module, 'UnitTest')
            test_instance = test_class()

            while exec_times != 0:
                for method in methods:
                    if hasattr(test_instance, method):
                        func = getattr(test_instance, method)
                        log.debug(f"Executing UnitTest.{method}...")
                        with log.case_context(case_name):
                            func()
                    else:
                        raise AttributeError(f"Method {method} not found in UnitTest class")
                    if method == 'teardown':
                        teardown_executed = True
                exec_times -= 1

        except Exception as e:
            result['passed'] = False
            result['errors'].append({
                'method': method if 'method' in locals() else 'N/A',
                'exception': traceback.format_exc()
            })
            if not self.continue_on_error:
                raise
        finally:
            if not teardown_executed and test_instance and hasattr(test_instance, 'teardown'):
                try:
                    test_instance.teardown()
                except Exception as e:
                    log.error(f"Teardown failed: {str(e)}")
            if test_instance:
                if hasattr(test_instance, '__del__'):
                    try:
                        test_instance.__del__()
                    except Exception as e:
                        log.error(f"__del__ error: {str(e)}")
                del test_instance
            gc.collect()
        return result

    # 跳过#开头行, 匹配数字为执行次数,空值默认为1
    def parse_case_name(self, raw_name):
        trimmed = raw_name.strip()
        if not trimmed or trimmed.startswith('#'):
            return None, 0
        match = re.match(r'^(.+?)\s+(-?\d+)$', trimmed)
        if match:
            base_name = match.group(1).strip()
            exec_times = int(match.group(2))
            return base_name, exec_times
        else:
            return trimmed, 1

    def get_cases_from_all_dirs(self):
        cases = []
        for run_file in self.testcases_path.rglob("run.txt"):
            context_dir = run_file.parent
            with open(run_file, 'r', encoding='utf-8') as f:
                for line in f:
                    raw_name = line.strip()
                    if not raw_name:
                        continue
                    case_name, exec_times = self.parse_case_name(raw_name)

                    if case_name == None or exec_times == 0: 
                        continue

                    relative_path = context_dir.relative_to(self.testcases_path)
                    cases.append((relative_path, case_name, exec_times)) 
        return cases

    def get_cases_from_txt(self):
        run_file = self.testcases_path / "run.txt"
        if not run_file.exists():
            raise FileNotFoundError("run.txt not found")

        with open(run_file) as f:
            return [line.strip() for line in f if line.strip()]

    def execute(self, specified_cases=None):
        print(self.get_cases_from_all_dirs())
        if specified_cases != None:
            cases_to_run = [specified_cases]
        else:
            cases_to_run = self.get_cases_from_all_dirs()

        total_results = {'total': 0, 'passed': 0, 'failed': 0}

        for relative_path, case, exec_times in cases_to_run:
            total_results['total'] += 1
            try:
                module = self.load_testcase(case, relative_path)
                result = self.run_single_case(module, case, exec_times)

                if result['passed']:
                    total_results['passed'] += 1
                    log.info(f"✅ {case} PASSED")
                else:
                    total_results['failed'] += 1
                    log.error(f"❌ {case} FAILED")
                    for error in result['errors']:
                        log.error(f"Error in {error['method']}:\n{error['exception']}")
                    if not self.continue_on_error:
                        break
            except Exception as e:
                log.error(f"🛑 Critical error in {case}:")
                logger.exception("An error occurred")
                if not self.continue_on_error:
                    sys.exit(1)

        log.info(f"Execution Summary:")
        log.info(f"Total cases: {total_results['total']}")
        log.info(f"Passed: {total_results['passed']}")
        log.info(f"Failed: {total_results['failed']}")

def config_log_init(log, config):
    log.log_dir = config.log.log_dir
    log.loglevel = config.log.loglevel
    log.rotation = config.log.rotation
    log.retention = config.log.retention


def config_init():
    config_log_init(log, global_config)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Case Executor')
    parser.add_argument('cases', nargs='*', help='Specific testcase files to run')
    parser.add_argument('--continue', dest='continue_on_error', 
                      action='store_true', help='Continue on failure')

    args = parser.parse_args()

    config_init()

    specified_cases = [c.replace('.py', '') for c in args.cases]
    
    executor = TestExecutor(continue_on_error=args.continue_on_error)
    executor.execute(specified_cases or None)