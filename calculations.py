# calculations.py
import math

from data import (  # Эти импорты могут остаться для автономной работы calculations.py
    MIN_PULLEY_DIAMETERS,
    LOAD_COEFFICIENTS,
    # Зависит от STANDARD_PULLEY_DIAMETERS_COMMON
    P0_DATA_BY_V_RANGES,
    P0_VALUES,
    CL_DATA,
    CALPHA_DATA,
    CZ_DATA
)


# Мы больше НЕ импортируем все словари напрямую здесь.
# Вместо этого мы будем передавать их в функции как аргументы,
# чтобы calculations.py был более универсальным и не зависел от data.py
# (хотя импорты все равно останутся для обратной совместимости, если кто-то захочет
# использовать calculations.py без streamlit. В app.py мы передаем нужные данные.)


def calculate_transmission_ratio(n1, n2):
    """
    Вычисляет передаточное число (i).
    n1 - частота вращения ведущего вала, n2 - частота вращения ведомого вала.
    """
    if n2 == 0:
        raise ValueError("Частота вращения ведомого вала (n2) не может быть равна нулю.")
    return n1 / n2


def calculate_design_power(nominal_power, load_type_choice, load_coefficients_data=LOAD_COEFFICIENTS):
    """
    Вычисляет расчетную мощность (P_расч) с учетом коэффициента режима работы (Kp).
    load_coefficients_data: словарь коэффициентов нагрузки (передается из Streamlit).
    """
    load_mapping = {
        '1': "спокойная",
        '2': "средняя",
        '3': "тяжелая",
        '4': "ударная"
    }

    load_type = load_mapping.get(load_type_choice)
    if load_type is None:
        raise ValueError("Неизвестный тип нагрузки.")

    kp_value = load_coefficients_data.get(load_type, 1.0)  # По умолчанию 1.0, если тип не найден
    return nominal_power * kp_value, kp_value


# В calculations.py найди функцию determine_belt_section
# и ЗАМЕНИ ЕЁ НА ЭТО:

def determine_belt_section(P_design, n1_rpm):
    """
    Определяет сечение ремня по расчетной мощности.
    Эти диапазоны являются ОБЩИМИ рекомендациями из инженерных справочников
    для классических клиновых ремней и могут отличаться от точных каталогов производителей.
    Для высокой точности требуется база данных конкретного производителя.
    """
    # Здесь мы используем более общие диапазоны мощности для выбора профиля,
    # что ближе к тому, как это делается на начальных этапах подбора.
    if P_design <= 0.75: # Обычно для мощностей до 0.75 кВт
        return 'A'
    elif P_design <= 7.5: # Обычно для мощностей до 7.5 кВт
        return 'B'
    elif P_design <= 30: # Обычно для мощностей до 30 кВт
        return 'C'
    elif P_design <= 75: # Обычно для мощностей до 75 кВт
        return 'D'
    elif P_design > 75: # Для мощностей свыше 75 кВт
        return 'E'
    return 'Не определено' # Если мощность не попала ни в один диапазон (крайне маловероятно)
    return "Не определено"


def get_min_pulley_diameter(belt_section, min_pulley_diameters_data=MIN_PULLEY_DIAMETERS):
    """
    Возвращает минимально рекомендуемый диаметр шкива для данного сечения ремня.
    min_pulley_diameters_data: словарь минимальных диаметров (передается из Streamlit).
    """
    return min_pulley_diameters_data.get(belt_section)


def find_nearest_standard_value(value, standard_list, greater_or_equal=True):
    """
    Находит ближайшее стандартное значение в списке.
    Если greater_or_equal=True, ищет ближайшее значение, которое больше или равно 'value'.
    Иначе ищет просто ближайшее.
    """
    if not standard_list:
        return None

    if greater_or_equal:
        filtered_list = [s_val for s_val in standard_list if s_val >= value]
        if not filtered_list:
            return max(standard_list)
        return min(filtered_list)
    else:
        return min(standard_list, key=lambda x: abs(x - value))


def calculate_belt_length(d1, d2, a):
    """
    Вычисляет расчетную длину ремня (L) по формуле.
    d1, d2 - диаметры шкивов, a - межосевое расстояние.
    Все в мм.
    """
    if a == 0:
        raise ValueError("Межосевое расстояние не может быть равно нулю для расчета длины ремня.")

    term1 = 2 * a
    term2 = 0.5 * math.pi * (d1 + d2)
    term3 = (d2 - d1) ** 2 / (4 * a)

    return term1 + term2 + term3


def calculate_actual_center_distance(lp, d1, d2):
    """
    Вычисляет фактическое межосевое расстояние (a) по стандартной длине ремня (Lp).
    """
    w = 0.5 * math.pi * (d1 + d2)
    y = (d2 - d1) ** 2

    discriminant = (lp - w) ** 2 - 2 * y

    if discriminant < 0:
        raise ValueError(
            "Невозможно рассчитать действительное межосевое расстояние: дискриминант отрицателен. Возможно, длина ремня слишком мала для выбранных диаметров шкивов.")

    return 0.25 * ((lp - w) + math.sqrt(discriminant))


def get_actual_transmission_ratio(d1, d2, slip_coefficient=0.01):
    """
    Вычисляет фактическое передаточное число с учетом проскальзывания.
    slip_coefficient - коэффициент относительного проскальзывания ремня (например, 0.01 для 1%).
    """
    if d1 == 0:
        raise ValueError("Диаметр ведущего шкива (d1) не может быть равен нулю.")
    return d2 / (d1 * (1 - slip_coefficient))


