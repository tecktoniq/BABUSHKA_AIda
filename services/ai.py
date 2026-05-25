import httpx
import logging
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL", "anthropic/claude-haiku-4-5")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "openrouter/free")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — Бабушка AIda, мудрая и тёплая гадалка с многолетним опытом.
Твой стиль: тёплый, загадочный, заботливый. Говоришь с лёгкой мистикой.
Обращайся к пользователю по имени или "дитя моё". Никогда не будь холодной или формальной.
Пиши кратко но ёмко — 3-5 предложений на карту, 5-7 на вердикт.
Отвечай только на русском языке. Не вставляй английские слова, английские заголовки и смешанный язык.
Не используй слова "AI", "ИИ", "анализ", "prompt", "карточный spread".
Не используй markdown, звёздочки, хэштеги. Только живой тёплый русский текст."""


async def ask_aida(prompt: str) -> str:
    """Отправить запрос к Claude Haiku через OpenRouter"""
    if not OPENROUTER_API_KEY:
        return local_fallback_answer(prompt)

    models = []
    for model in (MODEL, FALLBACK_MODEL):
        if model and model not in models:
            models.append(model)

    async with httpx.AsyncClient(timeout=30) as client:
        for model in models:
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/tecktoniq/BABUSHKA_AIda",
                        "X-Title": "BABUSHKA AIda",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 700,
                        "temperature": 0.85,
                    }
                )
                data = response.json()
                if response.status_code >= 400:
                    logger.warning("OpenRouter model %s failed: %s %s", model, response.status_code, data)
                    continue
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content")
                if content:
                    return content.strip()
                logger.warning("OpenRouter model %s returned no content: %s", model, data)
            except Exception as exc:
                logger.warning("OpenRouter request failed for %s: %s", model, exc)

    return local_fallback_answer(prompt)


def local_fallback_answer(prompt: str) -> str:
    """Мягкий резервный ответ, чтобы сценарий не ломался при ошибке API."""
    if "Карта судьбы" in prompt:
        return (
            "Карты шепчут, что эта карта судьбы описывает главный внутренний урок: "
            "как человек принимает себя, где берёт силу и через что растёт. "
            "Смотри на неё не как на приговор, а как на ключ: она показывает привычный путь души, "
            "её сильные стороны и место, где важно быть честнее с собой."
        )
    if "итоговый вердикт" in prompt.lower() or "Карты расклада" in prompt:
        return (
            "Если собрать три карты вместе, получается не случайный набор, а цепочка: "
            "прошлое показывает корень ситуации, настоящее — то, что требует внимания сейчас, "
            "а будущее — направление, куда всё может повернуть. "
            "Главный совет простой: не спешить, увидеть повторяющийся узор и выбрать действие, "
            "которое возвращает тебе спокойствие и власть над своей дорогой."
        )
    return (
        "Эта карта говорит о движении энергии вокруг твоего вопроса. "
        "В прямом положении она больше поддерживает и открывает путь, "
        "в перевёрнутом — показывает задержку, страх или место, где сила пока заблокирована. "
        "Прислушайся к первому ощущению: карта не приказывает, она подсвечивает то, что уже созрело внутри."
    )


async def interpret_card(name: str, card: dict, position: str, topic: str, question: str) -> str:
    """Интерпретация одной карты"""
    prompt = f"""Имя пользователя: {name}
Тема расклада: {topic}
Вопрос: {question}
Карта: {card['name']} ({card['position_label']})
Значение карты: {card['meaning']}
Позиция в раскладе: {position}

Дай живое толкование этой карты от лица Бабушки AIda.
Пиши только по-русски, без английских слов и технических терминов.
Учитывай тему вопроса и позицию карты. Обращайся к {name} по имени."""
    return await ask_aida(prompt)


async def get_verdict(name: str, topic: str, question: str, cards: list, interpretations: list) -> str:
    """Итоговый вердикт по всем трём картам"""
    cards_text = "\n".join([
        f"- {c['name']} ({c['position_label']}): {c['meaning']}"
        for c in cards
    ])
    prompt = f"""Имя пользователя: {name}
Тема: {topic}
Вопрос: {question}
Карты расклада:
{cards_text}

Дай итоговый вердикт по всему раскладу от лица Бабушки AIda.
Пиши только по-русски, без английских слов и технических терминов.
Свяжи все три карты вместе, дай мудрый совет для {name}.
Заверши тёплой фразой с заботой."""
    return await ask_aida(prompt)


async def get_daily_horoscope(name: str, zodiac: str, card_name: str, card_meaning: str) -> str:
    """Персональный гороскоп на день"""
    prompt = f"""Имя: {name}
Знак зодиака: {zodiac}
Карта дня: {card_name}
Значение карты: {card_meaning}

Напиши персональный утренний гороскоп от Бабушки AIda для {name}.
Пиши только по-русски, без английских слов и технических терминов.
Учитывай знак зодиака и карту дня. Тепло, мистично, с надеждой. 
Обращайся к {name} по имени."""
    return await ask_aida(prompt)


async def get_soul_card_reading(name: str, soul_card: dict) -> str:
    """Чтение карты судьбы"""
    prompt = f"""Имя: {name}
Карта судьбы (карта души): {soul_card['name']}
Значение: {soul_card['upright']}

Расскажи {name} о карте судьбы от лица Бабушки AIda.
Пиши только по-русски, без английских слов и технических терминов.
Это очень личное — карта на всю жизнь. Говори глубоко и тепло."""
    return await ask_aida(prompt)


async def get_soul_card_analysis(name: str, birthdate: str, calculation: dict, soul_card: dict) -> str:
    """Развёрнутый анализ карты судьбы с логикой расчёта."""
    digits = " + ".join(str(d) for d in calculation["digits"])
    steps = " → ".join(str(step) for step in calculation["steps"])
    prompt = f"""Имя: {name}
Дата рождения: {birthdate}
Расчёт карты судьбы:
Цифры даты: {digits}
Сумма и приведение к старшему аркану: {steps}
Итоговый номер карты: {calculation['card_id']}
Карта судьбы: {soul_card['name']}
Значение карты: {soul_card['upright']}

Объясни логику расчёта простыми словами и дай интересный развернутый результат по карте судьбы.
Пиши только по-русски, без английских слов и технических терминов.
Структура ответа:
1. Как посчитали карту.
2. Что эта карта говорит о характере и внутреннем пути.
3. Сильные стороны.
4. Теневая сторона и совет.
Пиши от лица Бабушки AIda, тепло и мистично, но без обращения к полу пользователя."""
    return await ask_aida(prompt)
