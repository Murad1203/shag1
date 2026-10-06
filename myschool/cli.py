"""CLI для работы с аттестационными периодами myschool.05edu.ru.

Примеры:
    python -m myschool schedules            # показать все ГАП школы
    python -m myschool groups --class-level 2
    python -m myschool create-period \\
        --name "Промежуточная аттестация 2026-2027" \\
        --period "Промежуточная,01.09.2026,26.05.2027" --apply
    python -m myschool assign --schedule-id 16209 --group-id 2204671 --apply
    python -m myschool assign --schedule-id 16209 --class-level 2 --all --apply

По умолчанию изменяющие команды работают в режиме предпросмотра (dry-run) —
показывают, что будет отправлено, но ничего не меняют. Добавьте --apply,
чтобы выполнить запрос на реальном сервере.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from typing import Optional

from .client import DATE_FMT, MySchoolClient, MySchoolError
from .config import Config


def _print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _parse_period(spec: str) -> dict:
    """Разобрать "Название,ДД.ММ.ГГГГ,ДД.ММ.ГГГГ" в словарь периода."""
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"period должен быть вида 'Название,ДД.ММ.ГГГГ,ДД.ММ.ГГГГ', получено: {spec!r}"
        )
    name, begin, end = parts
    for d in (begin, end):
        try:
            _dt.datetime.strptime(d, DATE_FMT)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"дата {d!r} не в формате ДД.ММ.ГГГГ"
            )
    return {"name": name, "begin_date": begin, "end_date": end}


# --------------------------------------------------------------------- команды


def cmd_schedules(client: MySchoolClient, args: argparse.Namespace) -> int:
    schedules = client.list_attestation_schedules()
    if args.json:
        _print_json(schedules)
        return 0
    for s in schedules:
        print(f"[{s['id']}] {s['name']}  (school_id={s.get('school_id')})")
        for p in s.get("periods", []):
            print(
                f"    - [{p['id']}] {p['name']}: "
                f"{p['begin_date']} — {p['end_date']}"
            )
    return 0


def cmd_groups(client: MySchoolClient, args: argparse.Namespace) -> int:
    groups = client.list_groups(class_level_id=args.class_level)
    if args.json:
        _print_json(groups)
        return 0
    for g in groups:
        print(
            f"[{g['id']}] {g.get('short_name','')}  {g.get('subject_name','')} "
            f"-> ГАП {g.get('attestation_periods_schedule_id')}"
        )
    print(f"\nВсего групп: {len(groups)}")
    return 0


def cmd_create_period(client: MySchoolClient, args: argparse.Namespace) -> int:
    result = client.create_attestation_schedule(
        name=args.name, periods=args.period, dry_run=not args.apply
    )
    if not args.apply:
        print("DRY-RUN (ничего не отправлено). Будет выполнено:")
    else:
        print("Отправлено на сервер. Ответ:")
    _print_json(result)
    return 0


def cmd_assign(client: MySchoolClient, args: argparse.Namespace) -> int:
    groups = client.list_groups(class_level_id=args.class_level)
    by_id = {g["id"]: g for g in groups}

    if args.all:
        targets = list(groups)
    elif args.group_id:
        targets = []
        for gid in args.group_id:
            if gid not in by_id:
                print(f"Группа {gid} не найдена в выдаче.", file=sys.stderr)
                return 2
            targets.append(by_id[gid])
    else:
        print("Укажите --group-id ... или --all (с --class-level).", file=sys.stderr)
        return 2

    for g in targets:
        result = client.assign_schedule_to_group(
            g, args.schedule_id, dry_run=not args.apply
        )
        tag = "DRY-RUN" if not args.apply else "OK"
        print(
            f"[{tag}] группа {g['id']} ({g.get('short_name','')} "
            f"{g.get('subject_name','')}) -> ГАП {args.schedule_id}"
        )
    print(f"\nОбработано групп: {len(targets)}"
          + ("" if args.apply else "  (режим предпросмотра, добавьте --apply)"))
    return 0


# ------------------------------------------------------------------- точка входа


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="myschool",
        description="Автоматизация аттестационных периодов myschool.05edu.ru",
    )
    p.add_argument("--config", help="путь к config.json (по умолчанию ./config.json)")
    p.add_argument("--json", action="store_true", help="печать сырого JSON")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("schedules", help="список графиков аттестационных периодов")
    sp.set_defaults(func=cmd_schedules)

    gp = sub.add_parser("groups", help="список учебных групп")
    gp.add_argument("--class-level", type=int, help="уровень класса (напр. 2)")
    gp.set_defaults(func=cmd_groups)

    cp = sub.add_parser(
        "create-period",
        help="создать график (промежуточная аттестация) — тело предположительное",
    )
    cp.add_argument("--name", required=True, help="название графика")
    cp.add_argument(
        "--period",
        required=True,
        action="append",
        type=_parse_period,
        metavar="Название,ДД.ММ.ГГГГ,ДД.ММ.ГГГГ",
        help="период графика (можно указывать несколько раз)",
    )
    cp.add_argument("--apply", action="store_true", help="выполнить реально")
    cp.set_defaults(func=cmd_create_period)

    ap = sub.add_parser("assign", help="привязать график к группам")
    ap.add_argument("--schedule-id", type=int, required=True, help="id графика (ГАП)")
    ap.add_argument("--group-id", type=int, action="append", help="id группы")
    ap.add_argument("--class-level", type=int, help="уровень класса для --all")
    ap.add_argument("--all", action="store_true", help="все группы уровня класса")
    ap.add_argument("--apply", action="store_true", help="выполнить реально")
    ap.set_defaults(func=cmd_assign)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = Config.load(args.config)
        client = MySchoolClient(config)
        return args.func(client, args)
    except (MySchoolError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
