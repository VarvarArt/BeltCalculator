# 1_Calculator.py
import streamlit as st
import math

# --- ЕДИНЫЙ ПРАВИЛЬНЫЙ БЛОК ИМПОРТОВ ---
# Импортируем все необходимые функции-расчеты из calculations.py
from calculations import (
    calculate_transmission_ratio,
    calculate_design_power,
    determine_belt_section,
    get_min_pulley_diameter,
    find_nearest_standard_value,
    calculate_belt_length,
    calculate_actual_center_distance,
    get_actual_transmission_ratio,
    calculate_belt_speed,
    get_p0_value,
    get_cl_value,
    calculate_angle_of_wrap,
    get_calpha_value,
    get_cz_value,
    calculate_number_of_belts,
    get_power_from_dataframe  # <-- Добавлено сюда
)

# Импортируем все данные и функцию загрузки из data.py
from data import (
    STANDARD_PULLEY_DIAMETERS,
    STANDARD_BELT_LENGTHS,
    P0_DATA_BY_V_RANGES,
    P0_VALUES,
    CL_DATA,
    CALPHA_DATA,
    CZ_DATA,
    LOAD_COEFFICIENTS,
    MATERIAL_P0_CORRECTION_FACTORS,
    load_power_data           # <-- Добавлено сюда
)

# --- КОНЕЦ БЛОКА ИМПОРТОВ ---
# 1_Calculator.py
# ...
from calculations import (
    # ... (все ваши старые импорты) ...
    calculate_number_of_belts,
    load_power_data,              # <<< НОВОЕ
    get_power_from_dataframe      # <<< НОВОЕ
)
# ...
# --- Настройки страницы Streamlit ---
st.set_page_config(
    page_title="Калькулятор приводных ремней",
    page_icon="⚙️",
    layout="centered"
)

st.title("⚙️ Калькулятор приводных ремней")
st.markdown("---")

st.header("1. Ввод основных параметров")

# --- Ввод основных параметров ---
power = st.number_input(
    "Номинальная мощность (P) в кВт:",
    min_value=0.1,
    value=10.0,
    step=0.1,
    format="%.2f",
    help="Введите мощность, передаваемую приводом."
)

n1 = st.number_input(
    "Частота вращения ведущего вала (n1) в об/мин:",
    min_value=1.0,
    value=1450.0,
    step=1.0,
    format="%.1f",
    help="Обороты ведущего вала."
)

n2 = st.number_input(
    "Частота вращения ведомого вала (n2) в об/мин:",
    min_value=1.0,
    value=480.0,
    step=1.0,
    format="%.1f",
    help="Обороты ведомого вала."
)

approx_center_distance = st.number_input(
    "Примерное межосевое расстояние (a_прим) в мм:",
    min_value=100.0,
    value=1000.0,
    step=10.0,
    format="%.1f",
    help="Примерное расстояние между центрами шкивов."
)

st.subheader("2. Выбор типа нагрузки")
load_type_mapping = {
    "Спокойная (равномерная) нагрузка": '1',
    "Средняя нагрузка (небольшие толчки)": '2',
    "Тяжелая нагрузка (умеренные толчки)": '3',
    "Ударная нагрузка (сильные толчки)": '4'
}
selected_load_type_name = st.selectbox(
    "Выберите тип нагрузки:",
    list(load_type_mapping.keys()),
    index=1, # По умолчанию выбираем "Средняя нагрузка"
    help="Тип нагрузки влияет на коэффициент режима работы (Kp)."
)
load_type_choice = load_type_mapping[selected_load_type_name]


# --- НОВЫЙ ВХОДНОЙ ПАРАМЕТР: Выбор материала ремня ---
st.subheader("3. Выбор материала ремня")
material_options = list(MATERIAL_P0_CORRECTION_FACTORS.keys())
selected_material_name = st.radio(
    "Выберите тип материала ремня (влияет на передаваемую мощность):",
    material_options,
    index=0, # По умолчанию выбираем "Стандартный"
    help="Разные материалы ремней могут передавать разную мощность."
)
material_correction_factor = MATERIAL_P0_CORRECTION_FACTORS[selected_material_name]


st.markdown("---")

