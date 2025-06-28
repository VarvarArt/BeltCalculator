# calculations.py (Финальная версия без scipy)

import math
import pandas as pd
from data import (
    LOAD_COEFFICIENTS, CALPHA_DATA, CZ_DATA, MIN_PULLEY_DIAMETERS
)


def get_power_from_dataframe(df, d_query, n_query):
    if df is None or df.empty:
        return 0.0, ["DataFrame is empty"]

    # Фильтруем DataFrame для нужного диаметра
    d_data = df[df['d'] == d_query]
    if d_data.empty:
        # Если точного значения диаметра нет, используем интерполяцию по диаметру
        unique_d = sorted(df['d'].unique())
        d_low = max([d for d in unique_d if d <= d_query], default=min(unique_d))
        d_high = min([d for d in unique_d if d >= d_query], default=max(unique_d))

        # Получаем значения для обоих диаметров
        low_power = get_power_for_speed(df[df['d'] == d_low], n_query)
        high_power = get_power_for_speed(df[df['d'] == d_high], n_query)

        # Интерполируем по диаметру
        return low_power + (high_power - low_power) * (d_query - d_low) / (d_high - d_low), []
    else:
        # Если диаметр точный, интерполируем только по скорости
        return get_power_for_speed(d_data, n_query), []


def get_power_for_speed(df, n_query):
    n_sorted = sorted(df['n1'].unique())
    if n_query in n_sorted:
        return float(df[df['n1'] == n_query]['Pb'].iloc[0])

    n_low = max([n for n in n_sorted if n <= n_query], default=min(n_sorted))
    n_high = min([n for n in n_sorted if n >= n_query], default=max(n_sorted))

    p_low = float(df[df['n1'] == n_low]['Pb'].iloc[0])
    p_high = float(df[df['n1'] == n_high]['Pb'].iloc[0])

    # Линейная интерполяция по скорости
    return p_low + (p_high - p_low) * (n_query - n_low) / (n_high - n_low)


def calculate_transmission_ratio(n1, n2):
    """Рассчитывает передаточное число."""
    return n1 / n2


def calculate_design_power(power, load_type):
    """Рассчитывает расчетную мощность с учетом коэффициента режима работы."""
    return power * LOAD_COEFFICIENTS.get(load_type, 1.0)


def determine_belt_section(power, n1):
    """Определяет сечение ремня на основе мощности и частоты вращения."""
    if power <= 3:
        return 'A'
    elif power <= 15:
        return 'B'
    else:
        return 'C'


def get_min_pulley_diameter(belt_section):
    """Возвращает минимальный диаметр шкива для заданного сечения ремня."""
    return MIN_PULLEY_DIAMETERS.get(belt_section, 0)


def find_nearest_standard_value(value, standard_values):
    """Находит ближайшее стандартное значение."""
    if not standard_values:
        return value
    return min(standard_values, key=lambda x: abs(x - value))


def calculate_belt_length(d1, d2, center_distance):
    """Рассчитывает длину ремня."""
    return 2 * center_distance + math.pi * (d1 + d2) / 2 + (d2 - d1) ** 2 / (4 * center_distance)


def calculate_actual_center_distance(belt_length, d1, d2):
    """Уточняет межосевое расстояние."""
    # Используем упрощенную формулу без итераций
    a = (belt_length - math.pi * (d1 + d2) / 2) / 2
    h = (d2 - d1) / 2
    return math.sqrt(a * a - h * h)


def get_actual_transmission_ratio(d1, d2):
    """Вычисляет фактическое передаточное число."""
    return d2 / d1


def calculate_belt_speed(d1, n1):
    """Рассчитывает скорость ремня."""
    return math.pi * d1 * n1 / (60 * 1000)  # м/с


def get_p0_value(pb_data, d1, n1, material_factor=1.0):
    """Получает номинальную мощность P0 с учетом поправки на материал."""
    p0, debug = get_power_from_dataframe(pb_data, d1, n1)
    return p0 * material_factor, debug


def get_cl_value(cl_data, belt_section, belt_length):
    """Получает коэффициент CL."""
    section_data = cl_data.get(belt_section, {})
    lengths = sorted(section_data.keys())

    if not lengths:
        return 1.0

    if belt_length <= min(lengths):
        return section_data[min(lengths)]
    if belt_length >= max(lengths):
        return section_data[max(lengths)]

    # Находим ближайшие значения для интерполяции
    for i, length in enumerate(lengths):
        if length > belt_length:
            l1, l2 = lengths[i - 1], length
            cl1, cl2 = section_data[l1], section_data[l2]
            # Линейная интерполяция
            return cl1 + (cl2 - cl1) * (belt_length - l1) / (l2 - l1)

    return 1.0


def calculate_angle_of_wrap(d1, d2, center_distance):
    """Рассчитывает угол обхвата малого шкива."""
    return 180 - 57 * (d2 - d1) / center_distance


def get_calpha_value(angle):
    """Получает коэффициент Cα."""
    angles = sorted(CALPHA_DATA.keys())

    if angle <= min(angles):
        return CALPHA_DATA[min(angles)]
    if angle >= max(angles):
        return CALPHA_DATA[max(angles)]

    # Находим ближайшие значения для интерполяции
    for i, a in enumerate(angles):
        if a > angle:
            a1, a2 = angles[i - 1], a
            c1, c2 = CALPHA_DATA[a1], CALPHA_DATA[a2]
            # Линейная интерполяция
            return c1 + (c2 - c1) * (angle - a1) / (a2 - a1)

    return 1.0


def get_cz_value(z):
    """Получает коэффициент Cz."""
    belts = sorted(CZ_DATA.keys())

    if z <= min(belts):
        return CZ_DATA[min(belts)]
    if z >= max(belts):
        return CZ_DATA[max(belts)]

    return CZ_DATA[z]


def calculate_number_of_belts(design_power, p0, cl, calpha, cz):
    """Рассчитывает необходимое количество ремней."""
    if p0 <= 0 or cl <= 0 or calpha <= 0 or cz <= 0:
        return float('inf')
    z = design_power / (p0 * cl * calpha * cz)
    return math.ceil(z)