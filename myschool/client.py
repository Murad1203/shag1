"""HTTP-клиент к API электронного журнала myschool.05edu.ru.

Эндпоинты и модель данных восстановлены из HAR-дампа реальной сессии
(см. docs/api-notes.md). Авторизация — по сессионному Cookie, который
фронтенд МЭШ получает при входе. Токен в коде не хранится: он берётся
из конфигурации (config.json / переменные окружения).
"""

from __future__ import annotations

import json
from typing import Any, Optional

import requests

from .config import Config


class MySchoolError(RuntimeError):
    """Ошибка обращения к API (неуспешный HTTP-статус или нечитаемый ответ)."""


# Формат дат в API — ДД.ММ.ГГГГ (например, 01.09.2026).
DATE_FMT = "%d.%m.%Y"


class MySchoolClient:
    def __init__(self, config: Config, *, timeout: float = 30.0):
        self.cfg = config
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self._base_headers())

    # ------------------------------------------------------------------ utils

    def _base_headers(self) -> dict:
        """Заголовки, которые МЭШ шлёт на каждый запрос к /api/ (из HAR)."""
        h = {
            "Accept": "*/*",
            "Accept-Language": "ru,en;q=0.9",
            "Content-Type": "application/json",
            "X-Mes-Subsystem": self.cfg.subsystem,
            "X-Mes-Hostid": self.cfg.host_id,
            "X-Mes-Roleid": self.cfg.role_id,
        }
        if self.cfg.cookie:
            h["Cookie"] = self.cfg.cookie
        if self.cfg.profile_id:
            h["Profile-Id"] = self.cfg.profile_id
        if self.cfg.academic_year_id:
            h["aid"] = self.cfg.academic_year_id
        return h

    def _url(self, path: str) -> str:
        return f"{self.cfg.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self._url(path)
        try:
            resp = self.session.request(
                method, url, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:  # сеть/TLS
            raise MySchoolError(f"{method} {url}: сетевая ошибка: {exc}") from exc

        if not resp.ok:
            body = resp.text[:500]
            raise MySchoolError(
                f"{method} {url}: HTTP {resp.status_code} {resp.reason}\n{body}"
            )

        if not resp.content:
            return None
        try:
            return resp.json()
        except json.JSONDecodeError as exc:
            raise MySchoolError(
                f"{method} {url}: ответ не JSON: {resp.text[:200]}"
            ) from exc

    # -------------------------------------------------- attestation schedules

    def list_attestation_schedules(self) -> list[dict]:
        """Список графиков аттестационных периодов (ГАП) школы.

        GET /api/ej/core/teacher/v1/attestation_periods_schedules?pid=<profile_id>

        Возвращает список объектов вида:
            {id, name, school_id, organization_id, academic_year_id,
             periods: [{id, name, begin_date, end_date, ...}]}
        """
        self.cfg.require("profile_id")
        return self._request(
            "GET",
            "/api/ej/core/teacher/v1/attestation_periods_schedules",
            params={"pid": self.cfg.profile_id},
        )

    def create_attestation_schedule(
        self, name: str, periods: list[dict], *, dry_run: bool = True
    ) -> dict:
        """Создать новый график аттестационных периодов (промежуточная аттестация).

        ВНИМАНИЕ: точный запрос создания в HAR не зафиксирован (записался только
        метрик-гол addAssessmentPeriodFormSaveClick). Тело и путь восстановлены
        по модели данных из GET-ответа и помечены как ПРЕДПОЛОЖИТЕЛЬНЫЕ.
        Проверьте реальный запрос в DevTools перед боевым применением.

        POST /api/ej/core/teacher/v1/attestation_periods_schedules

        periods: список словарей {name, begin_date, end_date} в формате ДД.ММ.ГГГГ.
        """
        self.cfg.require("school_id", "organization_id", "academic_year_id")
        payload = {
            "name": name,
            "school_id": _as_int(self.cfg.school_id),
            "organization_id": self.cfg.organization_id,
            "academic_year_id": _as_int(self.cfg.academic_year_id),
            "periods": [
                {
                    "name": p["name"],
                    "begin_date": p["begin_date"],
                    "end_date": p["end_date"],
                }
                for p in periods
            ],
        }
        if dry_run:
            return {"dry_run": True, "method": "POST", "payload": payload}
        return self._request(
            "POST",
            "/api/ej/core/teacher/v1/attestation_periods_schedules",
            json=payload,
        )

    def update_attestation_schedule(
        self, schedule_id: int, body: dict, *, dry_run: bool = True
    ) -> dict:
        """Обновить существующий график (например, добавить период).

        ПРЕДПОЛОЖИТЕЛЬНО: PUT /api/ej/core/teacher/v1/attestation_periods_schedules/<id>
        Передаётся полный объект графика с изменённым списком periods.
        """
        if dry_run:
            return {"dry_run": True, "method": "PUT", "id": schedule_id, "payload": body}
        return self._request(
            "PUT",
            f"/api/ej/core/teacher/v1/attestation_periods_schedules/{schedule_id}",
            json=body,
        )

    # ------------------------------------------------------------- group/plan

    def list_groups(
        self,
        class_level_id: Optional[int] = None,
        *,
        with_periods_schedule_id: bool = True,
        per_page: int = 300,
    ) -> list[dict]:
        """Список учебных групп (предмет x класс) с их графиком аттестации.

        GET /api/ej/plan/teacher/v1/groups?academic_year_id=..&class_level_id=..
            &with_periods_schedule_id=true&per_page=300
        """
        self.cfg.require("academic_year_id")
        params: dict[str, Any] = {
            "academic_year_id": self.cfg.academic_year_id,
            "with_periods_schedule_id": str(with_periods_schedule_id).lower(),
            "per_page": per_page,
        }
        if class_level_id is not None:
            params["class_level_id"] = class_level_id
            params["class_level_ids"] = class_level_id
        return self._request("GET", "/api/ej/plan/teacher/v1/groups", params=params)

    def assign_schedule_to_group(
        self, group: dict, schedule_id: int, *, dry_run: bool = True
    ) -> dict:
        """Привязать график аттестационных периодов к учебной группе.

        PUT /api/ej/plan/teacher/v1/groups/<group_id>
        В HAR при сохранении отправляется ПОЛНЫЙ объект группы с проставленным
        полем attestation_periods_schedule_id — поэтому передаём весь объект,
        меняя только это поле.
        """
        body = dict(group)
        body["attestation_periods_schedule_id"] = schedule_id
        group_id = body["id"]
        if dry_run:
            return {
                "dry_run": True,
                "method": "PUT",
                "group_id": group_id,
                "attestation_periods_schedule_id": schedule_id,
            }
        return self._request(
            "PUT", f"/api/ej/plan/teacher/v1/groups/{group_id}", json=body
        )


def _as_int(value: Any) -> Any:
    """Привести числовую строку к int, иначе вернуть как есть."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return value
