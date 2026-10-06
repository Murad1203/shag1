"""Конфигурация клиента.

Значения берутся (в порядке приоритета) из аргументов, переменных окружения
и файла конфигурации (JSON). Секреты (Cookie) в репозиторий не коммитим —
см. config.example.json и .gitignore.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


# Имена переменных окружения
ENV_PREFIX = "MYSCHOOL_"

# Значения по умолчанию, восстановленные из HAR-сессии myschool.05edu.ru.
# Это заголовки, которые фронтенд МЭШ (educationmanagement) шлёт на каждый
# запрос к /api/. Их можно переопределить в config.json или через окружение.
DEFAULTS = {
    "base_url": "https://myschool.05edu.ru",
    "subsystem": "hteacherweb",   # заголовок X-Mes-Subsystem
    "host_id": "22",              # заголовок X-Mes-Hostid
    "role_id": "26",              # заголовок X-Mes-Roleid
}


@dataclass
class Config:
    """Параметры подключения к API.

    Обязательные для реальных запросов: cookie, profile_id, academic_year_id.
    school_id / organization_id нужны только для создания нового графика.
    """

    cookie: str = ""
    profile_id: str = ""            # profile-id / pid (в HAR: 21209)
    academic_year_id: str = ""      # aid (в HAR: 14)
    school_id: str = ""             # school_id графика (в HAR: 586)
    organization_id: str = ""       # organization_id (в HAR: 400117035)

    base_url: str = DEFAULTS["base_url"]
    subsystem: str = DEFAULTS["subsystem"]
    host_id: str = DEFAULTS["host_id"]
    role_id: str = DEFAULTS["role_id"]

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Собрать конфиг из файла (если есть) и переменных окружения.

        Переменные окружения имеют приоритет над файлом.
        Поиск файла: аргумент path -> $MYSCHOOL_CONFIG -> ./config.json
        """
        data: dict = {}

        candidate = path or os.environ.get(f"{ENV_PREFIX}CONFIG") or "config.json"
        cfg_path = Path(candidate)
        if cfg_path.is_file():
            data.update(json.loads(cfg_path.read_text(encoding="utf-8")))

        for field in cls.__dataclass_fields__:
            env_key = f"{ENV_PREFIX}{field.upper()}"
            if env_key in os.environ:
                data[field] = os.environ[env_key]

        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)

    def require(self, *fields: str) -> None:
        """Проверить, что нужные поля заполнены, иначе понятная ошибка."""
        missing = [f for f in fields if not getattr(self, f, "")]
        if missing:
            raise ValueError(
                "Не заполнены обязательные параметры: "
                + ", ".join(missing)
                + ".\nУкажите их в config.json или через переменные окружения "
                + ", ".join(f"{ENV_PREFIX}{m.upper()}" for m in missing)
                + "."
            )

    def redacted(self) -> dict:
        """Словарь конфига с замаскированным cookie (для логов)."""
        d = asdict(self)
        if d.get("cookie"):
            d["cookie"] = f"<{len(d['cookie'])} символов>"
        return d