# --- Кнопка для запуска расчетов ---
if st.button("Выполнить расчет"):
    st.header("4. Результаты расчета")
    try:
        # --- 2. Расчет передаточного числа ---
        transmission_ratio = calculate_transmission_ratio(n1, n2)
        st.write(f"**Теоретическое передаточное число (i):** {transmission_ratio:.2f}")

        # --- 3. Определение коэффициента режима работы (Kp) и расчетной мощности (P_расч) ---
        calculated_power, kp_value = calculate_design_power(power, load_type_choice, load_coefficients_data=LOAD_COEFFICIENTS)
        st.write(f"**Коэффициент режима работы (Kp):** {kp_value}")
        st.write(f"**Расчетная мощность (P_расч):** {calculated_power:.2f} кВт")

        # --- 4. Подбор сечения ремня ---
        belt_section = determine_belt_section(calculated_power, n1)
        if belt_section == "Не определено":
            st.error("Невозможно определить сечение ремня. Проверьте входные параметры.")
            st.stop()
        st.write(f"**Предполагаемое сечение ремня:** {belt_section}")

        # --- 5. Определение диаметров шкивов ---
        min_d1 = get_min_pulley_diameter(belt_section)
        if min_d1 is None:
            st.error(f"Невозможно найти минимальный диаметр для сечения {belt_section}.")
            st.stop()

        standard_diameters_for_section = STANDARD_PULLEY_DIAMETERS.get(belt_section, [])
        if not standard_diameters_for_section:
            st.warning(f"ВНИМАНИЕ: Нет стандартных диаметров шкивов для сечения {belt_section} в базе данных. Используем минимальный d1.")
            selected_d1 = max(min_d1, 50)
            st.write(f"**Выбранный стандартный диаметр ведущего шкива (d1):** {selected_d1} мм (использован минимальный)")
        else:
            selected_d1 = find_nearest_standard_value(min_d1, standard_diameters_for_section, greater_or_equal=True)
            st.write(f"**Выбранный стандартный диаметр ведущего шкива (d1):** {selected_d1} мм (ближайший >= {min_d1})")

        calculated_d2 = selected_d1 * transmission_ratio
        selected_d2 = find_nearest_standard_value(calculated_d2, standard_diameters_for_section, greater_or_equal=False)

        if selected_d2 < min_d1:
            st.warning(f"ВНИМАНИЕ: Выбранный d2 ({selected_d2} мм) меньше минимально рекомендуемого для сечения {belt_section} ({min_d1} мм). Рекомендуется выбрать другой d1 или пересмотреть передачу.")

        st.write(f"**Расчетный диаметр ведомого шкива (d2_calc):** {calculated_d2:.2f} мм")
        st.write(f"**Выбранный стандартный диаметр ведомого шкива (d2):** {selected_d2} мм")

        actual_transmission_ratio = get_actual_transmission_ratio(selected_d1, selected_d2, slip_coefficient=0.01)
        st.write(f"**Фактическое передаточное число (i_факт) с учетом проскальзывания 1%:** {actual_transmission_ratio:.2f}")

        # --- 6. Расчет и подбор стандартной длины ремня и уточнение межосевого расстояния ---
        try:
            required_belt_length = calculate_belt_length(selected_d1, selected_d2, approx_center_distance)
            st.write(f"\n**Требуемая расчетная длина ремня (L_расч):** {required_belt_length:.2f} мм")
        except ValueError as e:
            st.error(f"Ошибка при расчете длины ремня: {e}")
            st.stop()

        standard_lengths_for_section = STANDARD_BELT_LENGTHS.get(belt_section, [])
        if not standard_lengths_for_section:
            st.warning(f"ВНИМАНИЕ: Нет стандартных длин ремней для сечения {belt_section} в базе данных. Используем расчетную длину.")
            selected_lp = required_belt_length
            st.write(f"**Выбранная стандартная длина ремня (Lp):** {selected_lp:.2f} мм (использована расчетная)")
        else:
            # ИЗМЕНЕННАЯ СТРОКА: greater_or_equal=True для длины ремня
            selected_lp = find_nearest_standard_value(required_belt_length, standard_lengths_for_section, greater_or_equal=True)
            st.write(f"**Выбранная стандартная длина ремня (Lp):** {selected_lp} мм (ближайшая >= {required_belt_length:.2f})")

        try:
            actual_center_distance = calculate_actual_center_distance(selected_lp, selected_d1, selected_d2)
            st.write(f"**Уточненное межосевое расстояние (a_ут) для Lp = {selected_lp} мм:** {actual_center_distance:.2f} мм")
        except ValueError as e:
            st.error(f"Ошибка при уточнении межосевого расстояния: {e}")
            st.stop()

        # 1_Calculator.py (внутри if st.button(...))

        # <<< НАЧАЛО НОВОГО БЛОКА >>>

        # --- 7. Расчет количества ремней (z) ---
        st.subheader("5. Расчет количества ремней")

        belt_speed_v = calculate_belt_speed(selected_d1, n1)
        st.write(f"**Окружная скорость ремня (V):** {belt_speed_v:.2f} м/с")

        p0_value = 0.0

        # --- УМНАЯ ЛОГИКА ВЫБОРА МЕТОДА РАСЧЕТА ---

        # Загружаем данные для профиля 'C', если они еще не загружены
        if 'power_data_c' not in st.session_state:
            st.session_state['power_data_c'] = load_power_data('C')

        # Если определен профиль 'C' и для него есть точные данные
        if belt_section == 'C' and st.session_state['power_data_c'] is not None:
            st.success("✅ Используются точные данные из каталога для профиля 'C'.")

            # Получаем базовую мощность Pb из нашей таблицы
            # Примечание: Мы пока не учитываем добавочную мощность Pd для простоты.
            p0_value = get_power_from_dataframe(st.session_state['power_data_c'], selected_d1, n1)

            # Применяем коэффициент материала к базовой мощности
            p0_value *= material_correction_factor

        # Для всех остальных профилей используем старый метод
        else:
            if belt_section != 'C':
                st.warning(
                    f"⚠️ Используется обобщенный расчет для профиля '{belt_section}'. Точные данные доступны только для профиля 'C'.")
            else:
                st.error("Не удалось загрузить точные данные для профиля 'C'. Используется обобщенный расчет.")

            # Старый, обобщенный метод расчета P0
            p0_value = get_p0_value(belt_section, belt_speed_v,
                                    material_correction_factor=material_correction_factor,
                                    p0_ranges_data=P0_DATA_BY_V_RANGES, p0_values_data=P0_VALUES)

        if p0_value == 0.0:
            st.error("ВНИМАНИЕ: Не удалось определить базовую мощность P0. Расчет количества ремней невозможен.")
            st.stop()
        st.write(f"**Номинальная мощность P0, передаваемая одним ремнем (с учетом материала):** {p0_value:.2f} кВт")

        # --- Остальная часть кода остается без изменений ---
        cl_value = get_cl_value(belt_section, selected_lp, cl_data=CL_DATA)
        st.write(f"**Коэффициент длины ремня (CL):** {cl_value:.2f}")

        try:
            angle_alpha1_deg = calculate_angle_of_wrap(selected_d1, selected_d2, actual_center_distance)
            st.write(f"**Угол обхвата меньшего шкива (alpha1):** {angle_alpha1_deg:.2f}°")
            calpha_value = get_calpha_value(angle_alpha1_deg, calpha_data=CALPHA_DATA)
            st.write(f"**Коэффициент угла обхвата (C_alpha):** {calpha_value:.2f}")
        except ValueError as e:
            st.error(f"Ошибка при расчете угла обхвата: {e}. Использовано значение C_alpha по умолчанию.")
            calpha_value = 1.0

        z_calculated_initial = calculate_number_of_belts(
            calculated_power, p0_value, cl_value, calpha_value, cz_trial=1.0
        )

        num_belts_rounded = math.ceil(z_calculated_initial)
        if num_belts_rounded == 0: num_belts_rounded = 1

        cz_value_final = get_cz_value(num_belts_rounded, cz_data=CZ_DATA)
        st.write(f"**Коэффициент количества ремней (Cz) для {num_belts_rounded} ремней:** {cz_value_final:.2f}")

        final_z_value = calculate_number_of_belts(
            calculated_power, p0_value, cl_value, calpha_value, cz_trial=cz_value_final
        )
        final_num_belts = math.ceil(final_z_value)
        if final_num_belts == 0: final_num_belts = 1

        st.write(f"**Окончательное расчетное количество ремней:** {final_z_value:.2f}")
        st.success(f"**Рекомендуемое количество ремней (целое): {final_num_belts} шт.**")

        # <<< КОНЕЦ НОВОГО БЛОКА >>>

    except Exception as e:
        st.error(f"Произошла ошибка при выполнении расчетов: {e}")
        st.warning("Пожалуйста, проверьте входные данные и попробуйте снова.")

