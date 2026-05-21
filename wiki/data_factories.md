# Фабрика тестовых данных

Фабрики данных создаются по принципам ООП и этой статье будет рассматриваться в контексте тестирования REST API. Одна фабрика соответствует одной схеме API.  

Рассмотрим на примере схемы profile ([api-service](https://api.skillcrafts.ru/api/docs/#/profiles/profiles_create)). В этой схеме нужно создавать профиль пользователя, для этого нужны данные их можно сгенерировать с помощью faker или создать свой ручной набор (если нужна строгость в плане КЭ и ГЗ).

Класс-фабрика состоит из нескольких частей:  

- константы,
- подгрузка ручных данных из файла (json, yml, можно сделать из любых),
- генераторы случайных данных для разных частей профиля,
- сборщик итогового словаря с тестовыми данными для профиля,
- генератор произвольного количества профилей.

Это демонстрационный минимум, список можно расширять сколько угодно.

### Пример фабрики профилей пользователя

```python
class ProfileFactory:
    """
    Фабрика для создания тестовых данных профилей пользователей
    в точном соответствии с реальной структурой ответа API.
    """

    EDU_LEVELS = [
        'nothing',
        'school_9',
        'school_11',
        ...
    ]

    def __init__(self, locale: str = "en_US", config_path: str | None = None):
        self.fake = Faker(locale)
        self._manual_data: list[dict[str, Any]] = []
        if config_path:
            self.load_manual_data(config_path)

    def load_manual_data(self, config_path: str) -> None:
        """Загружает ручные профили из JSON- или YAML-файла."""
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.endswith(('.yaml', '.yml')):
                import yaml
                self._manual_data = yaml.safe_load(f)
            else:
                self._manual_data = json.load(f)

    def create_profile(self, **overrides) -> dict[str, Any]:
        """
        Создаёт один профиль с опциональными переопределениями полей.
        Все поля приведены к структуре API.
        """
        user_id = random.randint(1, 99999)

        profile = {
            "first_name": self.fake.first_name(),
            "middle_name": self._optional_field(self.fake.first_name, 0.3),
            "last_name": self.fake.last_name(),
            "profession": self.fake.job(),
            "city": self.fake.city(),
            "country": self.fake.country(),
            "relocation": f"{self.fake.country()}, {self.fake.city()}",
            "edu_level": random.choice(self.EDU_LEVELS),
            "institution_name": self.fake.company(),
            "graduation_year": random.randint(2000, 2026),
            "short_desc": self.fake.sentence(nb_words=10)[:100],
            "full_desc": self.fake.text(max_nb_chars=500),
            "wallpaper": None,
            "avatar": None,
            "link_to_instagram": self._optional_field(self.fake.url, 0.7),
            "link_to_telegram": self._optional_field(self.fake.url, 0.7),
            "link_to_github": self._optional_field(self.fake.url, 0.7),
            "link_to_vk": self._optional_field(self.fake.url, 0.7),
        }

        profile.update(overrides)
        return profile

    def generate_profiles(
        self,
        count: int = 1,
        use_manual: bool = False,
        **overrides,
    ) -> list[dict[str, Any]]:
        """
        Возвращает список профилей заданной длины.
        """

        profiles = [self.create_profile() for _ in range(count)]

        if overrides:
            for p in profiles:
                p.update(overrides)
        return profiles
```

В идеале можно использовать модели данных из реального API и на его основе формировать список параметров и типов данных для профиля. Но это уже программа максимум и если целесообразно плотная интеграция с кодом разработки (возможно, создавать отдельную фабрику имеет больше смысла, так как модель могут несанкционированно изменить и пользователь перестанет иметь доступ к части своих данных после очередного релиза).