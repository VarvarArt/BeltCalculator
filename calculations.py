# calculations.py (исправлены ошибки типизации, импорта и именования)

import math
from typing import Dict, List, Tuple

import pandas

from data import LOAD_COEFFICIENTS, CALPHA_DATA, CZ_DATA  # MIN_PULLEY_DIAMETERS не используется здесь

def get_power_for_speed(df, n_query: float) -> Tuple[float, List[str]]:
    """Интерполяция мощности Pb по RPM."""
    debug_msgs: List[str] = []
    n_values = sorted(df['n1'].unique())
    if n_query in n_values:
        pb = float(df[df['n1'] == n_query]['Pb'].iloc[0])
        debug_msgs.append(f"Exact RPM {n_query}")
        return pb, debug_msgs

    lower = max((n for n in n_values if n <= n_query), default=n_values[0])
    upper = min((n for n in n_values if n >= n_query), default=n_values[-1])

    p_low = float(df[df['n1'] == lower]['Pb'].iloc[0])
    p_high = float(df[df['n1'] == upper]['Pb'].iloc[0])
    interp = p_low + (p_high - p_low) * (n_query - lower) / (upper - lower)
    debug_msgs.append(f"Interpolated RPM between {lower}-{upper}")
    return interp, debug_msgs

def get_power_from_dataframe(df, d_query: float, n_query: float) -> Tuple[float, List[str]]:
    """Интерполяция мощности Pb по диаметру и RPM."""
    debug_msgs: List[str] = []
    d_values = sorted(df['d'].unique())
    if d_query in d_values:
        power, msgs = get_power_for_speed(df[df['d'] == d_query], n_query)
        debug_msgs.extend(msgs)
        return power, debug_msgs

    lower = max((d for d in d_values if d <= d_query), default=d_values[0])
    upper = min((d for d in d_values if d >= d_query), default=d_values[-1])

    p_low, msgs_low = get_power_for_speed(df[df['d'] == lower], n_query)
    p_high, msgs_high = get_power_for_speed(df[df['d'] == upper], n_query)
    interp = p_low + (p_high - p_low) * (d_query - lower) / (upper - lower)

    debug_msgs.append(f"Interpolated diameter between {lower}-{upper}")
    debug_msgs.extend(msgs_low)
    debug_msgs.extend(msgs_high)
    return interp, debug_msgs

def calculate_transmission_ratio(n1: float, n2: float) -> float:
    return n1 / n2

def calculate_design_power(power: float, load_type: str) -> Tuple[float, float]:
    """
    Рассчитывает расчётную мощность и возвращает:
      - design_power: float
      - load_coeff: float
    """
    load_coeff = LOAD_COEFFICIENTS.get(load_type, 1.0)
    return power * load_coeff, load_coeff

def determine_belt_section(power: float, rpm: float) -> str:
    """Аргумент rpm используется для возможного расширения логики."""
    if power <= 3:
        return 'A'
    if power <= 15:
        return 'B'
    return 'C'

def get_p0_value(
    belt_section: str,
    d1: float,
    n1: float,
    pb_data: Dict[str, 'pandas.DataFrame'],
    material_factor: float = 1.0
) -> Tuple[float, List[str]]:
    """Возвращает скорректированную мощность P0 и отладочные сообщения."""
    debug_msgs: List[str] = []
    df = pb_data.get(belt_section)
    if df is None or df.empty:
        debug_msgs.append(f"No P0 data for section '{belt_section}'")
        return 1.0, debug_msgs

    debug_msgs.append(f"Found P0 data for '{belt_section}'")
    p0_base, msgs = get_power_from_dataframe(df, d1, n1)
    debug_msgs.extend(msgs)

    p0 = p0_base * material_factor
    debug_msgs.append(f"P0 corrected: {p0:.3f} kW")
    return p0, debug_msgs

def get_cl_value(
    belt_section: str,
    belt_length: float,
    cl_data: Dict[str, Dict[int, float]]
) -> Tuple[float, List[str]]:
    """Возвращает коэффициент CL и отладочные сообщения."""
    debug_msgs: List[str] = []
    section_map = cl_data.get(belt_section, {})
    if not section_map:
        debug_msgs.append(f"No CL data for section '{belt_section}'")
        return 1.0, debug_msgs

    lengths = sorted(section_map.keys())
    if belt_length <= lengths[0]:
        debug_msgs.append(f"Min length used: {lengths[0]}")
        return section_map[lengths[0]], debug_msgs
    if belt_length >= lengths[-1]:
        debug_msgs.append(f"Max length used: {lengths[-1]}")
        return section_map[lengths[-1]], debug_msgs

    for i in range(1, len(lengths)):
        if belt_length < lengths[i]:
            l1, l2 = lengths[i-1], lengths[i]
            c1, c2 = section_map[l1], section_map[l2]
            cl = c1 + (c2 - c1) * (belt_length - l1) / (l2 - l1)
            debug_msgs.append(f"Interpolated CL between lengths {l1}-{l2}")
            return cl, debug_msgs

    debug_msgs.append("Fallback CL = 1.0")
    return 1.0, debug_msgs

def calculate_belt_length(d1: float, d2: float, center: float) -> float:
    return 2*center + math.pi*(d1 + d2)/2 + (d2 - d1)**2/(4*center)

def calculate_actual_center_distance(length: float, d1: float, d2: float) -> float:
    a = (length - math.pi*(d1 + d2)/2) / 2
    h = (d2 - d1) / 2
    return math.sqrt(max(0.0, a*a - h*h))

def calculate_angle_of_wrap(d1: float, d2: float, center: float) -> float:
    if center == 0:
        return 180.0
    angle = 180 - 57*(d2 - d1)/center
    return max(90.0, angle)

def get_calpha_value(angle: float) -> float:
    for (low, high), val in CALPHA_DATA.items():
        if low <= angle <= high:
            return val
    return next(iter(CALPHA_DATA.values()))

def get_cz_value(belts: int) -> float:
    # Ожидает целое число ремней
    return CZ_DATA.get(belts, 1.0)

def calculate_number_of_belts(
    design_power: float,
    p0: float,
    cl: float,
    calpha: float,
    cz: float
) -> Tuple[int, List[str]]:
    """Возвращает количество ремней и отладочные сообщения."""
    debug_msgs: List[str] = []
    if any(v <= 0 for v in (p0, cl, calpha, cz)):
        debug_msgs.append("Invalid coefficient ≤ 0")
        return 0, debug_msgs

    needed = design_power / (p0 * cl * calpha * cz)
    belts = math.ceil(needed)
    debug_msgs.append(f"Calculated belts: {belts}")
    return belts, debug_msgs