if 'STANDARD_PULLEY_DIAMETERS' not in st.session_state:
    st.session_state['STANDARD_PULLEY_DIAMETERS'] = STANDARD_PULLEY_DIAMETERS
if 'STANDARD_BELT_LENGTHS' not in st.session_state:
    st.session_state['STANDARD_BELT_LENGTHS'] = STANDARD_BELT_LENGTHS
if 'P0_DATA_BY_V_RANGES' not in st.session_state:
    st.session_state['P0_DATA_BY_V_RANGES'] = P0_DATA_BY_V_RANGES
if 'P0_VALUES' not in st.session_state:
    st.session_state['P0_VALUES'] = P0_VALUES
if 'CL_DATA' not in st.session_state:
    st.session_state['CL_DATA'] = CL_DATA
if 'CALPHA_DATA' not in st.session_state:
    st.session_state['CALPHA_DATA'] = CALPHA_DATA
if 'CZ_DATA' not in st.session_state:
    st.session_state['CZ_DATA'] = CZ_DATA
if 'LOAD_COEFFICIENTS' not in st.session_state:
    st.session_state['LOAD_COEFFICIENTS'] = LOAD_COEFFICIENTS
if 'MATERIAL_P0_CORRECTION_FACTORS' not in st.session_state:
    st.session_state['MATERIAL_P0_CORRECTION_FACTORS'] = MATERIAL_P0_CORRECTION_FACTORS