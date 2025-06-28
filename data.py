# data.py (Финальная, рабочая версия)

import pandas as pd
import os
import csv


def _parse_cl_csv(filepath, profiles_in_order, data_dir="parsed_data"):
    cl_data_for_profiles = {profile: {} for profile in profiles_in_order}
    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            # Skip header rows until we find the INCHES row
            header_found = False
            lengths_inches = []
            for _ in range(10): # Limit rows to check to avoid infinite loop
                row = next(reader)
                if "INCHES" in row[0] or "INCHES" in row[1]: # Check both first columns
                    lengths_inches = [float(l.replace('½', '.5').replace('¼', '.25').replace('¾', '.75').replace(',', '.').strip()) for l in row[1:] if l.strip()]
                    header_found = True
                    break
            if not header_found:
                print(f"Warning: Could not find 'INCHES' header in {filepath}. Skipping CL data for this file.")
                return {}

            # Convert lengths to mm
            lengths_mm = [l * 25.4 for l in lengths_inches]

            for row in reader:
                if not row or not row[0].strip():
                    continue
                profile_name = row[0].strip().replace('"', '')
                if profile_name in profiles_in_order:
                    cl_values = [float(val.replace(',', '.').strip()) for val in row[1:] if val.strip()]
                    for i, cl_val in enumerate(cl_values):
                        if i < len(lengths_mm):
                            cl_data_for_profiles[profile_name][round(lengths_mm[i])] = cl_val
        print(f"Successfully parsed CL data from {filepath}.")
        return cl_data_for_profiles
    except Exception as e:
        print(f"Error parsing CL data from {filepath}: {e}")
        return {}

def _parse_pb_csv(filepath):
    processed_data = []
    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader) # Skip the first row

            header_row = next(reader)
            diameters = []
            print(f"DEBUG: _parse_pb_csv - Processing file: {filepath}")
            print(f"DEBUG: _parse_pb_csv - Header row: {header_row}")
            for d_str in header_row[1:]:
                d_clean = d_str.replace(',', '.').strip()
                if d_clean and d_clean != 'Ø':
                    try:
                        diameters.append(float(d_clean))
                    except ValueError:
                        print(f"DEBUG: _parse_pb_csv - Skipping non-numeric diameter: {d_str}")
                        pass
            print(f"DEBUG: _parse_pb_csv - Parsed diameters: {diameters}")
            
            if not diameters:
                print(f"Warning: No valid diameters found in header of {filepath}. Skipping Pb data for this file.")
                return None

            for row_idx, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue

                rpm_str = row[0].replace('.', '').strip()
                try:
                    rpm = float(rpm_str)
                except ValueError:
                    print(f"DEBUG: _parse_pb_csv - Skipping row {row_idx} due to invalid RPM: {rpm_str}")
                    continue

                power_values = row[1:]
                for i, power_cell in enumerate(power_values):
                    if i < len(diameters) and power_cell.strip():
                        power_clean = power_cell.replace('*', '').replace(',', '.').strip()
                        if power_clean:
                            try:
                                processed_data.append({
                                    'd': diameters[i],
                                    'n1': rpm,
                                    'Pb': float(power_clean)
                                })
                            except ValueError:
                                print(f"DEBUG: _parse_pb_csv - Skipping invalid power value '{power_cell}' at row {row_idx}, col {i}")
                                pass
            
            if not processed_data:
                print(f"Warning: No valid Pb data rows found in {filepath}. Returning empty DataFrame.")
                return pd.DataFrame(columns=['d', 'n1', 'Pb'])

        df_pb = pd.DataFrame(processed_data)
        print(f"Successfully parsed Pb data from {filepath}. Extracted {len(df_pb)} rows.")
        return df_pb

    except Exception as e:
        print(f"Error parsing Pb data from {filepath}: {e}")
        return None


