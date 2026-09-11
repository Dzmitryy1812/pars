import os
import sys
import time
from playwright.sync_api import sync_playwright

# ПРЯМАЯ И ПОЛНАЯ ССЫЛКА НА ВАШ МАРШРУТ (СОЧИ - ОРША НА 14.10.2026)
TARGET_URL = (
    "https://rw.by?"
    "from=%D0%A1%D0%BE%D1%87%D0%B8"
    "&from_exp=2064130"
    "&from_esr=0"
    "&to=%D0%9E%D1%80%D1%88%D0%B0"
    "&to_exp=2100170"
    "&to_esr=166403"
    "&date=2026-10-14"
    "&type=1"
)

def check_tickets():
    with sync_playwright() as p:
        print("🚀 Запуск маскированного браузера Chromium...")
        
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="ru-RU",
            timezone_id="Europe/Minsk"
        )
        
        page = context.new_page()
        page.add_init_script("delete navigator.__proto__.webdriver;")
        
        captured_data = []

        # Ловим ответы от API мест БЖД
        def handle_response(response):
            if "car_places" in response.url and response.status == 200:
                try:
                    captured_data.append(response.json())
                    print("🎯 API мест успешно перехвачено!")
                except:
                    pass

        page.on("response", handle_response)
        
        print(f"📡 Открываем страницу БЖД: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="commit", timeout=60000)
        
        # Даем сайту загрузить интерфейс
        time.sleep(8)
        
        try:
            # Ожидаем появление поездов
            page.wait_for_selector(".sch-table__row, .sch-table__body", timeout=30000)
            print("✅ Расписание поездов успешно отображено на странице.")
            
            # Находим кнопки раскрытия вагонов
            buttons = page.locator(".sch-table__status, .sch-table__status-link, .sch-table__status-info")
            count = buttons.count()
            print(f"🔗 Найдено доступных блоков поездов для раскрытия: {count}")
            
            for i in range(count):
                try:
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        time.sleep(1)
                        btn.click()
                        print(f"   鼠标 Клик по блоку мест #{i+1}")
                        time.sleep(4)
                except:
                    continue
                    
        except Exception as e:
            print("⚠️ Не удалось найти таблицу поездов. Страница заблокирована или пустая.")
            try:
                print(f"Фактический URL в браузере: {page.url}")
                print(f"Заголовок страницы: '{page.title()}'")
            except:
                pass
            browser.close()
            return

        browser.close()
        print("🔒 Браузер закрыт. Анализ результатов...")

        if not captured_data:
            print("❌ Свободные места в вагонах не найдены (API не вернуло car_places).")
            return

        lower_places_found = []

        for data in captured_data:
            if 'cars' in data:
                train_number = data.get('train_number', 'Неизвестный')
                for car in data['cars']:
                    type_letter = car.get('type_letter', '?')
                    car_number = car.get('number', '?')
                    places = car.get('places', [])
                    
                    if type_letter == 'П':  # Плацкарт
                        for place in places:
                            place_num = int(place.get('number', 0))
                            if place_num % 2 != 0:  # Нижнее место
                                type_text = "боковое" if place_num > 36 else "купейное"
                                lower_places_found.append(
                                    f"Поезд {train_number}, Вагон {car_number}, место {place_num} ({type_text})"
                                )

        print("\n================ РЕЗУЛЬТАТ ПРОВЕРКИ ================")
        if lower_places_found:
            lower_places_found = list(set(lower_places_found))
            print(f"🎉 НАЙДЕНО НИЖНИХ ПОЛОК В ПЛАЦКАРТЕ: {len(lower_places_found)}")
            for p in lower_places_found:
                print(f"📍 {p}")
        else:
            print("🔍 Поезда обработаны, но нижних полок в плацкарте сейчас нет.")
        print("====================================================")

if __name__ == "__main__":
    check_tickets()
