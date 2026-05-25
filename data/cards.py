import random
from datetime import datetime

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

TAROT_IMAGE_BASE_URL = "https://www.free-tarot-reading.net/img/cards/rider-waite"

MAJOR_IMAGE_SLUGS = {
    0: "the-fool",
    1: "the-magician",
    2: "the-high-priestess",
    3: "the-empress",
    4: "the-emperor",
    5: "the-hierophant",
    6: "the-lovers",
    7: "the-chariot",
    8: "strength",
    9: "the-hermit",
    10: "wheel-of-fortune",
    11: "justice",
    12: "the-hanged-man",
    13: "death",
    14: "temperance",
    15: "the-devil",
    16: "the-tower",
    17: "the-star",
    18: "the-moon",
    19: "the-sun",
    20: "judgement",
    21: "the-world",
}

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

RANK_SLUGS = {
    "Туз": "ace",
    "Двойка": "two",
    "Тройка": "three",
    "Четвёрка": "four",
    "Пятёрка": "five",
    "Шестёрка": "six",
    "Семёрка": "seven",
    "Восьмёрка": "eight",
    "Девятка": "nine",
    "Десятка": "ten",
    "Паж": "page",
    "Рыцарь": "knight",
    "Королева": "queen",
    "Король": "king",
}

SUIT_SLUGS = {
    "Жезлов": "wands",
    "Кубков": "cups",
    "Мечей": "swords",
    "Пентаклей": "pentacles",
}

# Генерируем все 56 младших арканов
MINOR_ARCANA = []
for suit_index, suit in enumerate(SUITS):
    for rank_index, rank in enumerate(RANKS):
        MINOR_ARCANA.append({
            "id": 22 + suit_index * len(RANKS) + rank_index,
            "name": f"{rank} {suit['name']}",
            "name_en": f"{RANK_SLUGS[rank].title()} of {SUIT_SLUGS[suit['name']].title()}",
            "upright": f"{suit['theme']}",
            "reversed": f"заблокированная энергия {suit['element']}а",
            "image_slug": f"{RANK_SLUGS[rank]}-of-{SUIT_SLUGS[suit['name']]}",
        })

for card in MAJOR_ARCANA:
    card["image_slug"] = MAJOR_IMAGE_SLUGS[card["id"]]

ALL_CARDS = MAJOR_ARCANA + MINOR_ARCANA


def get_card_image_url(card: dict) -> str:
    """URL картинки карты из колоды Rider-Waite."""
    return f"{TAROT_IMAGE_BASE_URL}/{card['image_slug']}.jpg"


def draw_cards(n=3):
    """Вытащить n случайных карт из колоды без повторов.

    random.sample делает выбор без возвращения: первая карта имеет шанс 1/78,
    вторая вытягивается из оставшихся 77, третья - из оставшихся 76.
    Перевёрнутая позиция считается отдельно, шанс 50/50 для каждой карты.
    """
    drawn = random.sample(ALL_CARDS, n)
    result = []
    for card in drawn:
        is_reversed = random.choice([True, False])
        result.append({
            "id": card["id"],
            "name": card["name"],
            "name_en": card.get("name_en", card["name"]),
            "is_reversed": is_reversed,
            "meaning": card["reversed"] if is_reversed else card["upright"],
            "position_label": "перевёрнутая" if is_reversed else "прямая",
            "image_url": get_card_image_url(card),
        })
    return result


def parse_birthdate(birthdate_str):
    """Вернуть дату рождения из форматов ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ."""
    normalized = birthdate_str.strip().replace("/", ".").replace("-", ".")
    return datetime.strptime(normalized, "%d.%m.%Y").date()


def normalize_birthdate(birthdate_str):
    return parse_birthdate(birthdate_str).strftime("%d.%m.%Y")


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
        birthdate = parse_birthdate(birthdate_str)
        day, month = birthdate.day, birthdate.month
        signs = [
            ((1, 20), "Водолей ♒"),
            ((2, 19), "Рыбы ♓"),
            ((3, 21), "Овен ♈"),
            ((4, 20), "Телец ♉"),
            ((5, 21), "Близнецы ♊"),
            ((6, 21), "Рак ♋"),
            ((7, 23), "Лев ♌"),
            ((8, 23), "Дева ♍"),
            ((9, 23), "Весы ♎"),
            ((10, 23), "Скорпион ♏"),
            ((11, 22), "Стрелец ♐"),
            ((12, 22), "Козерог ♑"),
        ]
        for (start_month, start_day), sign in reversed(signs):
            if (month, day) >= (start_month, start_day):
                return sign
        return "Козерог ♑"
    except ValueError:
        return "неизвестен"
