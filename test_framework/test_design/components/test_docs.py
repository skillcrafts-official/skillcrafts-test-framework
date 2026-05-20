"""
doc_util.py
Утилита для восстановления / генерации тестовой документации
в виде классических тест-кейсов (Markdown).
"""

import csv
import os
from typing import List, Optional, Dict, Any
from .framework import TestCase, TestStep  # Импорт классов нашего фреймворка


class TestDocGenerator:
    """
    Генерирует документацию по тест-кейсам в формате Markdown.
    """

    @staticmethod
    def from_csv(csv_path: str, output_path: Optional[str] = None) -> str:
        """
        Читает CSV-файл (созданный TestProject) и преобразует его в Markdown-документ
        с классическими тест-кейсами (включая результаты выполнения, если они есть).

        :param csv_path: путь к исходному CSV
        :param output_path: если указан, сохраняет результат в файл
        :return: строка с Markdown-документом
        """
        cases = TestDocGenerator._parse_csv(csv_path)
        md = TestDocGenerator._generate_markdown(cases, include_results=True)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"📄 Документация сохранена в {output_path}")
        return md

    @staticmethod
    def from_test_cases(test_cases: List[TestCase], output_path: Optional[str] = None) -> str:
        """
        Генерирует Markdown-документацию из списка объектов TestCase
        (например, после описания сценария без выполнения).

        :param test_cases: список тест-кейсов
        :param output_path: если указан, сохраняет результат в файл
        :return: строка с Markdown-документом
        """
        # Преобразуем объекты в словари (упрощённо, без результатов)
        cases_data = []
        for tc in test_cases:
            steps = []
            for step in tc.steps:
                steps.append({
                    'step_number': step.step_number,
                    'description': step.description,
                    'expected_result': step.expected_result,
                    'actual_result': '',
                    'status': '',
                    'duration': '',
                    'error': ''
                })
            cases_data.append({
                'test_case_id': tc.test_case_id,
                'title': tc.title,
                'priority': tc.priority,
                'tags': tc.tags,
                'precondition': tc.precondition,
                'status': '',
                'duration': '',
                'steps': steps
            })
        md = TestDocGenerator._generate_markdown(cases_data, include_results=False)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"📄 Шаблон документации сохранён в {output_path}")
        return md

    # ── Внутренние методы ──────────────────────────────────────

    @staticmethod
    def _parse_csv(csv_path: str) -> List[Dict[str, Any]]:
        """
        Читает CSV и группирует строки по Test Case ID.
        Возвращает список словарей с данными тест-кейсов.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

        cases_dict = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tc_id = row.get('Test Case ID', 'unknown')
                if tc_id not in cases_dict:
                    cases_dict[tc_id] = {
                        'test_case_id': tc_id,
                        'title': row.get('Title', ''),
                        'priority': row.get('Priority', ''),
                        'tags': row.get('Tags', '').split(',') if row.get('Tags') else [],
                        'precondition': row.get('Precondition', ''),
                        'status': row.get('Test Case Status', ''),
                        'duration': row.get('Test Case Duration', ''),
                        'steps': []
                    }
                # Добавляем шаг
                step = {
                    'step_number': row.get('Step Number', ''),
                    'description': row.get('Step Description', ''),
                    'expected_result': row.get('Expected Result', ''),
                    'actual_result': row.get('Actual Result', ''),
                    'status': row.get('Step Status', ''),
                    'duration': row.get('Step Duration', ''),
                    'error': row.get('Error Message', '')
                }
                cases_dict[tc_id]['steps'].append(step)
        return list(cases_dict.values())

    @staticmethod
    def _generate_markdown(cases_data: List[Dict], include_results: bool = True) -> str:
        """
        Генерирует Markdown-строку из подготовленных данных тест-кейсов.

        :param include_results: если True, добавляет фактические результаты и статусы
        """
        md_lines = []
        md_lines.append("# Тестовая документация (классические тест-кейсы)\n")
        md_lines.append(f"Дата генерации: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        md_lines.append("---\n\n")

        for case in cases_data:
            md_lines.append(f"## {case['title']}\n")
            md_lines.append(f"**ID:** {case['test_case_id']}  \n")
            md_lines.append(f"**Приоритет:** {case.get('priority', '')}  \n")
            if case.get('tags'):
                md_lines.append(f"**Теги:** {', '.join(case['tags'])}  \n")
            if case.get('precondition'):
                md_lines.append(f"**Предусловие:** {case['precondition']}  \n")
            if include_results:
                status = case.get('status', '')
                duration = case.get('duration', '')
                if status:
                    md_lines.append(f"**Статус автотеста:** {status}  \n")
                if duration:
                    md_lines.append(f"**Длительность:** {duration}  \n")
            md_lines.append("\n### Шаги\n\n")
            md_lines.append("| № | Описание шага | Ожидаемый результат |")
            if include_results:
                md_lines.append(" Фактический результат | Статус шага | Длительность | Ошибка |")
            md_lines.append("\n|---|--------------|---------------------|")
            if include_results:
                md_lines.append("-----------------------|-------------|-------------|-------|")
            md_lines.append("\n")

            for step in case['steps']:
                line = f"| {step['step_number']} | {step['description']} | {step['expected_result']} |"
                if include_results:
                    line += f" {step.get('actual_result', '')} | {step.get('status', '')} | {step.get('duration', '')} | {step.get('error', '')} |"
                md_lines.append(line + "\n")
            md_lines.append("\n\n---\n\n")

        return ''.join(md_lines)
