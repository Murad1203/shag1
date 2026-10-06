# API аттестационных периодов myschool.05edu.ru (разбор HAR)

Заметки восстановлены из HAR-дампа реальной сессии учителя/администратора
на платформе МЭШ (`educationmanagement`). Школа `school_id=586`,
`organization_id=400117035`, учебный год `academic_year_id (aid) = 14`,
профиль `profile_id (pid) = 21209`.

## Авторизация и общие заголовки

Авторизация — **по сессионному Cookie** (в HAR значение было вырезано).
Фронтенд шлёт на каждый запрос к `/api/` такие заголовки:

| Заголовок          | Значение в сессии | Назначение                       |
|--------------------|-------------------|----------------------------------|
| `Cookie`           | *(сессия)*        | авторизация                      |
| `Profile-Id`       | `21209`           | профиль пользователя (= `pid`)   |
| `aid`              | `14`              | учебный год                      |
| `X-Mes-Subsystem`  | `hteacherweb`     | подсистема журнала               |
| `X-Mes-Hostid`     | `22`              | идентификатор хоста МЭШ          |
| `X-Mes-Roleid`     | `26`              | роль пользователя                |
| `Content-Type`     | `application/json`|                                  |

Чтобы получить свежий `Cookie`: откройте журнал в браузере → DevTools →
Network → любой запрос к `/api/...` → скопируйте заголовок `Cookie` целиком
в `config.json`. Cookie живёт ограниченное время, при 401/403 обновите его.

## Признак фичи

`GET /educationmanagement/config/config.json` возвращает флаги, среди них:

```json
"ENABLE_OO_INTERMEDIATE_ATTESTATION": true
```

Это и есть «промежуточная аттестация» для общеобразовательной организации.
Экран её настройки — `/educationmanagement/handbook/final-attestation-form`.

## Эндпоинты

### 1. Список графиков аттестационных периодов (ГАП) — ПОДТВЕРЖДЁН

```
GET /api/ej/core/teacher/v1/attestation_periods_schedules?pid=21209
```

Ответ (сокращённо):

```json
[
  {
    "id": 16209,
    "name": "ГАП 1-9",
    "school_id": 586,
    "organization_id": "400117035",
    "academic_year_id": 14,
    "periods": [
      {"id": 37546, "name": "1 Четверть", "begin_date": "01.09.2026", "end_date": "25.10.2026", "attestation_periods_schedule_id": 16209},
      {"id": 37545, "name": "2 Четверть", "begin_date": "04.11.2026", "end_date": "30.12.2026", "attestation_periods_schedule_id": 16209},
      {"id": 37547, "name": "3 Четверть", "begin_date": "11.01.2027", "end_date": "26.03.2027", "attestation_periods_schedule_id": 16209},
      {"id": 37548, "name": "4 Четверть", "begin_date": "05.04.2027", "end_date": "26.05.2027", "attestation_periods_schedule_id": 16209}
    ]
  },
  {
    "id": 16212,
    "name": "ГАП 10-11",
    "periods": [
      {"id": 37550, "name": "1 полугодие", "begin_date": "01.09.2026", "end_date": "30.12.2026"},
      {"id": 37551, "name": "2 полугодие", "begin_date": "11.01.2027", "end_date": "26.05.2027"}
    ]
  }
]
```

Даты — в формате `ДД.ММ.ГГГГ`.

### 2. Список учебных групп с их ГАП — ПОДТВЕРЖДЁН

```
GET /api/ej/plan/teacher/v1/groups?class_level_id=2&class_level_ids=2&academic_year_id=14&with_periods_schedule_id=true&per_page=300
```

Каждая группа содержит, среди прочего:
`id`, `name`, `short_name`, `subject_id`, `subject_name`, `class_level_id`,
`class_unit_id`, `academic_year_id`, `periods_schedule_id`,
`attestation_periods_schedule_id` и флаги (`is_final_by_periods`,
`is_subgroup`, `is_metagroup`, ...).

### 3. Привязка ГАП к группе — ПОДТВЕРЖДЁН

```
PUT /api/ej/plan/teacher/v1/groups/2204676
```

В теле отправляется **весь объект группы** с проставленным
`attestation_periods_schedule_id`. Пример тела из HAR:

```json
{
  "id": 2204676,
  "name": "Изобразительное искусство 2-A УП 2 класс 2026-2027",
  "short_name": "2-A 1",
  "subject_id": 33623629,
  "periods_schedule_id": 22277,
  "class_level_id": 2,
  "class_unit_id": 119214,
  "academic_year_id": 14,
  "attestation_periods_schedule_id": 16209,
  "...": "остальные поля группы без изменений"
}
```

Сервер возвращает полный объект группы с развёрнутыми ученическими
составами и нагрузкой преподавателей.

### 4. Создание/изменение ГАП — ПРЕДПОЛОЖИТЕЛЬНО (в HAR нет тела запроса)

При сохранении формы «добавить аттестационный период» в HAR зафиксирован
только гол Яндекс.Метрики:

```
goal://myschool.05edu.ru/addAssessmentPeriodFormSaveClick
```

Сам XHR создания в дамп **не попал**. По модели данных из п.1 ожидается:

```
POST /api/ej/core/teacher/v1/attestation_periods_schedules
Content-Type: application/json

{
  "name": "Промежуточная аттестация 2026-2027",
  "school_id": 586,
  "organization_id": "400117035",
  "academic_year_id": 14,
  "periods": [
    {"name": "Промежуточная", "begin_date": "01.09.2026", "end_date": "26.05.2027"}
  ]
}
```

Изменение существующего графика — предположительно
`PUT /api/ej/core/teacher/v1/attestation_periods_schedules/{id}` с полным
объектом графика.

> ⚠️ Перед боевым применением команды `create-period` проверьте реальный
> запрос в DevTools (вкладка Network при нажатии «Сохранить») и при
> необходимости поправьте путь/тело в `myschool/client.py`.
