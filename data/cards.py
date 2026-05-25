import random

# Старшие арканы
MAJOR_ARCANA = [
    {"id": 0, "name": "Шут", "name_en": "The Fool", "upright": "новое начало, спонтанность, свобода", "reversed": "безрассудство, риск, наивность"},
    {"id": 1, "name": "Маг", "name_en": "The Magician", "upright": "сила воли, мастерство, ресурсы", "reversed": "манипуляция, слабая воля, иллюзии"},
    {"id": 2, "name": "Верховная Жрица", "name_en": "The High Priestess", "upright": "интуиция, тайное знание, внутренний голос", "reversed": "секреты, молчание, скрытое"},
    {"id": 3, "name": "Императрица", "name_en": "The Empress", "upright": "плодородие, красота, изобилие", "reversed": "зависимость, творческий блок"},
    {"id": 4, "name": "Император", "name_en": "The Emperor", "upright": "власть, стабильность, структура", "reversed": "тирания, жёсткость, негибкость"},
    {"id": 5, "name": "Иерофант", "name_en": "The Hierophant", "upright": "традиции, духовность, наставник", "reversed": "бунт, нетрадиционность"},
    {"id": 6, "name": "Влюблённые", "name_en": "The Lovers", "upright": "любовь, гармония, выбор", "reversed": "дисгармония, дисбаланс, разрыв"},
    {"id": 7, "name": "Колесница", "name_en": "The Chariot", "upright": "победа, воля, контроль", "reversed": "отсутствие контроля, агрессия"},
    {"id": 8, "name": "Сила", "name_en": "Strength", "upright": "сила, терпение, сострадание", "reversed": "слабость, неуверенность"},
    {"id": 9, "name": "Отшельник", "name_en": "The Hermit", "upright": "уединение, мудрость, поиск", "reversed": "изоляция, одиночество"},
    {"id": 10, "name": "Колесо Фортуны", "name_en": "Wheel of Fortune", "upright": "удача, перемены, судьба", "reversed": "неудача, сопротивление переменам"},
    {"id": 11, "name": "Справедливость", "name_en": "Justice", "upright": "справедливость, истина, закон", "reversed": "несправедливость, нечестность"},
    {"id": 12, "name": "Повешенный", "name_en": "The Hanged Man", "upright": "пауза, отпускание, жертва", "reversed": "задержки, сопротивление"},
    {"id": 13, "name": "Смерть", "name_en": "Death", "upright": "трансформация, конец и начало", "reversed": "сопротивление переменам, стагнация"},
    {"id": 14, "name": "Умеренность", "name_en": "Temperance", "upright": "баланс, терпение, цель", "reversed": "дисбаланс, излишества"},
    {"id": 15, "name": "Дьявол", "name_en": "The Devil", "upright": "зависимость, материализм, тени", "reversed": "освобождение, осознание"},
    {"id": 16, "name": "Башня", "name_en": "The Tower", "upright": "внезапные перемены, разрушение", "reversed": "избегание катастрофы, страх"},
    {"id": 17, "name": "Звезда", "name_en": "The Star", "upright": "надежда, вдохновение, обновление", "reversed": "отчаяние, разочарование"},
    {"id": 18, "name": "Луна", "name_en": "The Moon", "upright": "иллюзии, страхи, подсознание", "reversed": "путаница, страх, обман"},
    {"id": 19, "name": "Солнце", "name_en": "The Sun", "upright": "радость, успех, жизненная сила", "reversed": "пессимизм, депрессия"},
    {"id": 20, "name": "Суд", "name_en": "Judgement", "upright": "пробуждение, прощение, обновление", "reversed": "самосуд, сомнения"},
    {"id": 21, "name": "Мир", "name_en": "The World", "upright": "завершение, интеграция, успех", "reversed": "незавершённость, стагнация"},
]

# Масти младших арканов
SUITS = [
    {"name": "Жезлов", "element": "огонь", "theme": "творчество, энергия, действие"},
    {"name": "Кубков", "element": "вода", "theme": "эмоции, отношения, интуиция"},
    {"name": "Мечей", "element": "воздух", "theme": "мысли, конфликты, истина"},
    {"name": "Пентаклей", "element": "земля", "theme": "деньги, работа, материальное"},
]

RANKS = ["Туз", "Двойка", "Тройка", "Четвёрка", "Пятёрка", "Шестёрка",
         "Семёрка", "Восьмёрка", "Девятка", "Десятка",
         "Паж", "Рыцарь", "Королева", "Король"]

# Генерируем все 56 младших арканов
MINOR_ARCANA = []
for suit in SUITS:
    for rank in RANKS:
        MINOR_ARCANA.append({
            "name": f"{rank} {suit['name']}",
            "upright": f"{suit['theme']}",
            "reversed": f"заблокированная энергия {suit['element']}а",
        })

ALL_CARDS = MAJOR_ARCANA + MINOR_ARCANA


def draw_cards(n=3):
    """Вытащить n случайных карт из колоды"""
    drawn = random.sample(ALL_CARDS, n)
    result = []
    for card in drawn:
        is_reversed = random.choice([True, False])
        result.append({
            "name": card["name"],
            "is_reversed": is_reversed,
            "meaning": card["reversed"] if is_reversed else card["upright"],
            "position_label": "перевёрнутая" if is_reversed else "прямая",
        })
    return result


def get_soul_card(birthdate_str):
    """Карта судьбы по дате рождения"""
    try:
        digits = [int(d) for d in birthdate_str if d.isdigit()]
        total = sum(digits)
        while total > 21:
            total = sum(int(d) for d in str(total))
        for card in MAJOR_ARCANA:
            if card["id"] == total:
                return card
        return MAJOR_ARCANA[0]
    except:
        return MAJOR_ARCANA[0]


def get_zodiac(birthdate_str):
    """Знак зодиака по дате рождения"""
    try:
        parts = birthdate_str.split(".")
        day, month = int(parts[0]), int(parts[1])
        signs = [
            (1, 20, "Козерог ♑"), (2, 19, "Водолей ♒"),
            (3, 20, "Рыбы ♓"), (4, 20, "Овен ♈"),
            (5, 21, "Телец ♉"), (6, 21, "Близнецы ♊"),
            (7, 22, "Рак ♋"), (8, 23, "Лев ♌"),
            (9, 23, "Дева ♍"), (10, 23, "Весы ♎"),
            (11, 22, "Скорпион ♏"), (12, 22, "Стрелец ♐"),
            (12, 31, "Козерог ♑"),
        ]
        for end_day, end_month, sign in signs:
            if month < end_month or (month == end_month and day <= end_day):
                return sign
        return "Козерог ♑"
    except:
        return "неизвестен"
