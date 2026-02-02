# Задача: MVP генератора Firm Offers

## Контекст
Я фрейт-брокер, специализируюсь на украинском зерне → Средиземноморье (особенно Египет).
Сейчас создание firm offer занимает 2-4 часа. Хочу автоматизировать до 10-15 минут.

## Готовые данные (используй их!)

В папке `/data/` уже есть структурированные JSON:
- `ports.json` — порты погрузки/выгрузки с клаузами
- `cargo_stw.json` — грузы и STW факторы
- `charterers.json` — фрахтователи с комиссиями
- `clauses.json` — дополнительные клаузы (в /docs)

**ВАЖНО:** Используй эти готовые данные, не создавай свои!

## Документация

В папке `/docs/` детальная документация:
- `MASTER_LIBRARY.md` — полная библиотека 45+ клауз
- `SYSTEM_ARCHITECTURE.md` — логика выбора клауз
- `CARGO_DATABASE.md` — STW факторы (уже в cargo_stw.json)
- `CHARTERER_DATABASE.md` — структура чартерщиков

## MVP scope

### Что должно работать:

**1. Веб-форма с полями:**
- Порт погрузки (dropdown из ports.json → load)
- Порт выгрузки (dropdown из ports.json → discharge)
- Груз (dropdown из cargo_stw.json)
- Фрахтователь (dropdown из charterers.json)
- Количество (number input, MT)
- Фрахт (number input, $/MT)
- Laycan start/end (date inputs)
- Демерредж (number input, $/день)

**2. Генерация FO:**
- Загрузить клаузы из ports.json по выбранным портам
- Подставить STW из cargo_stw.json
- Включить grain clauses для зерновых
- Сформировать полный текст

**3. Вывод:**
- Готовый текст firm offer в textarea
- Кнопка "Copy to clipboard"
- (опционально) скачать как .txt

### Что НЕ нужно:
- PDF генерация
- Авторизация
- База данных (SQLite/PostgreSQL)
- История offers
- Counter workflow

## Технический стек

```
Backend: Python + FastAPI
Frontend: Простой HTML + Tailwind CSS + vanilla JS
Данные: JSON файлы (уже готовы в /data)
```

## Структура проекта

```
/backend
  /app
    main.py           # FastAPI, один endpoint
    generator.py      # Логика генерации FO
    models.py         # Pydantic модели
  requirements.txt

/frontend
  index.html          # Форма + результат
  script.js           # Fetch к API
  style.css           # Минимальные стили (или Tailwind CDN)
```

## API Endpoint

```
POST /api/generate

Request body:
{
  "load_port": "Reni",
  "discharge_port": "Alexandria", 
  "cargo": "Corn",
  "quantity": 55000,
  "freight_rate": 18.00,
  "laycan_start": "2025-12-15",
  "laycan_end": "2025-12-20",
  "demurrage_rate": 9000,
  "charterer_id": "CHTR-001"  // optional
}

Response:
{
  "firm_offer_text": "FIRM OFFER\n\nCHARTERERS:...",
  "summary": {
    "route": "Reni → Alexandria",
    "cargo": "55,000 MT Corn",
    "total_freight": 990000,
    "clauses_included": ["SULINA", "AIRRAID", "EGY-NOR", "EGY-SAMPLING"]
  }
}
```

## Логика генерации (generator.py)

```python
def generate_firm_offer(request):
    # 1. Загрузить данные из JSON
    ports = load_json("data/ports.json")
    cargoes = load_json("data/cargo_stw.json")
    
    # 2. Найти порт погрузки и его клаузы
    load_port = find_port(ports["ports"]["load"], request.load_port)
    load_clauses = [ports["clauses"][c] for c in load_port["clauses"]]
    
    # 3. Найти порт выгрузки и его клаузы
    discharge_port = find_port(ports["ports"]["discharge"], request.discharge_port)
    discharge_clauses = [ports["clauses"][c] for c in discharge_port["clauses"]]
    
    # 4. Найти груз и STW
    cargo = find_cargo(cargoes, request.cargo)
    cargo_description = format_cargo(cargo, request.quantity)
    
    # 5. Собрать текст FO
    return assemble_firm_offer(...)
```

## Пример вывода

Для: Reni → Alexandria, 55,000 MT Corn, $18/MT, Laycan 15-20 Dec 2025

```
FIRM OFFER

═══════════════════════════════════════════════════════

LOAD PORT: 1 GSB(A) RENI, UKRAINE

DISCHARGE PORT: 1 GSB(A) ALEXANDRIA, EGYPT

CARGO: 55,000 MTS OF CORN IN BULK STW ABT 49-50 WOG

LAYCAN: 15-20 DECEMBER 2025

FREIGHT: USD 18.00 PMT FIOST

DEMURRAGE: USD 9,000.00 PDPR BENDS

═══════════════════════════════════════════════════════
UKRAINE CLAUSES (DANUBE)
═══════════════════════════════════════════════════════

SULINA AND BYSTROE PASSING CHARGES FOR OWNRS ACCOUNT.
VSSL TO USE BYSTROE CHANNEL AS PRIORITY, IN CASE NOT AVAILABLE THEN SULINA CHANNEL.

TIME LOST DUE TO WAR/AIR RAID ALERTS NOT TO COUNT AS L/T

DEMURRAGE/DETENTION TO BE PAID TOGETHER WITH FREIGHT UPON COMPLETION OF DISCHARGE

═══════════════════════════════════════════════════════
EGYPT CLAUSES
═══════════════════════════════════════════════════════

AT DISCHARGE PORT N.O.R. TO BE TENDERED ON WORKING DAYS DURING OFFICE HRS (08:00-12:00 HRS) FROM SUNDAY TO THURSDAY

AT DISCHARGE PORT SAMPLING CARRIED OUT AS PER EGYPTIAN LAWS AND REGULATIONS. TIME FOR SAMPLING NOT TO COUNT AS L/T.

SATURDAYS, SUNDAYS AND HOLIDAYS INCLUDED (SHINC) AT LOAD PORT.
FRIDAYS, SATURDAYS AND HOLIDAYS INCLUDED (FHINC) AT DISCHARGE PORT.

═══════════════════════════════════════════════════════
CARGO CLAUSES (GRAIN)
═══════════════════════════════════════════════════════

LAST 3 CARGOES: CLEAN/HARMLESS/ODORLESS ONLY.
NO FERTILIZERS, CHEMICALS, COAL, OR OTHER CONTAMINATING CARGOES

CARGO TO BE PROPERLY TRIMMED, LEVELED AND STOWED IN ACCORDANCE WITH IMSBC CODE

═══════════════════════════════════════════════════════

OWISE AS PER ATTACHED CHRTS PROFORMA CP, BASED ON SYNACOMEX 2000 C/P
```

## Порядок работы

1. ✅ Изучи готовые JSON в /data
2. Создай backend/app/main.py с FastAPI
3. Создай backend/app/generator.py с логикой
4. Создай frontend/index.html с формой
5. Протестируй на сценарии "Reni → Alexandria, 55k corn"

## Критерии готовности

- [ ] Backend запускается: `uvicorn app.main:app --reload`
- [ ] POST /api/generate возвращает текст FO
- [ ] Frontend показывает форму
- [ ] Выбор портов подгружает правильные клаузы
- [ ] Текст FO содержит все нужные клаузы
- [ ] Кнопка Copy работает
