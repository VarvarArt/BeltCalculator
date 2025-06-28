# 1_Calculator.py (Исправленная версия без дублирования)

import streamlit as st
import math
import io
import sys

from calculations import (
    calculate_transmission_ratio, calculate_design_power, determine_belt_section, get_min_pulley_diameter,
    find_nearest_standard_value, calculate_belt_length, calculate_actual_center_distance,
    get_actual_transmission_ratio, calculate_belt_speed, get_p0_value, get_cl_value,
    calculate_angle_of_wrap, get_calpha_value, get_cz_value, calculate_number_of_belts,
    get_power_from_dataframe
)
from data import (
    STANDARD_PULLEY_DIAMETERS, STANDARD_BELT_LENGTHS,
    CALPHA_DATA, CZ_DATA, LOAD_COEFFICIENTS, MATERIAL_P0_CORRECTION_FACTORS, load_all_data
)

st.set_page_config(page_title="Калькулятор приводных ремней", page_icon="⚙️", layout="centered")
st.title("⚙️ Калькулятор приводных ремней")
st.markdown("---")

st.header("1. Ввод основных параметров")
power = st.number_input("Номинальная мощность (P) в кВт:", 0.1, value=15.0, step=0.1, format="%.2f")
n1 = st.number_input("Частота вращения ведущего вала (n1) в об/мин:", 1.0, value=1450.0, step=1.0, format="%.1f")
n2 = st.number_input("Частота вращения ведомого вала (n2) в об/мин:", 1.0, value=650.0, step=1.0, format="%.1f")
approx_center_distance = st.number_input("Примерное межосевое расстояние (a_прим) в мм:", 100.0, value=1000.0,
                                         step=10.0, format="%.1f")

st.subheader("2. Выбор типа нагрузки")
load_type_mapping = {"Спокойная (равномерная) нагрузка": '1', "Средняя нагрузка (небольшие толчки)": '2',
                     "Тяжелая нагрузка (умеренные толчки)": '3', "Ударная нагрузка (сильные толчки)": '4'}
selected_load_type_name = st.selectbox("Выберите тип нагрузки:", list(load_type_mapping.keys()), index=2)
load_type_choice = load_type_mapping[selected_load_type_name]

st.subheader("3. Выбор материала ремня")
material_options = list(MATERIAL_P0_CORRECTION_FACTORS.keys())
selected_material_name = st.radio("Выберите тип материала ремня:", material_options, index=0)
material_correction_factor = MATERIAL_P0_CORRECTION_FACTORS[selected_material_name]

st.markdown("---")

