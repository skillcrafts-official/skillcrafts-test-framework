import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
import traceback

from json import JSONDecodeError
from requests import RequestException


@dataclass
class TestStepResult:
    """Результат выполнения тестового шага"""
    step_number: int
    description: str
    expected_result: str
    actual_result: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class TestStep:
    """Контекстный менеджер для тестового шага"""
    
    def __init__(self, description: str, expected_result: str, step_number: Optional[int] = None):
        self.description = description
        self.expected_result = expected_result
        self.step_number = step_number
        self.start_time = None
        self.end_time = None
        self.status = 'skipped'
        self.actual_result = ''
        self.error_message = None
        self.screenshot_path = None
        self._parent_case = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.status = 'running'
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        
        if exc_type is None:
            self.status = 'passed'
            self.actual_result = self.expected_result
        elif exc_type is AssertionError:
            self.status = 'failed'
            self.actual_result = f"Assertion failed: {exc_val}"
            self.error_message = str(exc_val)
        else:
            self.status = 'error'
            self.actual_result = f"Error: {exc_val}"
            self.error_message = traceback.format_exc()
        
        # Возвращаем True для assertion errors, чтобы не прерывать тест
        return exc_type is AssertionError
    
    def set_screenshot(self, path: str):
        """Добавить скриншот к шагу"""
        self.screenshot_path = path
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_result(self) -> TestStepResult:
        """Конвертировать в объект результата"""
        return TestStepResult(
            step_number=self.step_number or 0,
            description=self.description,
            expected_result=self.expected_result,
            actual_result=self.actual_result,
            status=self.status,
            duration=self.duration,
            error_message=self.error_message,
            screenshot_path=self.screenshot_path
        )


