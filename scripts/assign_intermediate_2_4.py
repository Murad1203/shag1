#!/usr/bin/env python3
"""Закрепить промежуточный аттестационный период (ГАП) у 2–4 классов.

Скрипт находит нужный график аттестационных периодов, затем проходит по
всем учебным группам 2, 3 и 4 классов и проставляет им этот график
(поле attestation_periods_schedule_id), как это делает журнал при
сохранении на экране привязки.

По умолчанию — режим предпросмотра (dry-run): показывает, что будет
изменено, но ничего не отправляет. Для реального выполнения: --apply.

Примеры:
    # посмотреть, что будет сделано (ничего не меняя):
    python scripts/assign_intermediate_2_4.py

    # найти график по части названия и применить:
    python scripts/assign_intermediate_2_4.py --match "промеж" --apply

    # или явно указать id графика:
    python scripts/assign_intermediate_2_4.py --schedule-id 16209 --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# чтобы скрипт запускался из любой директории
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from myschool import Config, MySchoolClient, MySchoolError  # noqa: E402

# Классы, которым закрепляем период.
CLASS_LEVELS = [2, 3, 4]


def resolve_schedule_id(client: MySchoolClient, args) -> int:
    """Определить id графика: по --schedule-id или по подстроке названия."""
    schedules = client.list_attestation_schedules()

    if args.schedule_id is not None:
        found = next((s for s in schedules if s["id"] == args.schedule_id), None)
        if found is None:
            print(
                f"График с id={args.schedule_id} не найден. Доступные:",
                file=sys.stderr,
            )
            _print_schedules(schedules, sys.stderr)
            raise SystemExit(2)
        print(f"Выбран график: [{found['id']}] {found['name']}")
        return found["id"]

    needle = args.match.lower()
    matches = [s for s in schedules if needle in s["name"].lower()]
    if len(matches) == 1:
        s = matches[0]
        print(f"Найден график по '{args.match}': [{s['id']}] {s['name']}")
        return s["id"]

    if not matches:
        print(
            f"По подстроке '{args.match}' график не найден. "
            "Укажите --schedule-id вручную. Доступные графики:",
            file=sys.stderr,
        )
    else:
        print(
            f"По подстроке '{args.match}' найдено несколько графиков. "
            "Уточните --schedule-id:",
            file=sys.stderr,
        )
    _print_schedules(schedules, sys.stderr)
    raise SystemExit(2)


def _print_schedules(schedules, stream=sys.stdout) -> None:
    for s in schedules:
        print(f"  [{s['id']}] {s['name']}", file=stream)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", help="путь к config.json (по умолчанию ./config.json)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--schedule-id", type=int, help="id графика (ГАП) напрямую")
    g.add_argument("--match", default="промеж",
                   help="искать график по части названия (по умолчанию 'промеж')")
    p.add_argument("--apply", action="store_true",
                   help="выполнить реально (без него — только предпросмотр)")
    p.add_argument("--force", action="store_true",
                   help="переназначать даже если график уже проставлен")
    args = p.parse_args(argv)

    try:
        config = Config.load(args.config)
        client = MySchoolClient(config)

        schedule_id = resolve_schedule_id(client, args)

        total = 0
        changed = 0
        skipped = 0
        for level in CLASS_LEVELS:
            groups = client.list_groups(class_level_id=level)
            print(f"\n=== {level} класс: групп {len(groups)} ===")
            for grp in groups:
                total += 1
                current = grp.get("attestation_periods_schedule_id")
                label = (f"{grp.get('short_name','')} "
                         f"{grp.get('subject_name','')}").strip()
                if current == schedule_id and not args.force:
                    skipped += 1
                    print(f"  = группа {grp['id']} ({label}) уже на ГАП {schedule_id}")
                    continue
                client.assign_schedule_to_group(grp, schedule_id,
                                                dry_run=not args.apply)
                changed += 1
                tag = "OK" if args.apply else "DRY-RUN"
                print(f"  [{tag}] группа {grp['id']} ({label}) "
                      f"{current} -> {schedule_id}")

        print(
            f"\nИтого: групп {total}, "
            f"к изменению {changed}, пропущено (уже стоит) {skipped}."
        )
        if not args.apply and changed:
            print("Это был предпросмотр. Добавьте --apply, чтобы применить.")
        return 0

    except (MySchoolError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
