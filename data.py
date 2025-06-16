# data.py (Финальная версия, адаптированная под ваш CSV)

import pandas as pd
import os


def load_power_data(profile, data_dir="parsed_data"):
    """
    Загружает "сырые" данные, извлеченные через find_tables(), и преобразует их
    в готовый для использования формат ("длинный" DataFrame).
    """
    filename = f"power_data_{profile}_Pb_findtables.csv"
    filepath = os.path.join(data_dir, filename)

    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден. Не могу загрузить точные данные.")
        return None

    try:
        df_raw = pd.read_csv(filepath, header=None)

        # Первая строка - это заголовки. Ищем первую числовую ячейку для старта.
        header_row = df_raw.iloc[0].tolist()
        first_num_idx = -1
        for i, item in enumerate(header_row):
            if item and str(item).replace(',', '.').replace('.', '', 1).isdigit():
                first_num_idx = i
                break

        if first_num_idx == -1: return None  # Не нашли заголовки

        diameters = [float(str(d).replace(',', '.')) for d in header_row[first_num_idx:] if d]

        processed_data = []
        # Проходим по строкам данных (пропуская заголовок)
        for index, row in df_raw.iloc[1:].iterrows():
            rpm_str = str(row.iloc[0]).replace('.', '')  # '1.000' -> '1000'
            if not rpm_str or not rpm_str.isdigit(): continue
            rpm = float(rpm_str)

            power_values = row.iloc[first_num_idx:].tolist()
            for i, power_cell in enumerate(power_values):
                if i < len(diameters) and power_cell and isinstance(power_cell, str):
                    power_clean = power_cell.replace('*', '').replace(',', '.').strip()
                    if power_clean and power_clean.replace('.', '', 1).isdigit():
                        processed_data.append({'d': diameters[i], 'n1': rpm, 'Pb': float(power_clean)})

        df_long = pd.DataFrame(processed_data)
        print(f"Успешно загружены и преобразованы данные для профиля {profile} из {filepath}")
        return df_long
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при чтении файла {filepath}: {e}")
        return None


# --- Остальные данные (словари) ---
MIN_PULLEY_DIAMETERS = {"C": 180, "A": 71, "B": 112, "D": 280}
LOAD_COEFFICIENTS = {"спокойная": 1.0, "средняя": 1.1, "тяжелая": 1.2, "ударная": 1.3}
STANDARD_BELT_LENGTHS = {"C": [3000, 3150], "A": [], "B": []}  # Упрощено для примера
STANDARD_PULLEY_DIAMETERS = {"C": [180, 190, 200, 212, 224, 236, 250], "A": [], "B": []}
P0_DATA_BY_V_RANGES = {"A": [], "B": [], "C": []}
P0_VALUES = {"A": [], "B": [], "C": []}
CL_DATA = {"C": {}, "A": {}, "B": {}}
CALPHA_DATA = {(0, 120): 0.90, (120, 150): 0.95, (150, 170): 0.98, (170, 181): 1.00}
CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}
MATERIAL_P0_CORRECTION_FACTORS = {"Стандартный (CR/Полиэстер)": 1.0}