class TestCase:
    """Контекстный менеджер для тестового кейса"""
    
    def __init__(self, 
                 title: str,
                 description: str = '',
                 priority: str = 'Medium',
                 tags: List[str] = None,
                 precondition: str = '',
                 test_case_id: Optional[str] = None):
        self.test_case_id = test_case_id or str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.priority = priority
        self.tags = tags or []
        self.precondition = precondition
        self.steps: List[TestStep] = []
        self.start_time = None
        self.end_time = None
        self.status = 'skipped'
        self.error_message = None
        self._current_step_number = 0
        self._parent_project = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.status = 'running'
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        
        if exc_type is None:
            # Проверяем статусы шагов
            if any(step.status == 'failed' for step in self.steps):
                self.status = 'failed'
            elif any(step.status == 'error' for step in self.steps):
                self.status = 'error'
            elif all(step.status == 'passed' for step in self.steps):
                self.status = 'passed'
            else:
                self.status = 'completed'
        else:
            self.status = 'error'
            self.error_message = traceback.format_exc()
        
        # Если есть родительский проект, добавляем результаты в него
        if self._parent_project:
            self._parent_project.add_test_case_result(self)
        
        # Не подавляем исключения
        return False
    
    def step(self, description: str, expected_result: str) -> TestStep:
        """Создать новый тестовый шаг"""
        self._current_step_number += 1
        step = TestStep(description, expected_result, self._current_step_number)
        step._parent_case = self
        self.steps.append(step)
        return step
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку по тест-кейсу"""
        total_steps = len(self.steps)
        passed_steps = sum(1 for s in self.steps if s.status == 'passed')
        failed_steps = sum(1 for s in self.steps if s.status == 'failed')
        
        return {
            'test_case_id': self.test_case_id,
            'title': self.title,
            'status': self.status,
            'duration': self.duration,
            'total_steps': total_steps,
            'passed_steps': passed_steps,
            'failed_steps': failed_steps,
            'priority': self.priority,
            'tags': self.tags
        }


class TestProject:
    """Контекстный менеджер для тестового проекта"""
    
    def __init__(self, 
                 project_name: str,
                 output_file: str = 'test_checklist.csv',
                 include_screenshots: bool = True):
        self.project_name = project_name
        self.output_file = output_file
        self.include_screenshots = include_screenshots
        self.test_cases: List[TestCase] = []
        self.start_time = None
        self.end_time = None
        self.test_case_results: List[Dict[str, Any]] = []
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.end_time = datetime.now()
    #     self.generate_checklist()
    #     return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        if self.output_file is not None:          # <-- добавить эту проверку
            self.generate_checklist()
        return False

    def create_test_case(self, **kwargs) -> TestCase:
        """Создать новый тест-кейс"""
        test_case = TestCase(**kwargs)
        test_case._parent_project = self
        self.test_cases.append(test_case)
        return test_case
    
    def add_test_case_result(self, test_case: TestCase):
        """Добавить результат тест-кейса (вызывается автоматически)"""
        summary = test_case.get_summary()
        summary['steps'] = [step.to_result() for step in test_case.steps]
        self.test_case_results.append(summary)
    
    def generate_checklist(self):
        """Сгенерировать CSV чек-лист с результатами"""
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Project', 'Test Case ID', 'Title', 'Priority', 'Tags',
                'Step Number', 'Step Description', 'Expected Result',
                'Actual Result', 'Step Status', 'Step Duration',
                'Error Message', 'Screenshot', 'Test Case Status',
                'Test Case Duration'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.test_case_results:
                if result['total_steps'] > 0:
                    for step in result['steps']:
                        writer.writerow({
                            'Project': self.project_name,
                            'Test Case ID': result['test_case_id'],
                            'Title': result['title'],
                            'Priority': result['priority'],
                            'Tags': ','.join(result['tags']),
                            'Step Number': step.step_number,
                            'Step Description': step.description,
                            'Expected Result': step.expected_result,
                            'Actual Result': step.actual_result,
                            'Step Status': step.status,
                            'Step Duration': f"{step.duration:.3f}s",
                            'Error Message': step.error_message or '',
                            'Screenshot': step.screenshot_path or '',
                            'Test Case Status': result['status'],
                            'Test Case Duration': f"{result['duration']:.3f}s"
                        })
                else:
                    # Тест-кейс без шагов
                    writer.writerow({
                        'Project': self.project_name,
                        'Test Case ID': result['test_case_id'],
                        'Title': result['title'],
                        'Priority': result['priority'],
                        'Tags': ','.join(result['tags']),
                        'Step Number': '',
                        'Step Description': 'No steps defined',
                        'Expected Result': '',
                        'Actual Result': '',
                        'Step Status': result['status'],
                        'Step Duration': '',
                        'Error Message': '',
                        'Screenshot': '',
                        'Test Case Status': result['status'],
                        'Test Case Duration': f"{result['duration']:.3f}s"
                    })
        
        print(f"\n✅ Test checklist generated: {self.output_file}")
        self._print_summary()
    
    def _print_summary(self):
        """Вывести краткую сводку в консоль"""
        total = len(self.test_case_results)
        passed = sum(1 for t in self.test_case_results if t['status'] == 'passed')
        failed = sum(1 for t in self.test_case_results if t['status'] == 'failed')
        
        print(f"\n{'='*50}")
        print(f"Project: {self.project_name}")
        print(f"Total test cases: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Duration: {(self.end_time - self.start_time).total_seconds():.2f}s")
        print(f"{'='*50}\n")

    def generate_csv_string(self) -> str:
        """
        Генерирует полный CSV-отчёт в виде строки (для сохранения через Django FileField).
        """
        output = io.StringIO()
        fieldnames = [
            'Project', 'Test Case ID', 'Title', 'Priority', 'Tags',
            'Step Number', 'Step Description', 'Expected Result',
            'Actual Result', 'Step Status', 'Step Duration',
            'Error Message', 'Screenshot', 'Test Case Status',
            'Test Case Duration'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in self.test_case_results:
            if result['total_steps'] > 0:
                for step in result['steps']:
                    writer.writerow({
                        'Project': self.project_name,
                        'Test Case ID': result['test_case_id'],
                        'Title': result['title'],
                        'Priority': result['priority'],
                        'Tags': ','.join(result['tags']),
                        'Step Number': step.step_number,
                        'Step Description': step.description,
                        'Expected Result': step.expected_result,
                        'Actual Result': step.actual_result,
                        'Step Status': step.status,
                        'Step Duration': f"{step.duration:.3f}s",
                        'Error Message': step.error_message or '',
                        'Screenshot': step.screenshot_path or '',
                        'Test Case Status': result['status'],
                        'Test Case Duration': f"{result['duration']:.3f}s"
                    })
            else:
                # тест-кейс без шагов
                writer.writerow({
                    'Project': self.project_name,
                    'Test Case ID': result['test_case_id'],
                    'Title': result['title'],
                    'Priority': result['priority'],
                    'Tags': ','.join(result['tags']),
                    'Step Number': '',
                    'Step Description': 'No steps defined',
                    'Expected Result': '',
                    'Actual Result': '',
                    'Step Status': result['status'],
                    'Step Duration': '',
                    'Error Message': '',
                    'Screenshot': '',
                    'Test Case Status': result['status'],
                    'Test Case Duration': f"{result['duration']:.3f}s"
                })
        return output.getvalue()

    def get_summary(self) -> dict:
        """
        Возвращает сводную статистику выполнения тестов.
        """
        total = len(self.test_case_results)
        passed = sum(1 for t in self.test_case_results if t['status'] == 'passed')
        failed = sum(1 for t in self.test_case_results if t['status'] == 'failed')
        errors = sum(1 for t in self.test_case_results if t['status'] == 'error')
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
        }
