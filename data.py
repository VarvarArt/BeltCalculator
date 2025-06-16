# data.py (Финальная, рабочая версия)

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
        print(f"Файл {filepath} не найден.")
        return None

    try:
        # Указываем, что разделитель - запятая, а десятичный знак - тоже запятая.
        # header=1 говорит читать заголовки из второй строки (индекс 1).
        df_wide = pd.read_csv(filepath, header=1, sep=',', decimal=',')

        # Переименовываем первый столбец, чтобы к нему было удобно обращаться
        df_wide.rename(columns={df_wide.columns[0]: 'n1'}, inplace=True)

        # Очищаем столбец с оборотами от точек (для '1.000')
        df_wide['n1'] = df_wide['n1'].astype(str).str.replace('.', '').astype(float)

        # Используем pd.melt для "разворачивания" широкой таблицы в длинную.
        # Это стандартный и очень надежный способ.
        df_long = df_wide.melt(
            id_vars=['n1'],
            var_name='d',
            value_name='Pb'
        )

        # Очищаем данные от мусора
        df_long.dropna(subset=['Pb'], inplace=True)  # Удаляем строки без значения мощности
        df_long['d'] = pd.to_numeric(df_long['d'])
        df_long['Pb'] = pd.to_numeric(df_long['Pb'].astype(str).str.replace('*', ''))

        print(f"Успешно загружены и преобразованы данные для профиля {profile}.")
        return df_long

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при чтении файла {filepath}: {e}")
        return None


# --- ВОССТАНОВЛЕННЫЕ СЛОВАРИ ДАННЫХ ---
MIN_PULLEY_DIAMETERS = {"Z(0)": 50, "A": 71, "B": 112, "C": 180, "D": 280, "E": 450}
LOAD_COEFFICIENTS = {"спокойная": 1.0, "средняя": 1.1, "тяжелая": 1.2, "ударная": 1.3}
STANDARD_BELT_LENGTHS = {
    "Z(0)": [1000], "A": [1000], "B": [2000],
    "C": [1180, 1250, 1400, 1450, 1500, 1600, 1650, 1700, 1800, 1900, 2000, 2120, 2240, 2500, 2650, 2700, 2800, 3000,
          3150, 3350, 3550, 3585, 3750, 4000, 4250, 4350, 4500, 4750, 5000, 5300, 5600, 6000, 6300, 6700, 7100, 7500,
          8000, 9000, 9500],
    "D": [3000], "E": [5000]
}
STANDARD_PULLEY_DIAMETERS_COMMON = [50, 53, 56, 60, 63, 67, 71, 75, 80, 85, 90, 95, 100, 106, 112, 118, 125, 132, 140,
                                    150, 160, 170, 180, 190, 200, 212, 224, 236, 250, 265, 280, 300, 315, 335, 355, 375,
                                    400, 425, 450, 475, 500, 530, 560, 600, 620, 630, 670, 710, 750, 800, 850, 900, 950,
                                    1000]
STANDARD_PULLEY_DIAMETERS = {"Z(0)": STANDARD_PULLEY_DIAMETERS_COMMON, "A": STANDARD_PULLEY_DIAMETERS_COMMON,
                             "B": STANDARD_PULLEY_DIAMETERS_COMMON, "C": STANDARD_PULLEY_DIAMETERS_COMMON,
                             "D": STANDARD_PULLEY_DIAMETERS_COMMON, "E": STANDARD_PULLEY_DIAMETERS_COMMON}
P0_DATA_BY_V_RANGES = {"Z(0)": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))],
                       "A": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))],
                       "B": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))],
                       "C": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))],
                       "D": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))],
                       "E": [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, float('inf'))]}
P0_VALUES = {"Z(0)": [0.20, 0.50, 0.90, 1.30, 1.60, 2.00], "A": [0.50, 0.95, 1.60, 2.15, 2.60, 3.00],
             "B": [0.85, 1.40, 2.30, 3.10, 3.80, 4.50], "C": [1.20, 2.00, 3.00, 4.00, 4.80, 5.50],
             "D": [2.00, 3.50, 5.20, 6.50, 7.40, 8.50], "E": [3.00, 5.00, 7.00, 8.80, 10.0, 11.5]}
CL_DATA = {"Z(0)": {}, "A": {}, "B": {}, "C": {}, "D": {}, "E": {}}
CALPHA_DATA = {(0, 120): 0.90, (120, 150): 0.95, (150, 170): 0.98, (170, 181): 1.00}
CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}
MATERIAL_P0_CORRECTION_FACTORS = {"Стандартный (CR/Полиэстер)": 1.0, "Высокоэффективный (EPDM/Полиэстер)": 1.1,
                                  "Высокопрочный (CR/Арамид)": 1.2, "Премиум (TPU/Арамид или Сталь)": 1.35}