# 1_Calculator.py

import streamlit as st
import math
from calculations import *
from data import *

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
load_type_mapping = {"Спокойная": '1', "Средняя": '2', "Тяжелая": '3', "Ударная": '4'}
selected_load_type_name = st.selectbox("Выберите тип нагрузки:", list(load_type_mapping.keys()), index=2)
load_type_choice = load_type_mapping[selected_load_type_name]

st.subheader("3. Выбор материала ремня")
material_correction_factor = MATERIAL_P0_CORRECTION_FACTORS[
    st.radio("Тип материала:", list(MATERIAL_P0_CORRECTION_FACTORS.keys()), index=0)]

if st.button("Выполнить расчет"):
    st.header("4. Результаты расчета")
    try:
        transmission_ratio = calculate_transmission_ratio(n1, n2)
        calculated_power, kp_value = calculate_design_power(power, load_type_choice)
        belt_section = determine_belt_section(calculated_power, n1)
        min_d1 = get_min_pulley_diameter(belt_section)
        standard_diameters = STANDARD_PULLEY_DIAMETERS.get(belt_section, [])
        selected_d1 = find_nearest_standard_value(min_d1, standard_diameters)
        calculated_d2 = selected_d1 * transmission_ratio
        selected_d2 = find_nearest_standard_value(calculated_d2, standard_diameters, False)
        actual_transmission_ratio = get_actual_transmission_ratio(selected_d1, selected_d2)
        required_belt_length = calculate_belt_length(selected_d1, selected_d2, approx_center_distance)
        standard_lengths = STANDARD_BELT_LENGTHS.get(belt_section, [])
        selected_lp = find_nearest_standard_value(required_belt_length, standard_lengths)
        actual_center_distance = calculate_actual_center_distance(selected_lp, selected_d1, selected_d2)

        st.write(f"**Расчетная мощность (P_расч):** {calculated_power:.2f} кВт (Kp={kp_value})")
        st.write(f"**Сечение ремня:** {belt_section} | **Шкивы:** d1={selected_d1} мм, d2={selected_d2} мм")
        st.write(f"**Длина ремня (Lp):** {selected_lp} мм | **Межосевое (a):** {actual_center_distance:.2f} мм")

        st.subheader("5. Расчет количества ремней")
        belt_speed_v = calculate_belt_speed(selected_d1, n1)
        st.write(f"**Окружная скорость (V):** {belt_speed_v:.2f} м/с")

        p0_base = 0.0
        if 'power_data_c' not in st.session_state:
            st.session_state['power_data_c'] = load_power_data('C')

        if belt_section == 'C' and st.session_state['power_data_c'] is not None:
            st.success("✅ Расчет по каталогу для профиля 'C'.")
            p0_base = get_power_from_dataframe(st.session_state['power_data_c'], float(selected_d1), float(n1))
        else:
            st.warning(f"⚠️ Обобщенный расчет для профиля '{belt_section}'.")
            p0_base = get_p0_value(belt_section, belt_speed_v)

        p0_final = p0_base * material_correction_factor
        st.write(f"**Номинальная мощность P0 (с учетом материала):** {p0_final:.2f} кВт")

        cl_value = get_cl_value(belt_section, selected_lp)
        angle_alpha1_deg = calculate_angle_of_wrap(selected_d1, selected_d2, actual_center_distance)
        calpha_value = get_calpha_value(angle_alpha1_deg)
        z = calculate_number_of_belts(calculated_power, p0_final, cl_value, calpha_value)
        final_num_belts = math.ceil(z)
        cz_value_final = get_cz_value(final_num_belts)
        final_z_value = calculate_number_of_belts(calculated_power, p0_final, cl_value, calpha_value, cz_value_final)
        final_num_belts = math.ceil(final_z_value)

        st.info(f"CL: {cl_value:.2f} | Cα: {calpha_value:.2f} | Cz: {cz_value_final:.2f}")
        st.success(f"**Рекомендуемое количество ремней: {final_num_belts} шт.**")

    except Exception as e:
        st.error(f"Произошла ошибка: {e}")