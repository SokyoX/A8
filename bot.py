import os
from datetime import datetime, timedelta, timezone

import requests

URL = "https://motivationboard.drinkit.dodois.io/api/v1/boards"
PARAMS = {
    "countryId": 398,
    "unitId": "11f062d6-b6d4-a193-6491-5cdc834a1880",
    "locale": "ru",
}

TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]

TZ = timezone(timedelta(hours=5))  # Алматы
# Отчёты шлём только если конец отчётного часа попадает в этот диапазон.
# Например 9..23 -> первый отчёт "08:00-09:00", последний "22:00-23:00".
FIRST_REPORT_HOUR, LAST_REPORT_HOUR = 9, 23

# Пороги для цвета нормативов (поменяй под свои нормы)
STD_GREEN, STD_YELLOW = 90, 80


def mmss(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def build_message(d, end):
    start = end - timedelta(hours=1)
    hour = d["lastHourCounter"]
    likes = d["orderRatingCounter"]["likeCount"]
    dislikes = d["orderRatingCounter"]["dislikeCount"]
    std = d["productWithinStandardPercentageCounter"]["withinStandardPercentage"]

    std_icon = "🟢" if std >= STD_GREEN else "🟡" if std >= STD_YELLOW else "🔴"
    dis_icon = "👎" if dislikes == 0 else "🔴"

    return (
        f"☕ <b>Отчёт за {start:%H:%M}–{end:%H:%M}</b>\n"
        f"<i>{d['unitName']} · {d['unitAlias']}</i>\n"
        f"\n"
        f"📦 Заказов за час: <b>{hour['readyOrderCount']}</b>\n"
        f"👍 Лайки: <b>{likes}</b>\n"
        f"{dis_icon} Дизлайки: <b>{dislikes}</b>\n"
        f"⏱ Среднее время: <b>{mmss(hour['readySecondsAvg'])}</b>\n"
        f"{std_icon} Нормативы: <b>{std}%</b>"
    )


def main():
    now = datetime.now(TZ)
    end = now.replace(minute=0, second=0, microsecond=0)  # 16:07 -> 16:00

    if not (FIRST_REPORT_HOUR <= end.hour <= LAST_REPORT_HOUR) and os.environ.get("FORCE") != "1":
        print("Вне рабочих часов, пропускаю")
        return

    r = requests.get(URL, params=PARAMS, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):  # ответ приходит списком из одного элемента
        data = data[0]

    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": build_message(data, end),
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    resp.raise_for_status()


if __name__ == "__main__":
    main()
