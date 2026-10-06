"""Клиент к API электронного журнала myschool.05edu.ru (платформа МЭШ).

Пакет для автоматизации работы с аттестационными периодами:
просмотр графиков аттестационных периодов (ГАП), создание промежуточного
аттестационного периода и привязка графика к учебным группам.
"""

from .client import MySchoolClient, MySchoolError
from .config import Config

__all__ = ["MySchoolClient", "MySchoolError", "Config"]
__version__ = "0.1.0"