def calculate_belt_speed(d1, n1):
    """
    Вычисляет окружную скорость ремня (V) в м/с.
    d1 - диаметр ведущего шкива в мм, n1 - частота вращения ведущего вала в об/мин.
    V = (pi * d1 * n1) / (60 * 1000)
    """
    return (math.pi * d1 * n1) / (60 * 1000)


# calculations.py (Найти и ЗАМЕНИТЬ функцию get_p0_value)

# ... (весь код до этой функции остается прежним) ...

def get_p0_value(belt_section, V, material_correction_factor=1.0,
                 p0_ranges_data=P0_DATA_BY_V_RANGES, p0_values_data=P0_VALUES):
    """
    Возвращает номинальную мощность P0, передаваемую одним ремнем,
    на основе сечения ремня, окружной скорости V и коэффициента материала.
    material_correction_factor: коэффициент, учитывающий влияние материала ремня.
    p0_ranges_data: словарь диапазонов скоростей для P0.
    p0_values_data: словарь значений P0.
    """
    if belt_section not in p0_ranges_data or belt_section not in p0_values_data:
        return 0.0  # Возвращаем 0.0, если данные не найдены, чтобы избежать деления на ноль

    speed_ranges = p0_ranges_data[belt_section]
    p0_values_for_section = p0_values_data[belt_section]

    # Находим P0 для данного сечения и скорости
    p0_base = 0.0
    if V <= speed_ranges[0][0]:  # Если скорость меньше первого диапазона, берем первое значение
        p0_base = p0_values_for_section[0]
    elif V > speed_ranges[-1][1]:  # Если скорость больше последнего диапазона, берем последнее значение
        p0_base = p0_values_for_section[-1]
    else:
        for i, (min_v, max_v) in enumerate(speed_ranges):
            if min_v < V <= max_v:
                p0_base = p0_values_for_section[i]
                break

    # Применяем коэффициент корректировки материала
    return p0_base * material_correction_factor


# ... (весь код после этой функции остается прежним) ...

def get_cl_value(belt_section, lp, cl_data=CL_DATA):
    """
    Возвращает коэффициент длины ремня (CL) на основе сечения ремня и его длины Lp.
    Использует ближайшее значение из cl_data.
    cl_data: словарь данных CL (передается из Streamlit).
    """
    if belt_section not in cl_data or not cl_data[belt_section]:
        return 1.0

    available_lengths = sorted(cl_data[belt_section].keys())

    if not available_lengths:
        return 1.0

    nearest_lp = min(available_lengths, key=lambda x: abs(x - lp))

    return cl_data[belt_section][nearest_lp]


def calculate_angle_of_wrap(d1, d2, a):
    """
    Вычисляет угол обхвата меньшего шкива (alpha1) в градусах.
    d1, d2 - диаметры шкивов в мм, a - межосевое расстояние в мм.
    alpha1 = 180 - 57.3 * (d2 - d1) / a (в градусах)
    """
    if a == 0:
        raise ValueError("Межосевое расстояние не может быть равно нулю при расчете угла обхвата.")

    argument_for_asin = (d2 - d1) / (2 * a)
    if argument_for_asin > 1:
        argument_for_asin = 1
    elif argument_for_asin < -1:
        argument_for_asin = -1

    alpha_rad = math.pi - 2 * math.asin(argument_for_asin)
    angle_deg = math.degrees(alpha_rad)
    return angle_deg


def get_calpha_value(alpha1_deg, calpha_data=CALPHA_DATA):
    """
    Возвращает коэффициент угла обхвата (C_alpha) на основе угла обхвата alpha1 в градусах.
    calpha_data: словарь данных C_alpha (передается из Streamlit).
    """
    sorted_ranges = sorted(calpha_data.keys())

    for min_alpha, max_alpha in sorted_ranges:
        if min_alpha < alpha1_deg <= max_alpha:
            return calpha_data[(min_alpha, max_alpha)]

    if alpha1_deg <= sorted_ranges[0][0]:
        return calpha_data[sorted_ranges[0]]
    elif alpha1_deg > sorted_ranges[-1][1]:
        return calpha_data[sorted_ranges[-1]]

    print(
        f"ВНИМАНИЕ: Угол обхвата {alpha1_deg:.2f} градусов находится вне определенных диапазонов C_alpha. Использовано значение по умолчанию (0.90).")
    return 0.90


def get_cz_value(z, cz_data=CZ_DATA):
    """
    Возвращает коэффициент, учитывающий количество ремней (Cz).
    z - количество ремней.
    cz_data: словарь данных Cz (передается из Streamlit).
    """
    if z <= 0:
        raise ValueError("Количество ремней (z) должно быть положительным числом.")

    if z in cz_data:
        return cz_data[z]
    elif z >= 5:
        return cz_data[5]

    print(f"ВНИТОРИЕ: Коэффициент Cz для {z} ремней не определен в таблице. Использовано значение по умолчанию (1.0).")
    return 1.0


def calculate_number_of_belts(p_design, p0, cl, calpha, cz_trial=1.0):
    """
    Вычисляет требуемое количество ремней (z) на основе расчетной мощности и коэффициентов.
    """
    denominator = p0 * cl * calpha * cz_trial
    if denominator == 0:
        raise ValueError(
            "Деление на ноль при расчете количества ремней. Проверьте входные коэффициенты (P0, CL, C_alpha, Cz не могут быть равны 0).")

    z_calc = p_design / denominator
    return z_calc