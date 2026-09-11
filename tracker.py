import os
import sys
import time
from playwright.sync_api import sync_playwright

# Параметры поездки (Сочи — Орша, 14.10.2026)
TARGET_URL = "https://rw.by"

def check_tickets():
    with sync_playwright() as p:
        print("🚀 Запуск браузера Chromium...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        captured_data = []

        # Перехватываем ответы от внутреннего API БЖД
        def handle_response(response):
            if "car_places" in response.url and response.status == 200:
                try:
                    captured_data.append(response.json())
                except:
                    pass

        page.on("response", handle_response)
        
        print(f"📡 Открываем страницу БЖД: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
        
        # Ждем загрузки таблицы с поездами
        try:
            page.wait_for_selector(".sch-table__row", timeout=20000)
            print("✅ Список поездов успешно загружен на странице.")
            
            # Находим кнопки классов/мест для раскрытия информации о вагонах
            buttons = page.locator(".sch-table__status, .sch-table__status-link")
            count = buttons.count()
            print(f"🔗 Найдено доступных вариантов/поездов для раскрытия: {count}")
            
            if count == 0:
                print("⚠️ Доступных кнопок выбора мест на странице не обнаружено.")
            
            for i in range(count):
                try:
                    if buttons.nth(i).is_visible():
                        print(f"🖱️ Симулируем клик по блоку мест #{i+1}...")
                        buttons.nth(i).click()
                        time.sleep(3)  # Пауза, чтобы API успело ответить
                except Exception as click_err:
                    print(f"❌ Не удалось кликнуть по блоку #{i+1}: {click_err}")
                    continue
                    
        except Exception as e:
            print("⚠️ Поезда на странице не найдены. Возможно, продажа еще не открыта или билеты раскуплены:", e)
            browser.close()
            return

        browser.close()
        print("🔒 Браузер закрыт. Начинаем анализ перехваченных данных...")

        if not captured_data:
            print("❌ Данные о конкретных местах в вагонах (API car_places) не были получены.")
            return

        print(f"📊 Получено ответов от API мест: {len(captured_data)}")
        lower_places_found = []

        # Парсим JSON структуры
        for data in captured_data:
            if 'cars' in data:
                train_number = data.get('train_number', 'Неизвестный')
                for car in data['cars']:
                    type_letter = car.get('type_letter', '?')
                    car_number = car.get('number', '?')
                    places = car.get('places', [])
                    
                    # Логируем в консоль вообще все типы вагонов, которые встретили
                    print(f"--- Поезд {train_number} | Вагон №{car_number} ({type_letter}) | Свободно мест: {len(places)} ---")
                    
                    # Ищем только Плацкарт ('П')
                    if type_letter == 'П':
                        for place in places:
                            place_num = int(place.get('number', 0))
                            # Нечетные номера — нижние полки
                            if place_num % 2 != 0:
                                type_text = "боковое" if place_num > 36 else "купейное"
                                item = f"Поезд {train_number}, Вагон {car_number}, место {place_num} ({type_text})"
                                lower_places_found.append(item)

        print("\n================ РЕЗУЛЬТАТ ПРОВЕРКИ ================")
        if lower_places_found:
            # Убираем возможные дубликаты
            lower_places_found = list(set(lower_places_found))
            print(f"🎉 НАЙДЕНО НИЖНИХ ПОЛОК В ПЛАЦКАРТЕ: {len(lower_places_found)}")
            for p in lower_places_found:
                print(f"📍 {p}")
        else:
            print("🔍 Поезда/вагоны обработаны, но нижних полок в плацкарте прямо сейчас нет.")
        print("====================================================")

if __name__ == "__main__":
    check_tickets()
