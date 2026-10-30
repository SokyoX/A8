
import os
from datetime import datetime, timedelta, timezone

import requests

# API Drinkit
URL = "https://motivationboard.drinkit.dodois.io/api/v1/boards"

PARAMS = {
    "countryId": 398,
    "unitId": "11f062d6-b6d4-a193-6491-5cdc834a1880",
    "locale": "ru",
}

# Telegram settings
TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]
THREAD_ID = os.environ["TG_THREAD_ID"]

if not THREAD_ID.isdigit():
    raise ValueError("TG_THREAD_ID должен содержать числовой ID темы")

THREAD_ID = int(THREAD_ID)

# Алматы UTC+5
TZ = timezone(timedelta(hours=5))

# Время отправки
FIRST_REPORT_HOUR = 10
LAST_REPORT_HOUR = 23

# Пороги нормативов
STD_GREEN = 90
STD_YELLOW = 80


def mmss(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


def build_message(data, end):
    start = end - timedelta(hours=1)

    hour = data["lastHourCounter"]
    likes = data["orderRatingCounter"]["likeCount"]
    dislikes = data["orderRatingCounter"]["dislikeCount"]

    std = data["productWithinStandardPercentageCounter"][
        "withinStandardPercentage"
    ]

    if std >= STD_GREEN:
        std_icon = "🟢"
    elif std >= STD_YELLOW:
        std_icon = "🟡"
    else:
        std_icon = "🔴"

    dis_icon = "👎" if dislikes == 0 else "🔴"

    return (
        f"☕ <b>Отчёт за {start:%H:%M}–{end:%H:%M}</b>\n"
        f"<i>{data['unitName']} · {data['unitAlias']}</i>\n\n"
        f"📦 Заказов за час: <b>{hour['readyOrderCount']}</b>\n"
        f"👍 Лайки: <b>{likes}</b>\n"
        f"{dis_icon} Дизлайки: <b>{dislikes}</b>\n"
        f"⏱ Среднее время: <b>{mmss(hour['readySecondsAvg'])}</b>\n"
        f"{std_icon} Нормативы: <b>{std}%</b>"
    )


def main():
    now = datetime.now(TZ)
    end = now.replace(minute=0, second=0, microsecond=0)

    # Проверка рабочего времени
    if (
        not FIRST_REPORT_HOUR <= end.hour <= LAST_REPORT_HOUR
        and os.environ.get("FORCE") != "1"
    ):
        print("Вне рабочих часов. Отправка пропущена.")
        return

    # Получаем данные мотивашки
    print("Получаю данные Drinkit...")

    response = requests.get(
        URL,
        params=PARAMS,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()

    if isinstance(data, list):
        if not data:
            raise ValueError("API вернул пустой список")
        data = data[0]

    # Создаём сообщение
    message = build_message(data, end)

    # Отправляем строго в указанную тему
    payload = {
        "chat_id": CHAT_ID,
        "message_thread_id": THREAD_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    print(f"Отправляю отчёт в тему {THREAD_ID}...")

    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json=payload,
        timeout=20,
    )

    print("Telegram status:", resp.status_code)
    print("Telegram response:", resp.text)

    resp.raise_for_status()

    print("Отчёт успешно отправлен в нужную тему!")


if __name__ == "__main__":
    main()
