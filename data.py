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
        df_cl = pd.read_csv(filepath, header=1, encoding='utf-8')
        debug_messages.append(f"DEBUG: _parse_cl_csv_fixed - Успешно прочитан {filepath}")
        debug_messages.append(f"DEBUG: Колонки в файле: {df_cl.columns.tolist()}")

        column_mapping = {}
        for col in df_cl.columns[1:]:
            clean_col = str(col).replace(',', '.').strip()
            numbers = re.findall(r'\d+(?:\.\d+)?', clean_col)
            if numbers:
                inches = float(numbers[0])
                mm = round(inches * 25.4)
                column_mapping[col] = mm
                debug_messages.append(f"  Столбец '{col}' → {inches}\" → {mm}мм")

        for profile_name in profiles_in_order:
            profile_row = df_cl[df_cl.iloc[:, 0] == profile_name]
            if not profile_row.empty:
                row = profile_row.iloc[0]
                for col, mm_length in column_mapping.items():
                    val = row.get(col, "")
                    if pd.notna(val) and str(val).strip():
                        clean_val = str(val).replace(',', '.').strip()
                        cl_value = float(clean_val)
                        cl_data_for_profiles[profile_name][mm_length] = cl_value
                        debug_messages.append(f"  {profile_name}: длина {mm_length}мм → CL={cl_value}")
            else:
                debug_messages.append(f"Профиль '{profile_name}' не найден в {filepath}")

        return cl_data_for_profiles, debug_messages

    except Exception as e:
        debug_messages.append(f"Ошибка парсинга {filepath}: {e}")
        return cl_data_for_profiles, debug_messages


def _parse_pb_csv(filepath):
    """
    Парсинг данных P0 (базовой мощности) из CSV файлов
    """
    processed_data = []
    debug_messages = []

    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            header_row = next(reader)
            diameters = []
            debug_messages.append(f"DEBUG: _parse_pb_csv - {filepath}")
            for d_str in header_row[1:]:
                d_clean = d_str.replace(',', '.').strip()
                if d_clean and d_clean != 'Ø':
                    diameters.append(float(d_clean))
                    debug_messages.append(f"  Диаметр: {d_clean}мм")

            for row_idx, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue
                rpm = float(row[0].replace(',', '').strip())
                for i, cell in enumerate(row[1:]):
                    if i < len(diameters) and cell.strip() and cell.strip() != '-':
                        power = float(cell.replace(',', '.').replace('*', '').strip())
                        processed_data.append({
                            'd': diameters[i],
                            'n1': rpm,
                            'Pb': power
                        })
                        debug_messages.append(
                            f"  Запись: d={diameters[i]}мм, n1={rpm}, Pb={power}кВт")

        df_pb = pd.DataFrame(processed_data)
        debug_messages.append(f"SUCCESS: извлечено {len(df_pb)} записей P0")
        return df_pb, debug_messages

    except Exception as e:
        debug_messages.append(f"ERROR: парсинг {filepath}: {e}")
        return pd.DataFrame(columns=['d', 'n1', 'Pb']), debug_messages


def load_all_data():
    """
    Загрузка всех данных каталога
    """
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "parsed_tables")
    all_cl = {}
    all_pb = {}
    debug = []

    # CL — классические профили
    cl_profiles = ["Z", "A", "B", "C", "D", "E"]
    path_cl = os.path.join(data_dir, "page_026_table_2.csv")
    if os.path.exists(path_cl):
        cl_data, dbg = _parse_cl_csv_fixed(path_cl, cl_profiles)
        debug += dbg
        for prof, vals in cl_data.items():
            if vals:
                all_cl[prof] = vals
                debug.append(f"Loaded CL {prof}: {len(vals)}")
    else:
        debug.append(f"CL file missing: {path_cl}")

    # P0 — страницы → профили
    page_map = {
        '028': 'Z', '030': 'A', '032': 'A', '034': 'B', '036': 'B',
        '038': 'C', '040': 'C', '042': 'D', '044': 'D', '046': 'E'
    }
    for p, prof in page_map.items():
        file_p = os.path.join(data_dir, f"page_{p}_table_1.csv")
        if os.path.exists(file_p):
            df_pb, dbg = _parse_pb_csv(file_p)
            debug += dbg
            if not df_pb.empty:
                if prof in all_pb:
                    all_pb[prof] = pd.concat([all_pb[prof], df_pb], ignore_index=True)
                else:
                    all_pb[prof] = df_pb
                debug.append(f"Loaded P0 {prof}: {len(all_pb[prof])} records")
        else:
            debug.append(f"P0 file missing: {file_p}")

    # Отладка профиля C
    if 'C' in all_pb:
        df = all_pb['C']
        debug.append(f"Profile C P0 records: {len(df)}")
        debug.append(f"  Diameters: {sorted(df['d'].unique())}")
        debug.append(f"  RPM: {sorted(df['n1'].unique())}")

    if 'C' in all_cl:
        debug.append(f"Profile C CL values: {sorted(all_cl['C'].keys())}")

    return {"CL_DATA": all_cl, "PB_DATA": all_pb, "DEBUG": debug}


# Константы
LOAD_COEFFICIENTS = {
    "спокойная": 1.1, "средняя": 1.2, "тяжелая": 1.4, "ударная": 1.5
}
MIN_PULLEY_DIAMETERS = {"Z": 50, "A": 71, "B": 112, "C": 180, "D": 280, "E": 450}
CALPHA_DATA = {(175, 181): 1.00, (165, 175): 0.98, (155, 165): 0.95, (145, 155): 0.92,
               (135, 145): 0.89, (125, 135): 0.86, (115, 125): 0.82, (105, 115): 0.78,
               (0, 95): 0.69}
CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}
