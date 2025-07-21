import math
from typing import Dict, List, Tuple
import pandas as pd
from data import LOAD_COEFFICIENTS, CALPHA_DATA, CZ_DATA

def get_power_for_speed(df: pd.DataFrame, n_query: float) -> Tuple[float, List[str]]:
    debug_msgs: List[str] = []
    n_vals = sorted(df['n1'].unique().tolist())
    if n_query in n_vals:
        # Возьмём только первую подходящую запись
        filtered = df[df['n1'] == n_query]
        pb = float(filtered['Pb'].iloc[0])
        debug_msgs.append(f"Exact RPM {n_query}")
        return pb, debug_msgs
    lower = max((n for n in n_vals if n <= n_query), default=n_vals[0])
    upper = min((n for n in n_vals if n >= n_query), default=n_vals[-1])
    pb_low = float(df[df['n1'] == lower]['Pb'].iloc[0])
    pb_high = float(df[df['n1'] == upper]['Pb'].iloc[0])
    interp = pb_low + (pb_high - pb_low) * (n_query - lower) / (upper - lower)
    debug_msgs.append(f"Interpolated RPM {lower}-{upper}")
    return interp, debug_msgs

def get_power_from_dataframe(df: pd.DataFrame, d_query: float, n_query: float) -> Tuple[float, List[str]]:
    debug_msgs: List[str] = []
    d_vals = sorted([float(x) for x in df['d'].unique().tolist()])
    if d_query in d_vals:
        sub_df = df[df['d'] == d_query]
        power, msgs = get_power_for_speed(sub_df, n_query)
        debug_msgs += msgs
        return power, debug_msgs
    lower = float(max((d for d in d_vals if d <= d_query), default=d_vals[0]))
    upper = float(min((d for d in d_vals if d >= d_query), default=d_vals[-1]))
    sub_df_low = df[df['d'] == lower]
    sub_df_high = df[df['d'] == upper]
    p_low, msgs_low = get_power_for_speed(sub_df_low, n_query)
    p_high, msgs_high = get_power_for_speed(sub_df_high, n_query)
    interp = p_low + (p_high - p_low) * (d_query - lower) / (upper - lower)
    debug_msgs.append(f"Interpolated diameter {lower}-{upper}")
    debug_msgs += msgs_low + msgs_high
    return interp, debug_msgs

def calculate_transmission_ratio(n1: float, n2: float) -> float:
    return n1 / n2

def calculate_design_power(power: float, load_type: str) -> Tuple[float, float]:
    load_coeff = LOAD_COEFFICIENTS.get(load_type, 1.0)
    return power * load_coeff, load_coeff

def determine_belt_section(power: float, rpm: float) -> str:
    if power <= 3:
        return 'A'
    if power <= 15:
        return 'B'
    return 'C'

def get_p0_value(
    belt_section: str,
    d1: float,
    n1: float,
    pb_data: Dict[str, pd.DataFrame],
    material_factor: float = 1.0
) -> Tuple[float, List[str]]:
    debug_msgs: List[str] = []
    df = pb_data.get(belt_section)
    if df is None or df.empty:
        debug_msgs.append(f"No P0 data for '{belt_section}'")
        return 1.0, debug_msgs
    debug_msgs.append(f"Found P0 data for '{belt_section}'")
    p0_base, msgs = get_power_from_dataframe(df, d1, n1)
    debug_msgs += msgs
    p0 = p0_base * material_factor
    debug_msgs.append(f"P0 corrected: {p0:.3f} kW")
    return p0, debug_msgs

def get_cl_value(
    belt_section: str,
    belt_length: float,
    cl_data: Dict[str, Dict[int, float]]
) -> Tuple[float, List[str]]:
    debug_msgs: List[str] = []
    section_map = cl_data.get(belt_section, {})
    if not section_map:
        debug_msgs.append(f"No CL data for '{belt_section}'")
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
            debug_msgs.append(f"Interpolated CL {l1}-{l2}")
            return cl, debug_msgs
    debug_msgs.append("Fallback CL = 1.0")
    return 1.0, debug_msgs

def calculate_belt_length(d1: float, d2: float, center: float) -> float:
    return 2*center + math.pi*(d1 + d2)/2 + (d2 - d1)**2/(4*center)

def calculate_actual_center_distance(length: float, d1: float, d2: float) -> float:
    a = (length - math.pi*(d1 + d2)/2)/2
    h = (d2 - d1)/2
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
    return CZ_DATA.get(belts, 1.0)

def calculate_number_of_belts(
    design_power: float,
    p0: float,
    cl: float,
    calpha: float,
    cz: float
) -> Tuple[int, List[str]]:
    debug_msgs: List[str] = []
    if any(v <= 0 for v in (p0, cl, calpha, cz)):
        debug_msgs.append("Invalid coefficient ≤ 0")
        return 0, debug_msgs
    needed = design_power / (p0 * cl * calpha * cz)
    belts = math.ceil(needed)
    debug_msgs.append(f"Belts needed: {belts}")
    return belts, debug_msgs
