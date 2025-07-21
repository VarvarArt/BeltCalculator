# calculations.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)

import math
import pandas as pd
from data import (
    LOAD_COEFFICIENTS, CALPHA_DATA, CZ_DATA, MIN_PULLEY_DIAMETERS
)


def get_power_from_dataframe(df, d_query, n_query):
    """Получает мощность P0 из DataFrame с интерполяцией по диаметру и RPM."""
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
        if d_high == d_low:
            return low_power, [f"Использован ближайший диаметр: {d_low}мм"]

        interpolated_power = low_power + (high_power - low_power) * (d_query - d_low) / (d_high - d_low)
        return interpolated_power, [f"Интерполяция между диаметрами {d_low}-{d_high}мм"]
    else:
        # Если диаметр точный, интерполируем только по скорости
        power, debug_msg = get_power_for_speed(d_data, n_query)
        return power, [f"Точный диаметр {d_query}мм: {debug_msg}"]


def get_power_for_speed(df, n_query):
    """Получает мощность с интерполяцией по RPM."""
    if df.empty:
        return 0.0, "DataFrame пуст для данного диаметра"

    n_sorted = sorted(df['n1'].unique())
    if n_query in n_sorted:
        power = float(df[df['n1'] == n_query]['Pb'].iloc[0])
        return power, f"Точное значение RPM {n_query}"

    n_low = max([n for n in n_sorted if n <= n_query], default=min(n_sorted))
    n_high = min([n for n in n_sorted if n >= n_query], default=max(n_sorted))

    if n_low == n_high:
        power = float(df[df['n1'] == n_low]['Pb'].iloc[0])
        return power, f"Ближайший RPM {n_low}"

    p_low = float(df[df['n1'] == n_low]['Pb'].iloc[0])
    p_high = float(df[df['n1'] == n_high]['Pb'].iloc[0])

    # Линейная интерполяция по скорости
    interpolated_power = p_low + (p_high - p_low) * (n_query - n_low) / (n_high - n_low)
    return interpolated_power, f"Интерполяция RPM между {n_low}-{n_high}"


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


def get_p0_value(belt_section, d1, n1, pb_data, material_factor=1.0):
    """
    ИСПРАВЛЕННАЯ ФУНКЦИЯ: Получает номинальную мощность P0 из каталога.

    Параметры:
    - belt_section: сечение ремня (например, 'C')
    - d1: диаметр ведущего шкива
    - n1: обороты ведущего вала
    - pb_data: словарь DataFrames с данными P0 по профилям
    - material_factor: коэффициент материала
    """
    debug_messages = []

    # Получаем DataFrame для данного профиля
    df = pb_data.get(belt_section)
    if df is None or df.empty:
        debug_messages.append(f"❌ Нет данных P0 для профиля '{belt_section}'")
        return 1.0, debug_messages

    debug_messages.append(f"✅ Найдены данные P0 для профиля '{belt_section}': {len(df)} записей")

    # Получаем мощность с интерполяцией
    p0_base, interpolation_debug = get_power_from_dataframe(df, d1, n1)
    debug_messages.extend(interpolation_debug)

    # Применяем коэффициент материала
    p0_corrected = p0_base * material_factor

    debug_messages.append(f"P0 базовая: {p0_base:.3f} кВт")
    debug_messages.append(f"Коэффициент материала: {material_factor:.2f}")
    debug_messages.append(f"P0 скорректированная: {p0_corrected:.3f} кВт")

    return p0_corrected, debug_messages


def get_cl_value(belt_section, belt_length, cl_data):
    """
    ИСПРАВЛЕННАЯ ФУНКЦИЯ: Получает коэффициент CL из каталога.

    Параметры:
    - belt_section: сечение ремня (например, 'C')
    - belt_length: длина ремня в мм
    - cl_data: словарь с данными CL по профилям
    """
    debug_messages = []

    # Получаем данные для профиля
    section_data = cl_data.get(belt_section, {})
    if not section_data:
        debug_messages.append(f"❌ Нет данных CL для профиля '{belt_section}'")
        return 1.0, debug_messages

    debug_messages.append(f"✅ Найдены данные CL для профиля '{belt_section}': {len(section_data)} значений")

    # Получаем отсортированные длины
    lengths = sorted(section_data.keys())

    # Если длина меньше минимальной
    if belt_length <= min(lengths):
        cl_value = section_data[min(lengths)]
        debug_messages.append(f"Длина {belt_length}мм меньше минимальной {min(lengths)}мм, CL = {cl_value}")
        return cl_value, debug_messages

    # Если длина больше максимальной
    if belt_length >= max(lengths):
        cl_value = section_data[max(lengths)]
        debug_messages.append(f"Длина {belt_length}мм больше максимальной {max(lengths)}мм, CL = {cl_value}")
        return cl_value, debug_messages

    # Находим ближайшие значения для интерполяции
    for i, length in enumerate(lengths):
        if length > belt_length:
            l1, l2 = lengths[i - 1], length
            cl1, cl2 = section_data[l1], section_data[l2]
            # Линейная интерполяция
            cl_interpolated = cl1 + (cl2 - cl1) * (belt_length - l1) / (l2 - l1)
            debug_messages.append(f"Интерполяция CL между длинами {l1}-{l2}мм: {cl_interpolated:.3f}")
            return cl_interpolated, debug_messages

    # Fallback
    debug_messages.append("Используется CL = 1.0 (fallback)")
    return 1.0, debug_messages


def calculate_angle_of_wrap(d1, d2, center_distance):
    """Рассчитывает угол обхвата малого шкива."""
    if center_distance == 0:
        return 180.0
    angle = 180 - 57 * (d2 - d1) / center_distance
    return max(90, angle)  # Минимальный угол обхвата 90 градусов


def get_calpha_value(angle):
    """Получает коэффициент Cα."""
    # Преобразуем ключи из tuple в числа для удобства
    angle_ranges = []
    for key in CALPHA_DATA.keys():
        if isinstance(key, tuple):
            angle_ranges.append((key[0], key[1], CALPHA_DATA[key]))

    angle_ranges.sort(key=lambda x: x[0])  # Сортируем по нижней границе

    # Ищем подходящий диапазон
    for lower, upper, value in angle_ranges:
        if lower <= angle <= upper:
            return value

    # Если не нашли, возвращаем ближайшее
    if angle < angle_ranges[0][0]:
        return angle_ranges[0][2]
    else:
        return angle_ranges[-1][2]


def get_cz_value(z):
    """Получает коэффициент Cz."""
    belts = sorted(CZ_DATA.keys())

    if z <= min(belts):
        return CZ_DATA[min(belts)]
    if z >= max(belts):
        return CZ_DATA[max(belts)]

    return CZ_DATA.get(int(z), 1.0)


def calculate_number_of_belts(design_power, p0, cl, calpha, cz):
    """Рассчитывает необходимое количество ремней."""
    if p0 <= 0 or cl <= 0 or calpha <= 0 or cz <= 0:
        return float('inf'), ["Один или несколько коэффициентов равны нулю"]

    z = design_power / (p0 * cl * calpha * cz)
    belts_needed = math.ceil(z)

    debug = [
        f"Расчетная мощность: {design_power:.2f} кВт",
        f"P0: {p0:.3f}, CL: {cl:.3f}, Cα: {calpha:.3f}, Cz: {cz:.3f}",
        f"Расчетное количество: {z:.2f} → {belts_needed} ремней"
    ]

    return belts_needed, debug
