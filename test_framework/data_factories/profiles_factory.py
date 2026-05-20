import random
import uuid
from typing import Any, Dict, List, Optional
from faker import Faker


class ProfileFactory:
    """
    Фабрика для создания тестовых данных профилей пользователей
    в точном соответствии с реальной структурой ответа API.
    """

    EDU_LEVELS = [
        'nothing',
        'school_9',
        'school_11',
        'ptu',
        'technical_school',
        'college',
        'unfinished_higher',
        'bachelor',
        'specialist',
        'master',
        'phd',
        'doctor',
        'mba',
    ]

    def __init__(self, locale: str = "en_US", config_path: Optional[str] = None):
        self.fake = Faker(locale)
        self._manual_data: List[Dict[str, Any]] = []
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

    def _random_work_formats(self) -> Dict[str, Any]:
        """Генерирует случайный набор форматов работы."""
        # id от 1 до 100
        wid = random.randint(1, 100)
        office = self.fake.boolean(chance_of_getting_true=30)
        hybrid = not office and self.fake.boolean(chance_of_getting_true=50)
        remote = not office and not hybrid
        return {
            "office": office,
            "hybrid": hybrid,
            "remote": remote,
        }

    def _optional_field(self, func, chance_empty=0.75):
        """Случайно возвращает либо значение, либо пустую строку."""
        if random.random() < chance_empty:
            return ""
        return func()

    def create_profile(self, **overrides) -> Dict[str, Any]:
        """
        Создаёт один профиль с опциональными переопределениями полей.
        Все поля приведены к структуре API.
        """
        user_id = random.randint(1, 99999)

        profile = {
            # "user": user_id,
            # "work_formats": self._random_work_formats(),
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
            "wallpaper": None,  # self.fake.image_url(),
            "avatar": None,  #self.fake.image_url(),
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
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список профилей заданной длины.

        :param count: количество профилей
        :param use_manual: использовать ли ручные данные (если есть)
        :param overrides: поля, применяемые ко всем профилям
        """
        if use_manual and self._manual_data:
            profiles = list(self._manual_data[:count])
            while len(profiles) < count:
                profiles.append(self.create_profile())
        else:
            profiles = [self.create_profile() for _ in range(count)]

        if overrides:
            for p in profiles:
                p.update(overrides)
        return profiles


if __name__ == '__main__':

    profile = ProfileFactory()
    print(profile.create_profile())

    print(profile.generate_profiles(10))
