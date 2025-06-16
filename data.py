# data.py (Финальная версия, адаптированная под find_tables)

import pandas as pd
import os


# --- НОВАЯ, АДАПТИРОВАННАЯ ФУНКЦИЯ ЗАГРУЗКИ ---
def load_power_data(profile, data_dir="parsed_data"):
    """
    Загружает данные, извлеченные через find_tables(), и преобразует их
    в "длинный" формат (d, n1, Pb).
    """
    filename = f"power_data_{profile}_Pb_findtables.csv"
    filepath = os.path.join(data_dir, filename)

    if not os.path.exists(filepath):
        return None

    try:
        # Читаем CSV без заголовка, т.к. он у нас "в данных"
        df_raw = pd.read_csv(filepath, header=None)

        # Извлекаем заголовки-диаметры из первой строки (пропуская первую ячейку)
        diameters = [float(str(d).replace(',', '.')) for d in df_raw.iloc[0, 1:].tolist() if
                     str(d).replace(',', '.').replace('.', '', 1).isdigit()]

        processed_data = []
        # Проходим по остальным строкам (пропуская первую строку с заголовками)
        for index, row in df_raw.iloc[1:].iterrows():
            # Извлекаем обороты из первого столбца
            rpm_str = str(row.iloc[0]).replace('.', '')  # Убираем точки-разделители тысяч
            if not rpm_str.isdigit(): continue
            rpm = float(rpm_str)

            # Извлекаем значения мощности
            power_values = row.iloc[1:].tolist()

            for i, power_str in enumerate(power_values):
                if i < len(diameters) and isinstance(power_str, str) and power_str:
                    # Убираем звездочки и заменяем запятые
                    power_clean = str(power_str).replace('*', '').replace(',', '.')
                    if power_clean.replace('.', '', 1).isdigit():
                        processed_data.append({
                            'd': diameters[i],
                            'n1': rpm,
                            'Pb': float(power_clean)
                        })

        df_long = pd.DataFrame(processed_data)
        print(f"Успешно загружены и преобразованы данные для профиля {profile} из файла {filepath}")
        return df_long

    except Exception as e:
        print(f"Ошибка при чтении и преобразовании файла {filepath}: {e}")
        return None


# --- Остальные данные (словари) остаются без изменений ---

MIN_PULLEY_DIAMETERS = {"Z(0)": 50, "A": 71, "B": 112, "C": 180, "D": 280, "E": 450}
LOAD_COEFFICIENTS = {"спокойная": 1.0, "средняя": 1.1, "тяжелая": 1.2, "ударная": 1.3}
STANDARD_BELT_LENGTHS = {
    "C": [1180, 1250, 1400, 1450, 1500, 1600, 1650, 1700, 1800, 1900, 2000, 2120, 2240, 2500, 2650, 2700, 2800, 3000,
          3150, 3350, 3550, 3585, 3750, 4000, 4250, 4350, 4500, 4750, 5000, 5300, 5600, 6000, 6300, 6700, 7100, 7500,
          8000, 9000, 9500]
}
STANDARD_PULLEY_DIAMETERS_COMMON = [180, 190, 200, 212, 236, 265, 300, 335, 375, 400, 425, 450]  # Пример для C
STANDARD_PULLEY_DIAMETERS = {"C": STANDARD_PULLEY_DIAMETERS_COMMON}
P0_DATA_BY_V_RANGES = {"C": []}
P0_VALUES = {"C": []}
CL_DATA = {"C": {}}  # Упрощенные данные, т.к. мы пока не парсим CL
CALPHA_DATA = {(0, 120): 0.90, (120, 150): 0.95, (150, 170): 0.98, (170, 181): 1.00}
CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}
MATERIAL_P0_CORRECTION_FACTORS = {"Стандартный (CR/Полиэстер)": 1.0, "Высокоэффективный (EPDM/Полиэстер)": 1.1,
                                  "Высокопрочный (CR/Арамид)": 1.2, "Премиум (TPU/Арамид или Сталь)": 1.35}