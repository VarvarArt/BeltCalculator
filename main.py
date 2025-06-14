# main.py
import math  # Для использования math.ceil

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
    calculate_number_of_belts
)
from data import STANDARD_PULLEY_DIAMETERS, STANDARD_BELT_LENGTHS


def calculate_v_belt_parameters():
    """
    Калькулятор для сбора основных параметров, расчета передаточного числа,
    расчетной мощности, подбора сечения ремня, определения минимальных
    диаметров шкивов, расчета длины ремня и уточнения межосевого расстояния,
    а также количества ремней.
    """
    print("Добро пожаловать в калькулятор приводных ремней!")
    print("Для начала, пожалуйста, введите следующие параметры для клинового ремня.")

    # --- 1. Запрос основных параметров ---
    while True:
        try:
            power_str = input("Введите номинальную мощность (P) в кВт: ")
            power = float(power_str)
            if power <= 0:
                print("Мощность должна быть положительным числом. Пожалуйста, попробуйте снова.")
            else:
                break
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите числовое значение для мощности.")

    while True:
        try:
            n1_str = input("Введите частоту вращения ведущего вала (n1) в об/мин: ")
            n1 = float(n1_str)
            if n1 <= 0:
                print("Частота вращения должна быть положительным числом. Пожалуйста, попробуйте снова.")
            else:
                break
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите числовое значение для частоты вращения.")

    while True:
        try:
            n2_str = input("Введите частоту вращения ведомого вала (n2) в об/мин: ")
            n2 = float(n2_str)
            if n2 <= 0:
                print("Частота вращения должна быть положительным числом. Пожалуйста, попробуйте снова.")
            else:
                break
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите числовое значение для частоты вращения.")

    while True:
        try:
            center_distance_str = input("Введите ПРИМЕРНОЕ межосевое расстояние (D или C) в мм: ")
            approx_center_distance = float(center_distance_str)
            if approx_center_distance <= 0:
                print("Межосевое расстояние должно быть положительным числом. Пожалуйста, попробуйте снова.")
            else:
                break
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите числовое значение для межосевого расстояния.")

    print("\n--- Введенные параметры ---")
    print(f"Номинальная мощность (P): {power} кВт")
    print(f"Частота вращения ведущего вала (n1): {n1} об/мин")
    print(f"Частота вращения ведомого вала (n2): {n2} об/мин")
    print(f"Примерное межосевое расстояние (D или C): {approx_center_distance} мм")

    # --- 2. Расчет передаточного числа ---
    transmission_ratio = calculate_transmission_ratio(n1, n2)
    print(f"\n--- Расчетные параметры ---")
    print(f"Теоретическое передаточное число (i): {transmission_ratio:.2f}")

    # --- 3. Определение коэффициента режима работы (Kp) и расчетной мощности (P_расч) ---
    print("\nВыберите тип нагрузки для определения коэффициента режима работы (Kp):")
    print("1. Спокойная (равномерная) нагрузка")
    print("2. Средняя нагрузка (небольшие толчки)")
    print("3. Тяжелая нагрузка (умеренные толчки)")
    print("4. Ударная нагрузка (сильные толчки)")

    load_type_choice = ''
    while load_type_choice not in ['1', '2', '3', '4']:
        load_type_choice = input("Введите номер соответствующего типа нагрузки (1-4): ")
        if load_type_choice not in ['1', '2', '3', '4']:
            print("Неверный ввод. Пожалуйста, введите число от 1 до 4.")

    calculated_power, kp_value = calculate_design_power(power, load_type_choice)
    print(f"Коэффициент режима работы (Kp): {kp_value}")
    print(f"Расчетная мощность (P_расч): {calculated_power:.2f} кВт")

    # --- 4. Подбор сечения ремня ---
    belt_section = determine_belt_section(calculated_power, n1)
    print(f"Предполагаемое сечение ремня: {belt_section}")

    # --- 5. Определение диаметров шкивов ---
    if belt_section == "Не определено":
        print("Невозможно продолжить расчет диаметров шкивов, так как сечение ремня не определено.")
        return

    min_d1 = get_min_pulley_diameter(belt_section)
    if min_d1 is None:
        print(f"Невозможно найти минимальный диаметр для сечения {belt_section}.")
        return

    print(f"Минимальный рекомендуемый диаметр ведущего шкива (d1_min) для сечения {belt_section}: {min_d1} мм")

    standard_diameters_for_section = STANDARD_PULLEY_DIAMETERS.get(belt_section, [])

    if not standard_diameters_for_section:
        print(f"ВНИМАНИЕ: Нет стандартных диаметров шкивов для сечения {belt_section} в базе данных.")
        selected_d1 = max(min_d1, 50)
        print(f"Используем минимальный d1: {selected_d1} мм")
    else:
        selected_d1 = find_nearest_standard_value(min_d1, standard_diameters_for_section, greater_or_equal=True)
        print(f"Выбранный стандартный диаметр ведущего шкива (d1): {selected_d1} мм (ближайший >= {min_d1})")

    calculated_d2 = selected_d1 * transmission_ratio
    selected_d2 = find_nearest_standard_value(calculated_d2, standard_diameters_for_section, greater_or_equal=False)

    if selected_d2 < min_d1:
        print(
            f"ВНИМАНИЕ: Выбранный d2 ({selected_d2} мм) меньше минимально рекомендуемого для сечения {belt_section} ({min_d1} мм). Рекомендуется выбрать другой d1 или пересмотреть передачу.")

    print(f"Расчетный диаметр ведомого шкива (d2_calc): {calculated_d2:.2f} мм")
    print(f"Выбранный стандартный диаметр ведомого шкива (d2): {selected_d2} мм")

    actual_transmission_ratio = get_actual_transmission_ratio(selected_d1, selected_d2, slip_coefficient=0.01)
    print(f"Фактическое передаточное число (i_факт) с учетом проскальзывания 1%: {actual_transmission_ratio:.2f}")

    # --- 6. Расчет и подбор стандартной длины ремня и уточнение межосевого расстояния ---

    try:
        required_belt_length = calculate_belt_length(selected_d1, selected_d2, approx_center_distance)
        print(f"\nТребуемая расчетная длина ремня (L_расч): {required_belt_length:.2f} мм")
    except ValueError as e:
        print(f"Ошибка при расчете длины ремня: {e}")
        return

    standard_lengths_for_section = STANDARD_BELT_LENGTHS.get(belt_section, [])

    if not standard_lengths_for_section:
        print(f"ВНИМАНИЕ: Нет стандартных длин ремней для сечения {belt_section} в базе данных.")
        selected_lp = required_belt_length
        print(f"Используем расчетную длину ремня: {selected_lp:.2f} мм")
    else:
        selected_lp = find_nearest_standard_value(required_belt_length, standard_lengths_for_section,
                                                  greater_or_equal=False)
        print(f"Выбранная стандартная длина ремня (Lp): {selected_lp} мм (ближайшая к {required_belt_length:.2f})")

    try:
        actual_center_distance = calculate_actual_center_distance(selected_lp, selected_d1, selected_d2)
        print(f"Уточненное межосевое расстояние (a_ут) для Lp = {selected_lp} мм: {actual_center_distance:.2f} мм")
    except ValueError as e:
        print(f"Ошибка при уточнении межосевого расстояния: {e}")
        return  # Выходим, если не можем рассчитать межосевое

    # --- 7. Расчет количества ремней (z) ---
    print("\n--- Расчет количества ремней ---")

    # 7.1. Расчет скорости ремня (V)
    belt_speed_v = calculate_belt_speed(selected_d1, n1)
    print(f"Окружная скорость ремня (V): {belt_speed_v:.2f} м/с")

    # 7.2. Получение P0
    p0_value = get_p0_value(belt_section, belt_speed_v)
    if p0_value == 0.0:
        print(
            "ВНИМАНИЕ: Не удалось определить P0 для данного сечения и скорости. Расчет количества ремней может быть неточным.")
        # Если P0_value равно 0, дальнейшие расчеты будут некорректны
        return
    print(f"Номинальная мощность P0, передаваемая одним ремнем: {p0_value:.2f} кВт")

    # 7.3. Получение CL
    cl_value = get_cl_value(belt_section, selected_lp)
    print(f"Коэффициент длины ремня (CL): {cl_value:.2f}")

    # 7.4. Расчет угла обхвата и получение C_alpha
    try:
        angle_alpha1_deg = calculate_angle_of_wrap(selected_d1, selected_d2, actual_center_distance)
        print(f"Угол обхвата меньшего шкива (alpha1): {angle_alpha1_deg:.2f}°")
        calpha_value = get_calpha_value(angle_alpha1_deg)
        print(f"Коэффициент угла обхвата (C_alpha): {calpha_value:.2f}")
    except ValueError as e:
        print(f"Ошибка при расчете угла обхвата: {e}")
        calpha_value = 1.0  # Заглушка, если ошибка
        print(f"Использовано значение C_alpha по умолчанию: {calpha_value:.2f}")

    # 7.5. Расчет z (первое приближение, Cz = 1.0)
    # Поскольку Cz зависит от z, а z - от Cz, сделаем итерацию:
    # 1. Считаем z при Cz=1.0
    # 2. Округляем z до целого числа (z_rounded)
    # 3. Берем Cz для z_rounded
    # 4. Пересчитываем z с новым Cz и округляем до целого.

    z_calculated_initial = 0
    try:
        z_calculated_initial = calculate_number_of_belts(
            calculated_power, p0_value, cl_value, calpha_value, cz_trial=1.0
        )
        print(f"Расчетное количество ремней (первое приближение, Cz=1.0): {z_calculated_initial:.2f}")
    except ValueError as e:
        print(f"Ошибка при расчете количества ремней: {e}")
        return

    # Округляем до ближайшего целого числа ремней вверх (т.к. ремней должно быть достаточно)
    num_belts_rounded = math.ceil(z_calculated_initial)
    if num_belts_rounded == 0:  # Если вдруг получилось 0, то минимум 1 ремень
        num_belts_rounded = 1

    # Получаем Cz для округленного количества ремней
    cz_value_final = get_cz_value(num_belts_rounded)
    print(f"Коэффициент количества ремней (Cz) для {num_belts_rounded} ремней: {cz_value_final:.2f}")

    # Пересчитываем z с окончательным Cz
    try:
        final_z_value = calculate_number_of_belts(
            calculated_power, p0_value, cl_value, calpha_value, cz_trial=cz_value_final
        )
        # Окончательно округляем вверх, так как количество ремней должно быть целым
        final_num_belts = math.ceil(final_z_value)
        if final_num_belts == 0:
            final_num_belts = 1
        print(f"Окончательное расчетное количество ремней: {final_z_value:.2f}")
        print(f"**Рекомендуемое количество ремней (целое): {final_num_belts} шт.**")

    except ValueError as e:
        print(f"Ошибка при окончательном расчете количества ремней: {e}")
        return


# Вызов функции для запуска калькулятора
if __name__ == "__main__":
    calculate_v_belt_parameters()