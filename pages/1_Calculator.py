import streamlit as st
import math

from data import (
    load_all_data,
    MIN_PULLEY_DIAMETERS,
    LOAD_COEFFICIENTS,
    MATERIAL_P0_CORRECTION_FACTORS,
)
from calculations import (
    calculate_transmission_ratio,
    calculate_design_power,
    determine_belt_section,
    calculate_belt_length,
    get_p0_value,
    get_cl_value,
    calculate_angle_of_wrap,
    get_calpha_value,
    get_cz_value,
    calculate_number_of_belts,
)

def main():
    st.title("Калькулятор клиновых ремней")

    # точное приведение типа
    data_loaded = load_all_data()
    pb_data = data_loaded["PB_DATA"]  # type: ignore
    cl_data = data_loaded["CL_DATA"]  # type: ignore
    debug_all = data_loaded["DEBUG"]  # type: ignore

    st.sidebar.header("Параметры")
    power = st.sidebar.number_input("Мощность, кВт", min_value=0.1, value=5.0)
    n1 = st.sidebar.number_input("Обороты ведущего вала, об/мин", min_value=100, value=1450)
    n2 = st.sidebar.number_input("Обороты ведомого вала, об/мин", min_value=100, value=725)
    center = st.sidebar.number_input("Межосевое расстояние, мм", min_value=100, value=500)
    load_type = st.sidebar.selectbox("Тип нагрузки", list(LOAD_COEFFICIENTS.keys()))
    material = st.sidebar.selectbox("Материал ремня", list(MATERIAL_P0_CORRECTION_FACTORS.keys()))

    if st.sidebar.button("Рассчитать"):
        ratio = calculate_transmission_ratio(n1, n2)
        design_power, load_coeff = calculate_design_power(power, load_type)
        section = determine_belt_section(design_power, n1)

        d1 = max(MIN_PULLEY_DIAMETERS[section], 80)
        d2 = d1 * ratio
        L = calculate_belt_length(d1, d2, center)

        mat_factor = MATERIAL_P0_CORRECTION_FACTORS[material]
        p0, dbg_p0 = get_p0_value(section, d1, n1, pb_data, mat_factor)
        cl, dbg_cl = get_cl_value(section, L, cl_data)

        wrap = calculate_angle_of_wrap(d1, d2, center)
        calpha = get_calpha_value(wrap)
        cz = get_cz_value(math.ceil(design_power / (p0 * cl * calpha)))

        belts, dbg_belts = calculate_number_of_belts(design_power, p0, cl, calpha, cz)

        st.subheader("Результаты")
        st.write(f"Расчётная мощность: {design_power:.2f} кВт (коэфф.: {load_coeff:.2f})")
        st.write(f"Сечение ремня: {section}")
        st.write(f"Диаметры: ведущий {d1:.0f} мм / ведомый {d2:.0f} мм")
        st.write(f"Длина ремня: {L:.0f} мм")
        st.write(f"P0: {p0:.2f} кВт; CL: {cl:.3f}; Cα: {calpha:.2f}; Cz: {cz:.2f}")
        st.write(f"Необходимое количество ремней: {belts}")

        st.subheader("Отладка")
        for msg in dbg_p0 + dbg_cl + dbg_belts + debug_all:
            st.text(msg)

if __name__ == "__main__":
    main()
