from test_design.test_docs import TestDocGenerator

# Генерируем Markdown с результатами
md_text = TestDocGenerator.from_csv("api_checklist.csv", "docs/test_cases_with_results.md")
print(md_text)
