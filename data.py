# data.py (Исправленная версия для корректной работы калькулятора)

import pandas as pd
import os
import csv
import re


def _parse_cl_csv_fixed(filepath, profiles_in_order):
    """
    ИСПРАВЛЕННАЯ функция парсинга CL данных с правильной обработкой структуры CSV
    """
    debug_messages = []
    cl_data_for_profiles = {profile: {} for profile in profiles_in_order}

    try:
        # Читаем CSV с правильными параметрами
        df_cl = pd.read_csv(filepath, header=1, encoding='utf-8')
        debug_messages.append(f"DEBUG: _parse_cl_csv_fixed - Успешно прочитан {filepath}")
        debug_messages.append(f"DEBUG: Колонки в файле: {df_cl.columns.tolist()}")

        # Очищаем названия столбцов (длины в дюймах) и создаем маппинг
        column_mapping = {}
        lengths_mm = []

        for col in df_cl.columns[1:]:  # Пропускаем первый столбец с профилями
            # Очищаем название столбца и извлекаем число
            clean_col = str(col).replace(',', '.').strip()
            # Используем регулярное выражение для извлечения числа
            numbers = re.findall(r'\d+(?:\.\d+)?', clean_col)
            if numbers:
                try:
                    inches = float(numbers[0])
                    mm = round(inches * 25.4)  # Конвертируем в мм
                    lengths_mm.append(mm)
                    column_mapping[col] = mm
                    debug_messages.append(f"Столбец '{col}' → {inches}\" → {mm}мм")
                except ValueError:
                    debug_messages.append(f"Пропуск столбца '{col}': не удалось извлечь число")

        debug_messages.append(f"Найдено {len(column_mapping)} колонок с длинами: {sorted(lengths_mm)}")

        # Обрабатываем каждый профиль
        for profile_name in profiles_in_order:
            # Ищем профиль в первом столбце
            profile_row = df_cl[df_cl.iloc[:, 0] == profile_name]
            if not profile_row.empty:
                debug_messages.append(f"Найден профиль '{profile_name}' в строке {profile_row.index[0]}")
                row_data = profile_row.iloc[0]

                values_found = 0
                for col, mm_length in column_mapping.items():
                    if col in row_data.index:
                        val = row_data[col]
                        if pd.notna(val) and str(val).strip():
                            try:
                                # Очищаем значение от лишних символов
                                clean_val = str(val).replace(',', '.').strip()
                                cl_value = float(clean_val)
                                cl_data_for_profiles[profile_name][mm_length] = cl_value
                                values_found += 1
                                debug_messages.append(f"  {profile_name}: длина {mm_length}мм → CL={cl_value}")
                            except ValueError:
                                debug_messages.append(
                                    f"  Пропуск значения '{val}' для {profile_name} (длина {mm_length}мм)")

                debug_messages.append(f"Для профиля '{profile_name}' найдено {values_found} значений CL")
            else:
                debug_messages.append(f"Профиль '{profile_name}' не найден в {filepath}")

        return cl_data_for_profiles, debug_messages

    except Exception as e:
        debug_messages.append(f"Ошибка парсинга {filepath}: {str(e)}")
        return cl_data_for_profiles, debug_messages


def _parse_cl_csv(filepath, profiles_in_order):
    """
    ОРИГИНАЛЬНАЯ функция - заменена на _parse_cl_csv_fixed
    Оставлена для совместимости
    """
    return _parse_cl_csv_fixed(filepath, profiles_in_order)


