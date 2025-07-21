import pandas as pd
import os
import csv
import re

def _parse_cl_csv_fixed(filepath: str, profiles_in_order: list[str]) -> tuple[dict[str, dict[int, float]], list[str]]:
    debug_messages: list[str] = []
    cl_data_for_profiles: dict[str, dict[int, float]] = {profile: {} for profile in profiles_in_order}
    try:
        df_cl = pd.read_csv(filepath, header=1, encoding='utf-8')
        debug_messages.append(f"DEBUG: Прочитан {os.path.basename(filepath)}; колонки: {df_cl.columns.tolist()}")
        column_mapping: dict[str, int] = {}
        for col in df_cl.columns[1:]:
            clean_col = str(col).replace(',', '.').strip()
            nums = re.findall(r'\d+(?:\.\d+)?', clean_col)
            if nums:
                inches = float(nums[0])
                mm = round(inches * 25.4)
                column_mapping[col] = mm
                debug_messages.append(f"Колонка '{col}' → {mm} мм")
        for profile in profiles_in_order:
            row_idx = df_cl.index[df_cl.iloc[:, 0] == profile]
            if len(row_idx) == 0:
                debug_messages.append(f"Профиль '{profile}' не найден")
                continue
            row = df_cl.iloc[row_idx[0]]
            for col, mm in column_mapping.items():
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    cl = float(str(val).replace(',', '.'))
                    cl_data_for_profiles[profile][mm] = cl
                    debug_messages.append(f"{profile}: {mm} мм → CL={cl}")
        return cl_data_for_profiles, debug_messages
    except Exception as e:
        debug_messages.append(f"Ошибка парсинга {os.path.basename(filepath)}: {e}")
        return cl_data_for_profiles, debug_messages

def _parse_pb_csv(filepath: str) -> tuple[pd.DataFrame, list[str]]:
    data: list[dict[str, float]] = []
    debug_messages: list[str] = []
    try:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            header = next(reader)
            diameters = [float(d.replace(',', '.')) for d in header[1:] if d.strip() and d != 'Ø']
            debug_messages.append(f"DEBUG: Диаметры {os.path.basename(filepath)}: {diameters}")
            for row in reader:
                if not row or not row[0].strip(): continue
                rpm = float(row[0].replace(',', '').strip())
                for i, cell in enumerate(row[1:]):
                    if i < len(diameters) and cell.strip() and cell.strip() != '-':
                        pb = float(cell.replace(',', '.').replace('*', '').strip())
                        data.append({'d': diameters[i], 'n1': rpm, 'Pb': pb})
                        debug_messages.append(f"Добавлена запись d={diameters[i]}, n1={rpm}, Pb={pb}")
        df = pd.DataFrame(data)
        debug_messages.append(f"SUCCESS: Извлечено {len(df)} записей из {os.path.basename(filepath)}")
        return df, debug_messages
    except Exception as e:
        debug_messages.append(f"ERROR: Парсинг {os.path.basename(filepath)}: {e}")
        return pd.DataFrame(columns=['d', 'n1', 'Pb']), debug_messages

def load_all_data() -> dict:
    base = os.path.dirname(__file__)
    data_dir = os.path.join(base, "parsed_tables")
    CL_DATA: dict[str, dict[int, float]] = {}
    PB_DATA: dict[str, pd.DataFrame] = {}
    DEBUG: list[str] = []
    profiles_cl = ["Z", "A", "B", "C", "D", "E"]
    filepath_cl = os.path.join(data_dir, "page_026_table_2.csv")
    if os.path.exists(filepath_cl):
        cl_data, dbg = _parse_cl_csv_fixed(filepath_cl, profiles_cl)
        DEBUG += dbg
        for prof, vals in cl_data.items():
            if vals:
                CL_DATA[prof] = vals
                DEBUG.append(f"Loaded CL {prof}: {len(vals)} values")
    else:
        DEBUG.append(f"CL файл не найден: {filepath_cl}")
    page_map = {'028':'Z','030':'A','032':'A','034':'B','036':'B','038':'C','040':'C','042':'D','044':'D','046':'E'}
    for page, prof in page_map.items():
        path_pb = os.path.join(data_dir, f"page_{page}_table_1.csv")
        if os.path.exists(path_pb):
            df, dbg = _parse_pb_csv(path_pb)
            DEBUG += dbg
            if not df.empty:
                if prof in PB_DATA:
                    PB_DATA[prof] = pd.concat([PB_DATA[prof], df], ignore_index=True)
                else:
                    PB_DATA[prof] = df
                DEBUG.append(f"Loaded P0 {prof}: {len(PB_DATA[prof])} records from {page}")
        else:
            DEBUG.append(f"P0 файл не найден: {path_pb}")
    return {"CL_DATA": CL_DATA, "PB_DATA": PB_DATA, "DEBUG": DEBUG}

LOAD_COEFFICIENTS = {
    "спокойная": 1.1, "средняя": 1.2, "тяжелая": 1.4, "ударная": 1.5
}
MIN_PULLEY_DIAMETERS = {"Z":50,"A":71,"B":112,"C":180,"D":280,"E":450}
CALPHA_DATA = {
    (175,181):1.00,(165,175):0.98,(155,165):0.95,(145,155):0.92,
    (135,145):0.89,(125,135):0.86,(115,125):0.82,(105,115):0.78,(0,95):0.69
}
CZ_DATA = {1:1.00,2:1.15,3:1.25,4:1.30,5:1.35}
MATERIAL_P0_CORRECTION_FACTORS = {
    "Стандартный (CR/Полиэстер)":1.0,
    "Высокоэффективный (EPDM/Полиэстер)":1.1,
    "Высокопрочный (CR/Арамид)":1.2,
    "Премиум (TPU/Арамид или Сталь)":1.35
}