def load_all_data(data_dir="parsed_data"):
    print("DEBUG: load_all_data - Функция загрузки данных вызвана.")
    all_cl_data = {}
    all_pb_data = {}

    # Load CL data for Classical Wrapped Belts (Z, A, B, C, D, E, 20, 25)
    cl_profiles_classical = ["Z", "A", "B", "C", "D", "E", "20", "25"]
    cl_data_classical = _parse_cl_csv(os.path.join(data_dir, "page_026_table_2.csv"), cl_profiles_classical)
    for profile, data in cl_data_classical.items():
        all_cl_data[profile] = data

    # Load CL data for Narrow Wrapped V-belts DIN (SPZ, SPA, SPB, SPC)
    cl_profiles_narrow_wrapped_din = ["SPZ", "SPA", "SPB", "SPC"]
    cl_data_narrow_wrapped_din = _parse_cl_csv(os.path.join(data_dir, "page_054_table_2.csv"), cl_profiles_narrow_wrapped_din)
    for profile, data in cl_data_narrow_wrapped_din.items():
        all_cl_data[profile] = data

    # Load CL data for Narrow Wrapped V-belts ARPM (3V, 5V, 8V)
    cl_profiles_narrow_wrapped_arpm = ["3V", "5V", "8V"]
    cl_data_narrow_wrapped_arpm = _parse_cl_csv(os.path.join(data_dir, "page_072_table_2.csv"), cl_profiles_narrow_wrapped_arpm)
    for profile, data in cl_data_narrow_wrapped_arpm.items():
        all_cl_data[profile] = data

    # Load CL data for Classical Raw Edge V-belts (AX, BX, CX)
    cl_profiles_classical_raw_edge = ["AX", "BX", "CX"]
    cl_data_classical_raw_edge = _parse_cl_csv(os.path.join(data_dir, "page_080_table_2.csv"), cl_profiles_classical_raw_edge)
    for profile, data in cl_data_classical_raw_edge.items():
        all_cl_data[profile] = data

    # Load CL data for Narrow Raw Edge V-belts DIN (XPZ, XPA, XPB, XPC)
    cl_profiles_narrow_raw_edge_din = ["XPZ", "XPA", "XPB", "XPC"]
    cl_data_narrow_raw_edge_din = _parse_cl_csv(os.path.join(data_dir, "page_088_table_2.csv"), cl_profiles_narrow_raw_edge_din)
    for profile, data in cl_data_narrow_raw_edge_din.items():
        all_cl_data[profile] = data

    # Load Pb data
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
            df_pb = _parse_pb_csv(filepath)
            if df_pb is not None and not df_pb.empty:
                all_pb_data[profile_name] = df_pb
        else:
            print(f"Warning: Pb data file not found for page {page_num_str} at {filepath}. Skipping.")

    return {
        "CL_DATA": all_cl_data,
        "PB_DATA": all_pb_data
    }

# --- ВОССТАНОВЛЕННЫЕ СЛОВАРИ ДАННЫХ ---
MIN_PULLEY_DIAMETERS = {"Z(0)": 50, "A": 71, "B": 112, "C": 180, "D": 280, "E": 450}
LOAD_COEFFICIENTS = {"спокойная": 1.1, "средняя": 1.2, "тяжелая": 1.4, "ударная": 1.5}
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
STANDARD_PULLEY_DIAMETERS = {"Z(0)": STANDARD_PULLEY_DIAMETERS_COMMON, "A": STANDARD_PULLEY_DIAMETERS_COMMON,
                             "B": STANDARD_PULLEY_DIAMETERS_COMMON, "C": STANDARD_PULLEY_DIAMETERS_COMMON,
                             "D": STANDARD_PULLEY_DIAMETERS_COMMON, "E": STANDARD_PULLEY_DIAMETERS_COMMON}



CALPHA_DATA = {(175, 181): 1.00, (165, 175): 0.98, (155, 165): 0.95, (145, 155): 0.92, (135, 145): 0.89, (125, 135): 0.86, (115, 125): 0.82, (105, 115): 0.78, (95, 105): 0.74, (0, 95): 0.69}
CZ_DATA = {1: 1.00, 2: 1.15, 3: 1.25, 4: 1.30, 5: 1.35}
MATERIAL_P0_CORRECTION_FACTORS = {"Стандартный (CR/Полиэстер)": 1.0, "Высокоэффективный (EPDM/Полиэстер)": 1.1,
                                  "Высокопрочный (CR/Арамид)": 1.2, "Премиум (TPU/Арамид или Сталь)": 1.35}