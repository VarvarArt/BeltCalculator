# calculations.py

import math
import pandas as pd
from scipy.interpolate import griddata
from data import (
    LOAD_COEFFICIENTS, P0_DATA_BY_V_RANGES, P0_VALUES, CL_DATA, CALPHA_DATA, CZ_DATA, MIN_PULLEY_DIAMETERS
)

def calculate_transmission_ratio(n1, n2):
    if n2 == 0: raise ValueError("Частота вращения ведомого вала (n2) не может быть равна нулю.")
    return n1 / n2

def calculate_design_power(nominal_power, load_type_choice, load_coefficients_data=LOAD_COEFFICIENTS):
    load_mapping = {'1': "спокойная", '2': "средняя", '3': "тяжелая", '4': "ударная"}
    load_type = load_mapping.get(load_type_choice)
    if load_type is None: raise ValueError("Неизвестный тип нагрузки.")
    kp_value = load_coefficients_data.get(load_type, 1.0)
    return nominal_power * kp_value, kp_value

def determine_belt_section(P_design, n1_rpm):
    if P_design <= 0.75: return 'A'
    elif P_design <= 7.5: return 'B'
    elif P_design <= 30: return 'C'
    elif P_design <= 75: return 'D'
    elif P_design > 75: return 'E'
    return 'Не определено'

def get_min_pulley_diameter(belt_section, min_pulley_diameters_data=MIN_PULLEY_DIAMETERS):
    return min_pulley_diameters_data.get(belt_section)

def find_nearest_standard_value(value, standard_list, greater_or_equal=True):
    if not standard_list: return None
    if greater_or_equal:
        filtered_list = [s_val for s_val in standard_list if s_val >= value]
        if not filtered_list: return max(standard_list)
        return min(filtered_list)
    else:
        return min(standard_list, key=lambda x: abs(x - value))

def calculate_belt_length(d1, d2, a):
    if a == 0: raise ValueError("Межосевое расстояние не может быть равно нулю.")
    return 2 * a + 0.5 * math.pi * (d1 + d2) + (d2 - d1) ** 2 / (4 * a)

def calculate_actual_center_distance(lp, d1, d2):
    w = 0.5 * math.pi * (d1 + d2)
    y = (d2 - d1) ** 2
    discriminant = (lp - w) ** 2 - 2 * y
    if discriminant < 0: raise ValueError("Невозможно рассчитать: длина ремня слишком мала.")
    return 0.25 * ((lp - w) + math.sqrt(discriminant))

def get_actual_transmission_ratio(d1, d2, slip_coefficient=0.01):
    if d1 == 0: raise ValueError("Диаметр ведущего шкива (d1) не может быть равен нулю.")
    return d2 / (d1 * (1 - slip_coefficient))

def calculate_belt_speed(d1, n1):
    return (math.pi * d1 * n1) / 60000

def get_p0_value(belt_section, V, material_correction_factor=1.0, p0_ranges_data=P0_DATA_BY_V_RANGES, p0_values_data=P0_VALUES):
    if belt_section not in p0_ranges_data or belt_section not in p0_values_data: return 0.0
    speed_ranges = p0_ranges_data[belt_section]
    p0_values_for_section = p0_values_data[belt_section]
    p0_base = 0.0
    if V <= speed_ranges[0][0]: p0_base = p0_values_for_section[0]
    elif V > speed_ranges[-1][1]: p0_base = p0_values_for_section[-1]
    else:
        for i, (min_v, max_v) in enumerate(speed_ranges):
            if min_v < V <= max_v: p0_base = p0_values_for_section[i]; break
    return p0_base * material_correction_factor

def get_cl_value(belt_section, lp, cl_data=CL_DATA):
    if belt_section not in cl_data or not cl_data[belt_section]: return 1.0
    available_lengths = sorted(cl_data[belt_section].keys())
    if not available_lengths: return 1.0
    nearest_lp = min(available_lengths, key=lambda x: abs(x - lp))
    return cl_data[belt_section][nearest_lp]

def calculate_angle_of_wrap(d1, d2, a):
    if a == 0: raise ValueError("Межосевое расстояние не может быть равно нулю.")
    argument_for_asin = (d2 - d1) / (2 * a)
    if argument_for_asin > 1: argument_for_asin = 1
    elif argument_for_asin < -1: argument_for_asin = -1
    return math.degrees(math.pi - 2 * math.asin(argument_for_asin))

def get_calpha_value(alpha1_deg, calpha_data=CALPHA_DATA):
    sorted_ranges = sorted(calpha_data.keys())
    for min_alpha, max_alpha in sorted_ranges:
        if min_alpha < alpha1_deg <= max_alpha: return calpha_data[(min_alpha, max_alpha)]
    if alpha1_deg <= sorted_ranges[0][0]: return calpha_data[sorted_ranges[0]]
    elif alpha1_deg > sorted_ranges[-1][1]: return calpha_data[sorted_ranges[-1]]
    return 0.90

def get_cz_value(z, cz_data=CZ_DATA):
    if z <= 0: raise ValueError("Количество ремней должно быть положительным.")
    if z in cz_data: return cz_data[z]
    elif z >= 5: return cz_data[5]
    return 1.0

def calculate_number_of_belts(p_design, p0, cl, calpha, cz_trial=1.0):
    denominator = p0 * cl * calpha * cz_trial
    if denominator == 0: raise ValueError("Деление на ноль при расчете ремней.")
    return p_design / denominator

# --- НОВАЯ ФУНКЦИЯ ДЛЯ РАБОТЫ С ТОЧНЫМИ ДАННЫМИ ---
def get_power_from_dataframe(df_power, d1, n1):
    if df_power is None or df_power.empty: return 0.0
    points = df_power[['d', 'n1']].values
    values = df_power['Pb'].values
    query_point = (d1, n1)
    try:
        interpolated_power = griddata(points, values, query_point, method='linear')
        if pd.isna(interpolated_power):
            interpolated_power = griddata(points, values, query_point, method='nearest')
        return float(interpolated_power) if pd.notna(interpolated_power) else 0.0
    except Exception as e:
        print(f"Ошибка во время интерполяции: {e}")
        return 0.0