def _parse_pb_csv(filepath):
    """
    Парсинг данных P0 (базовой мощности) из CSV файлов
    """
    processed_data = []
    debug_messages = []

    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            # Пропускаем первую строку (если есть заголовок)
            next(reader)

            # Читаем строку с диаметрами
            header_row = next(reader)
            diameters = []
            debug_messages.append(f"DEBUG: _parse_pb_csv - Processing file: {filepath}")
            debug_messages.append(f"DEBUG: _parse_pb_csv - Header row: {header_row}")

            for d_str in header_row[1:]:  # Пропускаем первый столбец
                d_clean = d_str.replace(',', '.').strip()
                if d_clean and d_clean != 'Ø':
                    try:
                        diameter = float(d_clean)
                        diameters.append(diameter)
                        debug_messages.append(f"DEBUG: Найден диаметр: {diameter}мм")
                    except ValueError:
                        debug_messages.append(f"DEBUG: _parse_pb_csv - Пропуск нечислового диаметра: {d_str}")

            debug_messages.append(f"DEBUG: _parse_pb_csv - Всего диаметров: {len(diameters)}")

            if not diameters:
                debug_messages.append(f"Warning: Не найдено валидных диаметров в заголовке {filepath}")
                return pd.DataFrame(columns=['d', 'n1', 'Pb']), debug_messages

            # Обрабатываем строки с данными
            for row_idx, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue

                # Извлекаем RPM из первого столбца
                rpm_str = row[0].replace('.', '').replace(',', '').strip()
                try:
                    rpm = float(rpm_str)
                except ValueError:
                    debug_messages.append(
                        f"DEBUG: _parse_pb_csv - Пропуск строки {row_idx} из-за невалидного RPM: {rpm_str}")
                    continue

                # Обрабатываем значения мощности
                power_values = row[1:]
                for i, power_cell in enumerate(power_values):
                    if i < len(diameters) and power_cell.strip():
                        # Очищаем значение мощности
                        power_clean = power_cell.replace('*', '').replace(',', '.').strip()
                        if power_clean and power_clean != '-':
                            try:
                                power_value = float(power_clean)
                                processed_data.append({
                                    'd': diameters[i],
                                    'n1': rpm,
                                    'Pb': power_value
                                })
                                debug_messages.append(
                                    f"DEBUG: Добавлена запись: d={diameters[i]}мм, n1={rpm}об/мин, Pb={power_value}кВт")
                            except ValueError:
                                debug_messages.append(
                                    f"DEBUG: _parse_pb_csv - Пропуск невалидного значения мощности '{power_cell}' в строке {row_idx}, столбце {i}")

        if not processed_data:
            debug_messages.append(f"Warning: Не найдено валидных данных P0 в {filepath}")
            return pd.DataFrame(columns=['d', 'n1', 'Pb']), debug_messages

        df_pb = pd.DataFrame(processed_data)
        debug_messages.append(f"SUCCESS: Успешно извлечено {len(df_pb)} записей P0 из {filepath}")

        # Дополнительная информация для отладки
        debug_messages.append(f"Диапазон диаметров: {df_pb['d'].min()}-{df_pb['d'].max()}мм")
        debug_messages.append(f"Диапазон RPM: {df_pb['n1'].min()}-{df_pb['n1'].max()}об/мин")
        debug_messages.append(f"Диапазон мощности: {df_pb['Pb'].min()}-{df_pb['Pb'].max()}кВт")

        return df_pb, debug_messages

    except Exception as e:
        debug_messages.append(f"ERROR: Ошибка парсинга P0 данных из {filepath}: {e}")
        return pd.DataFrame(columns=['d', 'n1', 'Pb']), debug_messages


