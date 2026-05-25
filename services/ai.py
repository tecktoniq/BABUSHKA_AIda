import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL", "anthropic/claude-haiku-4-5")

SYSTEM_PROMPT = """Ты — Бабушка AIda, мудрая и тёплая гадалка с многолетним опытом.
Твой стиль: тёплый, загадочный, заботливый. Говоришь с лёгкой мистикой.
Обращайся к пользователю по имени или "дитя моё". Никогда не будь холодной или формальной.
Пиши кратко но ёмко — 3-5 предложений на карту, 5-7 на вердикт.
Не используй markdown, звёздочки, хэштеги. Только живой тёплый текст."""


async def ask_aida(prompt: str) -> str:
    """Отправить запрос к Claude Haiku через OpenRouter"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 400,
                "temperature": 0.9,
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def interpret_card(name: str, card: dict, position: str, topic: str, question: str) -> str:
    """Интерпретация одной карты"""
    prompt = f"""Имя пользователя: {name}
Тема расклада: {topic}
Вопрос: {question}
Карта: {card['name']} ({card['position_label']})
Значение карты: {card['meaning']}
Позиция в раскладе: {position}

Дай живую интерпретацию этой карты от лица Бабушки AIda. 
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
Учитывай знак зодиака и карту дня. Тепло, мистично, с надеждой. 
Обращайся к {name} по имени."""
    return await ask_aida(prompt)


async def get_soul_card_reading(name: str, soul_card: dict) -> str:
    """Чтение карты судьбы"""
    prompt = f"""Имя: {name}
Карта судьбы (карта души): {soul_card['name']}
Значение: {soul_card['upright']}

Расскажи {name} о её карте судьбы от лица Бабушки AIda.
Это очень личное — карта на всю жизнь. Говори глубоко и тепло."""
    return await ask_aida(prompt)