if st.button("Выполнить расчет"):
    st.header("4. Результаты расчета")

    # Показать индикатор загрузки
    with st.spinner('Загрузка данных из каталога...'):
        try:
            _ALL_DATA = load_all_data()
            CL_DATA = _ALL_DATA["CL_DATA"]
            PB_DATA = _ALL_DATA["PB_DATA"]
            debug_messages = _ALL_DATA.get("DEBUG_MESSAGES", [])
        except Exception as e:
            st.error(f"Ошибка загрузки данных: {e}")
            st.stop()

    try:
        # Основные расчеты
        transmission_ratio = calculate_transmission_ratio(n1, n2)
        st.write(f"**Теоретическое передаточное число (i):** {transmission_ratio:.2f}")

        calculated_power, kp_value = calculate_design_power(power, load_type_choice)
        st.write(f"**Коэффициент режима работы (Kp):** {kp_value}")
        st.write(f"**Расчетная мощность (P_расч):** {calculated_power:.2f} кВт")

        belt_section = determine_belt_section(calculated_power, n1)
        st.write(f"**Предполагаемое сечение ремня:** {belt_section}")

        # Выбор диаметров шкивов
        min_d1 = get_min_pulley_diameter(belt_section)
        standard_diameters = STANDARD_PULLEY_DIAMETERS.get(belt_section, [])

        if not standard_diameters:
            st.error(f"Не найдены стандартные диаметры для профиля {belt_section}")
            st.stop()

        selected_d1 = find_nearest_standard_value(min_d1, standard_diameters, greater_or_equal=True)
        st.write(f"**Выбранный стандартный диаметр ведущего шкива (d1):** {selected_d1} мм")

        calculated_d2 = selected_d1 * transmission_ratio
        selected_d2 = find_nearest_standard_value(calculated_d2, standard_diameters, greater_or_equal=False)
        st.write(f"**Выбранный стандартный диаметр ведомого шкива (d2):** {selected_d2} мм")

        actual_transmission_ratio = get_actual_transmission_ratio(selected_d1, selected_d2)
        st.write(f"**Фактическое передаточное число (i_факт):** {actual_transmission_ratio:.2f}")

        # Расчет длины ремня
        required_belt_length = calculate_belt_length(selected_d1, selected_d2, approx_center_distance)
        standard_lengths = STANDARD_BELT_LENGTHS.get(belt_section, [])

        if not standard_lengths:
            st.error(f"Не найдены стандартные длины для профиля {belt_section}")
            st.stop()

        selected_lp = find_nearest_standard_value(required_belt_length, standard_lengths, greater_or_equal=True)
        st.write(f"**Выбранная стандартная длина ремня (Lp):** {selected_lp} мм")

        actual_center_distance = calculate_actual_center_distance(selected_lp, selected_d1, selected_d2)
        st.write(f"**Уточненное межосевое расстояние (a_ут):** {actual_center_distance:.2f} мм")

        st.subheader("5. Расчет количества ремней")
        belt_speed_v = calculate_belt_speed(selected_d1, n1)
        st.write(f"**Окружная скорость ремня (V):** {belt_speed_v:.2f} м/с")

        # Получение базовой мощности P0
        p0_base, p0_debug_messages = get_p0_value(belt_section, float(selected_d1), float(n1), PB_DATA,
                                                  material_correction_factor)
        debug_messages.extend(p0_debug_messages)

        if p0_base <= 0.0:
            st.error(
                f"ВНИМАНИЕ: Не удалось определить базовую мощность P0 из каталога для профиля '{belt_section}'. Проверьте наличие файлов данных.")
            st.warning("Используется приближенное значение P0 = 1.0 кВт для продолжения расчета.")
            p0_base = 1.0  # Временное значение для продолжения работы
        else:
            st.success(f"✅ Используются точные данные из каталога для профиля '{belt_section}'.")

        p0_final = p0_base * material_correction_factor
        st.write(f"**Номинальная мощность P0 (с учетом материала):** {p0_final:.2f} кВт")

        # Получение коэффициентов
        cl_value = get_cl_value(belt_section, selected_lp, CL_DATA)
        if cl_value == 1.0:
            st.warning(f"Коэффициент длины CL = 1.0 (возможно, данные не найдены для профиля {belt_section})")

        angle_alpha1_deg = calculate_angle_of_wrap(selected_d1, selected_d2, actual_center_distance)
        calpha_value = get_calpha_value(angle_alpha1_deg)

        # Расчет количества ремней
        z_calculated_initial = calculate_number_of_belts(calculated_power, p0_final, cl_value, calpha_value, 1.0)
        num_belts_rounded = math.ceil(z_calculated_initial) if z_calculated_initial > 0 else 1
        cz_value_final = get_cz_value(num_belts_rounded)
        final_z_value = calculate_number_of_belts(calculated_power, p0_final, cl_value, calpha_value, cz_value_final)
        final_num_belts = math.ceil(final_z_value) if final_z_value > 0 else 1

        st.info(
            f"Коэффициент длины (CL): {cl_value:.2f} | Угол обхвата (α1): {angle_alpha1_deg:.2f}° | Коэф. угла (Cα): {calpha_value:.2f} | Коэф. кол-ва (Cz): {cz_value_final:.2f}")
        st.success(f"**Рекомендуемое количество ремней: {final_num_belts} шт.**")

        # Показать отладочную информацию в развернутом блоке
        if debug_messages:
            with st.expander("Отладочная информация", expanded=False):
                st.write(f"Количество отладочных сообщений: {len(debug_messages)}")
                for i, msg in enumerate(debug_messages[-20:]):  # Показать только последние 20 сообщений
                    st.text(f"{i + 1}: {msg}")

    except Exception as e:
        st.error(f"Произошла непредвиденная ошибка: {e}")
        st.exception(e)  # Показать полную трассировку ошибки
        st.warning("Пожалуйста, проверьте входные данные и попробуйте снова.")