import argparse
import importlib
import inspect
import sys
from utils import log
from pathlib import Path
from utils.config_parser import SingletonConfig
import traceback

class TestExecutor:
    def __init__(self, continue_on_error=False):
        self.continue_on_error = continue_on_error
        self.testcases_path = Path(__file__).parent / "testcase"
        sys.path.insert(0, str(self.testcases_path))

    def load_testcase(self, case_name):
        try:
            module_name = case_name.rstrip('.py')
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

            return module
        except Exception as e:
            log.error(f"Load {case_name} failed: {str(e)}")
            raise

    def run_single_case(self, case_module):
        methods = ['setup', 'start_run', 'teardown']
        result = {'passed': True, 'errors': []}

        try:
            test_class = getattr(case_module, 'UnitTest')
            test_instance = test_class()

            for method in methods:
                if hasattr(test_instance, method):
                    func = getattr(test_instance, method)
                    log.debug(f"Executing UnitTest.{method}...")
                    func()
                else:
                    raise AttributeError(f"Method {method} not found in UnitTest class")
        except Exception as e:
            result['passed'] = False
            result['errors'].append({
                'method': method if 'method' in locals() else 'N/A',
                'exception': traceback.format_exc()
            })
            if not self.continue_on_error:
                raise
        return result

    def get_cases_from_txt(self):
        run_file = self.testcases_path / "run.txt"
        if not run_file.exists():
            raise FileNotFoundError("run.txt not found")
            
        with open(run_file) as f:
            return [line.strip() for line in f if line.strip()]

    def execute(self, specified_cases=None):
        cases_to_run = specified_cases or self.get_cases_from_txt()
        total_results = {'total': 0, 'passed': 0, 'failed': 0}
        
        for case in cases_to_run:
            total_results['total'] += 1
            try:
                module = self.load_testcase(case)
                result = self.run_single_case(module)
                
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
                log.error(f"🛑 Critical error in {case}: {str(e)}")
                if not self.continue_on_error:
                    sys.exit(1)

        print("\nExecution Summary:")
        print(f"Total cases: {total_results['total']}")
        print(f"Passed: {total_results['passed']}")
        print(f"Failed: {total_results['failed']}")

config = SingletonConfig('config.cfg')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Case Executor')
    parser.add_argument('cases', nargs='*', help='Specific testcase files to run')
    parser.add_argument('--continue', dest='continue_on_error', 
                      action='store_true', help='Continue on failure')
    
    args = parser.parse_args()


    specified_cases = [c.replace('.py', '') for c in args.cases]
    
    executor = TestExecutor(continue_on_error=args.continue_on_error)
    executor.execute(specified_cases or None)