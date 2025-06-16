# pdf_parser.py (Версия 12, Финальная, основанная на фактах)

import fitz
import pandas as pd
import re
import os

PDF_PATH = "catalog.pdf"
OUTPUT_DIR = "parsed_data"


def parse_power_tables_from_text(text_content):
    """
    Самый надежный парсер, основанный на анализе реального вывода debug_output.txt.
    Он находит ВСЕ таблицы мощностей, собирает из них ОДИН поток чисел и затем
    структурирует его.
    """

    # --- Шаг 1: Найти и извлечь все числа из всех таблиц Pb ---

    # Находим весь текст, который находится между 'RPM / Ø' и 'Pd (kW)'
    # re.DOTALL позволяет точке (.) соответствовать также и символу новой строки
    power_blocks = re.findall(r"RPM / Ø(.*?)Pd \(kW\)", text_content, re.DOTALL)

    if not power_blocks:
        print("ОШИБКА: Не удалось найти блоки таблиц с мощностью (между 'RPM / Ø' и 'Pd (kW)').")
        return None

    all_numbers_from_tables = []
    for block in power_blocks:
        # Внутри каждого блока находим абсолютно все числа
        # Убираем звездочки, заменяем запятые на точки
        cleaned_block = block.replace(',', '.').replace('*', '')
        numbers_in_block = re.findall(r'[\d\.]+', cleaned_block)
        all_numbers_from_tables.extend(numbers_in_block)

    # --- Шаг 2: Собрать из потока чисел шапку и данные ---

    diameters = []
    data_stream = []
    header_collected = False

    for num_str in all_numbers_from_tables:
        # RPM - это целые числа от 100 и выше. В PDF они могут быть как "100" или "1.000".
        # Мы убираем точку, чтобы получить само число для проверки.
        cleaned_num_str = num_str.replace('.', '')

        # Если мы еще не собрали шапку
        if not header_collected:
            # Проверяем, является ли текущее число началом данных (т.е. RPM)
            if cleaned_num_str.isdigit() and int(cleaned_num_str) >= 100:
                # Да, это RPM. Сбор шапки окончен.
                header_collected = True
                # Это число уже относится к данным, добавляем его в поток данных
                data_stream.append(num_str)
            else:
                # Нет, это диаметр. Добавляем в шапку.
                diameters.append(float(num_str))
        else:
            # Шапка уже собрана, все последующие числа - это данные
            data_stream.append(num_str)

    # --- Шаг 3: Превратить поток данных в структурированную таблицу ---

    if not diameters or not data_stream:
        print("ОШИБКА: Не удалось собрать шапку с диаметрами или поток данных.")
        return None

    final_data = []
    row_width = len(diameters) + 1  # Ширина строки = 1 RPM + кол-во диаметров

    # Нарезаем поток данных на строки правильной ширины
    # len(data_stream) // row_width - это количество полных строк, которые мы можем составить
    num_full_rows = len(data_stream) // row_width

    for i in range(num_full_rows):
        row_start_index = i * row_width
        row = data_stream[row_start_index: row_start_index + row_width]

        try:
            # Первое число в строке - это RPM
            rpm = int(row[0].replace('.', ''))
            # Остальные - мощности
            power_values = [float(p) for p in row[1:]]

            # Сопоставляем каждую мощность с ее диаметром из шапки
            for j, power in enumerate(power_values):
                final_data.append({
                    'd': diameters[j],
                    'n1': rpm,
                    'Pb': power
                })
        except (ValueError, IndexError):
            # Пропускаем строку, если в ней мусор
            continue

    return final_data


def main():
    print(f"===== Запуск парсера PDF (Версия 12, Финальная) =====")
    if not os.path.exists(PDF_PATH):
        print(f"ОШИБКА: Файл '{PDF_PATH}' не найден.")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Читаем ТОЛЬКО страницы с таблицами мощности Pb ---
    PROFILE_MAP = {'C': [37, 39]}

    for profile, pages_indices in PROFILE_MAP.items():
        print(f"\n--- Обработка профиля: {profile} ---")
        text_content = ""
        with fitz.open(PDF_PATH) as doc:
            for page_num in pages_indices:
                if page_num < len(doc):
                    print(f"Читаю страницу {page_num + 1}...")
                    page = doc[page_num]
                    text_content += page.get_text("text") + "\n"

        full_data = parse_power_tables_from_text(text_content)

        if not full_data:
            print(f"ОШИБКА: Не удалось извлечь данные для профиля {profile}.")
            continue

        df = pd.DataFrame(full_data)
        output_filename = os.path.join(OUTPUT_DIR, f"power_data_{profile}_Pb.csv")
        df.to_csv(output_filename, index=False)

        print(f"\nУСПЕШНО: Профиль {profile} обработан. Извлечено {len(df)} строк.")
        print(f"Файл сохранен: {output_filename}")

    print("\n===== Парсинг завершен! =====")


if __name__ == "__main__":
    main()