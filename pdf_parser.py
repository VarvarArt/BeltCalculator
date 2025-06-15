# pdf_parser.py (Версия 4, потоковый парсер)

import fitz
import pandas as pd
import re
import os

PDF_PATH = "catalog.pdf"
OUTPUT_DIR = "parsed_data"


def parse_catalog_text(combined_text):
    """
    Парсер, использующий "потоковую" логику для обработки таблиц,
    где каждая ячейка может быть на новой строке.
    """
    state = "WAITING_FOR_HEADER"
    header_diameters = []
    collected_values = []
    final_data = []

    # Набор известных RPM для определения начала данных
    known_rpms = {str(i * 100) for i in range(1, 31)}
    known_rpms.update({str(i * 50) for i in range(1, 61)})
    known_rpms.add('75')

    lines = combined_text.split('\n')
    print("--- [DEBUG] Начинаю обработку. Всего физических строк:", len(lines), "---")

    for i, line in enumerate(lines):
        cleaned_line = line.replace(',', '.').replace('\xa0', ' ').strip()
        if not cleaned_line:
            continue

        if state == "WAITING_FOR_HEADER":
            if "RPM / Ø" in cleaned_line:
                state = "READING_HEADER"
                print(f"--- [DEBUG] Строка {i}: Нашел заголовок 'RPM / Ø'. Переключаюсь в режим 'READING_HEADER'.")
            continue

        if state == "READING_HEADER":
            values = re.findall(r'[\d\.]+', cleaned_line)
            if not values:
                continue

            # Если первое значение в строке - это известный RPM, значит, шапка закончилась
            if values[0] in known_rpms:
                state = "READING_DATA"
                print(f"--- [DEBUG] Строка {i}: Нашел первый RPM '{values[0]}'. Шапка таблицы собрана.")
                print(f"--- [DEBUG] Собрано {len(header_diameters)} диаметров: {header_diameters}")
                print("--- [DEBUG] Переключаюсь в режим 'READING_DATA'.")
                # Эта строка уже содержит данные, поэтому обрабатываем ее ниже
            else:
                # Иначе, это часть шапки - добавляем диаметры
                header_diameters.extend(values)
                continue

        if state == "READING_DATA":
            values = re.findall(r'[\d\.]+', cleaned_line)
            if not values:
                continue

            # Накапливаем все найденные числа в один большой список
            collected_values.extend(values)

    # --- После того, как все строки прочитаны, начинаем разбор накопленных данных ---
    if not header_diameters:
        print("--- [CRITICAL ERROR] Шапка с диаметрами не была найдена! ---")
        return None

    print(f"\n--- [DEBUG] Разбор накопленных данных. Собрано {len(collected_values)} чисел. ---")

    # +1 для столбца с RPM
    row_length = len(header_diameters) + 1

    # Проходим по списку, "отрезая" куски длиной в один логический ряд
    for i in range(0, len(collected_values), row_length):
        full_row = collected_values[i: i + row_length]

        if len(full_row) < row_length:
            print(f"--- [DEBUG] Пропускаю неполный ряд в конце. Длина: {len(full_row)}/{row_length}")
            continue

        rpm = full_row[0]
        power_values = full_row[1:]

        for idx, power_str in enumerate(power_values):
            try:
                final_data.append({
                    'd': float(header_diameters[idx]),
                    'n1': float(rpm),
                    'Pb': float(power_str)
                })
            except (ValueError, IndexError):
                continue

    return final_data


def main():
    print(f"===== Запуск парсера PDF (Версия 4) для профиля 'C' =====")

    if not os.path.exists(PDF_PATH):
        print(f"ОШИБКА: Файл '{PDF_PATH}' не найден.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    profile_to_test = 'C'
    pages = [37, 38, 39, 40]

    combined_text = ""
    print(f"--- Чтение страниц {', '.join(str(p + 1) for p in pages)} для профиля '{profile_to_test}' ---")

    with fitz.open(PDF_PATH) as doc:
        for page_num in pages:
            page = doc[page_num]
            combined_text += page.get_text("text") + "\n"

    print("--- Текст со страниц объединен. Начинаю извлечение. ---")
    extracted_data = parse_catalog_text(combined_text)

    if not extracted_data:
        print("\nОШИБКА: Не удалось извлечь данные.")
        return

    df = pd.DataFrame(extracted_data)

    output_filename = os.path.join(OUTPUT_DIR, f"power_data_{profile_to_test}_Pb.csv")
    df.to_csv(output_filename, index=False)

    print(f"\n===== Парсинг УСПЕШНО завершен! =====")
    print(f"Извлечено {len(df)} строк данных (точек d-n1-Pb).")
    print(f"Результат сохранен в файл: {output_filename}")


if __name__ == "__main__":
    main()