def load_all_data():
    """
    ИСПРАВЛЕННАЯ функция загрузки всех данных каталога
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "parsed_tables")

    all_cl_data = {}
    all_pb_data = {}
    all_debug_messages = []

    all_debug_messages.append(f"DEBUG: load_all_data - Функция загрузки данных вызвана. Data directory: {data_dir}")
    all_debug_messages.append(f"DEBUG: Существование папки {data_dir}: {os.path.exists(data_dir)}")

    # === ЗАГРУЗКА ДАННЫХ CL (коэффициенты длины) ===

    # Классические профили
    cl_profiles_classical = ["Z", "A", "B", "C", "D", "E", "20", "25"]
    cl_file_classical = os.path.join(data_dir, "page_026_table_2.csv")
    if os.path.exists(cl_file_classical):
        cl_data_classical, debug_cl_classical = _parse_cl_csv_fixed(cl_file_classical, cl_profiles_classical)
        all_debug_messages.extend(debug_cl_classical)
        for profile, data in cl_data_classical.items():
            if data:  # Только если есть данные
                all_cl_data[profile] = data
                all_debug_messages.append(f"SUCCESS: Загружены CL данные для профиля {profile}: {len(data)} значений")
    else:
        all_debug_messages.append(f"WARNING: Файл {cl_file_classical} не найден")

    # Узкоклиновые профили DIN
    cl_profiles_narrow_wrapped_din = ["SPZ", "SPA", "SPB", "SPC"]
    cl_file_narrow_din = os.path.join(data_dir, "page_054_table_2.csv")
    if os.path.exists(cl_file_narrow_din):
        cl_data_narrow_wrapped_din, debug_cl_narrow_wrapped_din = _parse_cl_csv_fixed(cl_file_narrow_din,
                                                                                      cl_profiles_narrow_wrapped_din)
        all_debug_messages.extend(debug_cl_narrow_wrapped_din)
        for profile, data in cl_data_narrow_wrapped_din.items():
            if data:
                all_cl_data[profile] = data

    # Узкоклиновые профили ARPM
    cl_profiles_narrow_wrapped_arpm = ["3V", "5V", "8V"]
    cl_file_narrow_arpm = os.path.join(data_dir, "page_072_table_2.csv")
    if os.path.exists(cl_file_narrow_arpm):
        cl_data_narrow_wrapped_arpm, debug_cl_narrow_wrapped_arpm = _parse_cl_csv_fixed(cl_file_narrow_arpm,
                                                                                        cl_profiles_narrow_wrapped_arpm)
        all_debug_messages.extend(debug_cl_narrow_wrapped_arpm)
        for profile, data in cl_data_narrow_wrapped_arpm.items():
            if data:
                all_cl_data[profile] = data

    # Классические профили с зубчатыми краями
    cl_profiles_classical_raw_edge = ["AX", "BX", "CX"]
    cl_file_raw_edge = os.path.join(data_dir, "page_080_table_2.csv")
    if os.path.exists(cl_file_raw_edge):
        cl_data_classical_raw_edge, debug_cl_classical_raw_edge = _parse_cl_csv_fixed(cl_file_raw_edge,
                                                                                      cl_profiles_classical_raw_edge)
        all_debug_messages.extend(debug_cl_classical_raw_edge)
        for profile, data in cl_data_classical_raw_edge.items():
            if data:
                all_cl_data[profile] = data

    # Узкоклиновые профили DIN с зубчатыми краями
    cl_profiles_narrow_raw_edge_din = ["XPZ", "XPA", "XPB", "XPC"]
    cl_file_narrow_raw_din = os.path.join(data_dir, "page_088_table_2.csv")
    if os.path.exists(cl_file_narrow_raw_din):
        cl_data_narrow_raw_edge_din, debug_cl_narrow_raw_edge_din = _parse_cl_csv_fixed(cl_file_narrow_raw_din,
                                                                                        cl_profiles_narrow_raw_edge_din)
        all_debug_messages.extend(debug_cl_narrow_raw_edge_din)
        for profile, data in cl_data_narrow_raw_edge_din.items():
            if data:
                all_cl_data[profile] = data

    all_debug_messages.append(f"ИТОГО загружено CL данных для профилей: {list(all_cl_data.keys())}")

    # === ЗАГРУЗКА ДАННЫХ P0 (базовая мощность) ===

    # Маппинг страниц на профили
    pb_page_profile_map = {
        '028': 'Z', '030': 'A', '032': 'A', '034': 'B', '036': 'B', '038': 'C',
        '040': 'C', '042': 'D', '044': 'D', '046': 'E', '048': '20', '050': '25',
        '056': 'SPZ', '058': 'SPZ', '060': 'SPA', '062': 'SPB', '064': 'SPB',
        '066': 'SPC', '068': 'SPC', '070': 'SPC', '074': '3V', '076': '5V',
        '078': '8V', '082': 'AX', '084': 'BX', '086': 'CX', '090': 'XPZ',
        '092': 'XPA', '094': 'XPA', '096': 'XPB', '098': 'XPB', '100': 'XPC',
        '102': 'XPC', '104': 'XPC'
    }

    for page_num_str, profile_name in pb_page_profile_map.items():
        filepath = os.path.join(data_dir, f"page_{page_num_str}_table_1.csv")
        if os.path.exists(filepath):
            df_pb, debug_pb = _parse_pb_csv(filepath)
            all_debug_messages.extend(debug_pb)

            if df_pb is not None and not df_pb.empty:
                # Если для профиля уже есть данные, объединяем их
                if profile_name in all_pb_data:
                    existing_df = all_pb_data[profile_name]
                    combined_df = pd.concat([existing_df, df_pb], ignore_index=True)
                    all_pb_data[profile_name] = combined_df
                    all_debug_messages.append(
                        f"SUCCESS: Добавлены данные P0 для профиля '{profile_name}' (страница {page_num_str}). Всего записей: {len(combined_df)}")
                else:
                    all_pb_data[profile_name] = df_pb
                    all_debug_messages.append(
                        f"SUCCESS: Загружены данные P0 для профиля '{profile_name}' (страница {page_num_str}). Записей: {len(df_pb)}")
            else:
                all_debug_messages.append(
                    f"WARNING: Пустые данные P0 для страницы {page_num_str} (профиль {profile_name})")
        else:
            all_debug_messages.append(f"WARNING: Файл P0 не найден для страницы {page_num_str}: {filepath}")

    all_debug_messages.append(f"ИТОГО загружено P0 данных для профилей: {list(all_pb_data.keys())}")

    # Подробная статистика по профилю C
    if 'C' in all_pb_data:
        df_c = all_pb_data['C']
        all_debug_messages.append(f"ПРОФИЛЬ C: {len(df_c)} записей")
        all_debug_messages.append(f"  Диаметры: {sorted(df_c['d'].unique())}")
        all_debug_messages.append(f"  RPM: {sorted(df_c['n1'].unique())}")
        all_debug_messages.append(f"  Мощность: {df_c['Pb'].min():.3f}-{df_c['Pb'].max():.3f} кВт")

    if 'C' in all_cl_data:
        cl_c = all_cl_data['C']
        all_debug_messages.append(f"ПРОФИЛЬ C CL: {len(cl_c)} значений")
        all_debug_messages.append(f"  Длины: {sorted(cl_c.keys())} мм")
        all_debug_messages.append(f"  CL коэффициенты: {sorted(cl_c.values())}")

    return {
        "CL_DATA": all_cl_data,
        "PB_DATA": all_pb_data,
        "DEBUG_MESSAGES": all_debug_messages
    }


# === КОНСТАНТЫ И СПРАВОЧНЫЕ ДАННЫЕ ===

MIN_PULLEY_DIAMETERS = {
    "Z(0)": 50, "A": 71, "B": 112, "C": 180, "D": 280, "E": 450
}

LOAD_COEFFICIENTS = {
    "спокойная": 1.1, "средняя": 1.2, "тяжелая": 1.4, "ударная": 1.5
}

STANDARD_BELT_LENGTHS = {
    "Z(0)": [360, 381, 395, 410, 420, 425, 435, 450, 457, 470, 480, 500, 530, 560, 600, 630, 670, 710, 750, 800, 850,
             900, 950, 1000, 1060, 1120, 1180, 1250, 1320, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2120, 2240, 2500,
             2800],
    "A": [420, 435, 450, 457, 470, 480, 500, 530, 600, 630, 670, 690, 710, 730, 750, 775, 800, 830, 850, 875, 880, 930,
          940, 950, 965, 970, 1000, 1020, 1030, 1040, 1045, 1060, 1090, 1100, 1120, 1150, 1160, 1180, 1200, 1213, 1220,
          1225, 1240, 1250, 1300, 1320, 1350, 1400, 1430, 1450, 1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 2000,
          2120, 2240, 2360, 2500, 2650, 2800, 3000, 3150, 3350, 3750, 4000, 4500, 5300],
    "B": [530, 630, 670, 710, 750, 800, 840, 887, 900, 930, 937, 950, 987, 1000, 1020, 1040, 1045, 1050, 1060, 1080,
          1100, 1120, 1130, 1150, 1160, 1180, 1200, 1225, 1230, 1250, 1280, 1290, 1320, 1350, 1400, 1420, 1450, 2720,
          2800, 3000, 3070, 3100, 3150, 3350, 3500, 3550, 3750, 3900, 4000, 4250, 4500, 4750, 5000, 5300, 5600, 6000,
          6300, 6500, 6700, 7100, 7250, 7620, 8500, 9000],
    "C": [1180, 1250, 1400, 1450, 1500, 1600, 1650, 1700, 1800, 1900, 2000, 2120, 2240, 2500, 2650, 2700, 2800, 3000,
          3150, 3350, 3550, 3585, 3750, 4000, 4250, 4350, 4500, 4750, 5000, 5300, 5600, 6000, 6300, 6700, 7100, 7500,
          8000, 9000, 9500],
    "D": [1900, 2000, 2120, 2240, 2360, 2500, 2650, 2800, 3000, 3150, 3350, 3475, 3550, 3750, 4000, 4250, 4500, 4750,
          5000, 5300, 5600, 6000, 6300, 6700, 7100, 7500, 8000, 8500, 9000, 9500, 10000, 11200, 11750, 12500],
    "E": [3350, 3750, 4000, 4500, 4750, 5000, 5600, 6000, 6300, 7100, 7500, 8000, 10000, 10600, 11200]
}

STANDARD_PULLEY_DIAMETERS_COMMON = [50, 53, 56, 60, 63, 67, 71, 75, 80, 85, 90, 95, 100, 106, 112, 118, 125, 132, 140,
                                    150, 160, 170, 180, 190, 200, 212, 224, 236, 250, 265, 280, 300, 315, 335, 355, 375,
                                    400, 425, 450, 475, 500, 530, 560, 600, 620, 630, 670, 710, 750, 800, 850, 900, 950,
                                    1000]

STANDARD_PULLEY_DIAMETERS = {
    "Z(0)": STANDARD_PULLEY_DIAMETERS_COMMON,
    "A": STANDARD_PULLEY_DIAMETERS_COMMON,
    "B": STANDARD_PULLEY_DIAMETERS_COMMON,
    "C": STANDARD_PULLEY_DIAMETERS_COMMON,
    "D": STANDARD_PULLEY_DIAMETERS_COMMON,
    "E": STANDARD_PULLEY_DIAMETERS_COMMON
}

CALPHA_DATA = {
    (175, 181): 1.00, (165, 175): 0.98, (155, 165): 0.95, (145, 155): 0.92,
    (135, 145): 0.89, (125, 135): 0.86, (115, 125): 0.82, (105, 115): 0.78,
    (95, 105): 0.74, (0, 95): 0.69
}

CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}

MATERIAL_P0_CORRECTION_FACTORS = {
    "Стандартный (CR/Полиэстер)": 1.0,
    "Высокоэффективный (EPDM/Полиэстер)": 1.1,
    "Высокопрочный (CR/Арамид)": 1.2,
    "Премиум (TPU/Арамид или Сталь)": 1.35
}
