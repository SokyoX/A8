
import os
from datetime import datetime, timedelta, timezone

import requests

# API мотивашки Drinkit
URL = "https://motivationboard.drinkit.dodois.io/api/v1/boards"

PARAMS = {
    "countryId": 398,
    "unitId": "11f062d6-b6d4-a193-6491-5cdc834a1880",
    "locale": "ru",
}

# Telegram
TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]

# Необязательный ID темы Telegram
THREAD_ID = os.environ.get("TG_THREAD_ID")

# Время Алматы (UTC+5)
TZ = timezone(timedelta(hours=5))

# Отчёты с 09:00 до 23:00 включительно
FIRST_REPORT_HOUR = 9
LAST_REPORT_HOUR = 23

# Пороги нормативов
STD_GREEN = 90
STD_YELLOW = 80


def mmss(sec):
    minutes, seconds = divmod(int(sec), 60)
    return f"{minutes}:{seconds:02d}"


def build_message(data, end):
    start = end - timedelta(hours=1)

    hour = data["lastHourCounter"]
    likes = data["orderRatingCounter"]["likeCount"]
    dislikes = data["orderRatingCounter"]["dislikeCount"]
    std = data["productWithinStandardPercentageCounter"][
        "withinStandardPercentage"
    ]

    std_icon = (
        "🟢" if std >= STD_GREEN
        else "🟡" if std >= STD_YELLOW
        else "🔴"
    )

    dis_icon = "👎" if dislikes == 0 else "🔴"

    return (
        f"☕ <b>Отчёт за {start:%H:%M}–{end:%H:%M}</b>\n"
        f"<i>{data['unitName']} · {data['unitAlias']}</i>\n"
        f"\n"
        f"📦 Заказов за час: <b>{hour['readyOrderCount']}</b>\n"
        f"👍 Лайки: <b>{likes}</b>\n"
        f"{dis_icon} Дизлайки: <b>{dislikes}</b>\n"
        f"⏱ Среднее время: <b>{mmss(hour['readySecondsAvg'])}</b>\n"
        f"{std_icon} Нормативы: <b>{std}%</b>"
    )


def main():
    now = datetime.now(TZ)
    end = now.replace(minute=0, second=0, microsecond=0)

    # Проверяем рабочее время
    if (
        not FIRST_REPORT_HOUR <= end.hour <= LAST_REPORT_HOUR
        and os.environ.get("FORCE") != "1"
    ):
        print("Вне рабочих часов, пропускаю")
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

    # Формируем отчёт
    message = build_message(data, end)

    # Подготавливаем отправку в Telegram
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    # Если указан ID темы — отправляем в неё
    if THREAD_ID:
        payload["message_thread_id"] = int(THREAD_ID)

    print("Отправляю отчёт в Telegram...")

    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json=payload,
        timeout=20,
    )

    print("Telegram status:", resp.status_code)
    print("Telegram response:", resp.text)

    resp.raise_for_status()

    print("Отчёт успешно отправлен!")


if __name__ == "__main__":
    main()
