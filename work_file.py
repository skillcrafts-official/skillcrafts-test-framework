EDU_LEVELS = {
    "nothing": "не указано",
    "school_9": "9 классов",
    "school_11": "11 классов",
    "ptu": "ПТУ / Профессиональное училище",
    "technical_school": "Техникум",
    "college": "Колледж",
    "unfinished_higher": "Неоконченное высшее",
    "bachelor": "Бакалавр",
    "specialist": "Специалист",
    "master": "Магистр",
    "phd": "Кандидат наук",
    "doctor": "Доктор наук",
    "mba": "MBA"
}.keys()

print(*map(lambda x: repr(x), EDU_LEVELS), sep=',\n')