import streamlit as st

# --- Настройки страницы ---
st.set_page_config(
    page_title="Архитектура Приложения",
    page_icon="🏗️",
    layout="wide"  # Широкий макет лучше подходит для документации
)

# --- Заголовок ---
st.title("🏗️ Архитектура Приложения \"Калькулятор Клиноременных Передач\"")
st.write("---")

# --- Раздел 1: Обзор ---
st.header("1. Обзор Архитектуры (Высокоуровневый)")
st.markdown("""
Приложение построено по модульному принципу и следует паттерну "Модель-Представление-Контроллер" (MVC) в упрощенном виде, что характерно для Streamlit-приложений. Основные компоненты:
*   **Модуль Данных (`data.py`):** Хранит все статические справочные данные (коэффициенты, стандартные размеры).
*   **Модуль Расчетов (`calculations.py`):** Содержит основную бизнес-логику и формулы для выполнения инженерных расчетов.
*   **Модуль Приложения/Интерфейса (`1_Calculator.py`):** Обеспечивает пользовательский интерфейс, собирает входные данные, вызывает расчеты и отображает результаты.

**Взаимодействие:** `1_Calculator.py` импортирует данные из `data.py` и функции из `calculations.py`.
""")

# --- Диаграмма Mermaid ---
st.subheader("Схема взаимодействия")
st.code("""
graph TD
    User(👤 Пользователь) -- Ввод данных --> App[Интерфейс: 1_Calculator.py]
    App -- Вызов функций --> Calculations[Логика: calculations.py]
    Calculations -- Запрашивает данные --> Data[Данные: data.py]
    Data -- Возвращает данные --> Calculations
    Calculations -- Возвращает результат --> App
    App -- Отображает результат --> User
""", language="mermaid")

st.write("---")

# --- Раздел 2: Детализация модулей ---
st.header("2. Детальная Архитектура Модулей")

st.subheader("2.1. Модуль Данных (`data.py`)")
st.markdown("""
**Назначение:** Единое хранилище всех статических справочных данных, необходимых для расчетов. Это "база знаний" калькулятора.

**Содержимое:**
*   **Справочные таблицы (в виде словарей и списков):**
    *   `LOAD_COEFFICIENTS`: Коэффициенты режима работы ($K_p$) в зависимости от типа нагрузки.
    *   `MATERIAL_P0_CORRECTION_FACTORS`: Коэффициенты, корректирующие $P_0$ в зависимости от материала ремня.
    *   `P0_VALUES` и `P0_DATA_BY_V_RANGES`: Основная таблица номинальной мощности $P_0$ на один ремень для различных сечений по диапазонам окружной скорости.
    *   `CL_DATA`: Коэффициенты длины ремня ($C_L$) в зависимости от длины ремня.
    *   `CZ_DATA`: Коэффициенты количества ремней ($C_Z$) в зависимости от их количества.
    *   `STANDARD_PULLEY_DIAMETERS` и `STANDARD_BELT_LENGTHS`: Списки стандартных диаметров шкивов и длин ремней.
    *   `MIN_PULLEY_DIAMETERS`: Минимально допустимые диаметры шкивов для каждого профиля.

**Точки расширения:**
*   Включение узких профилей (SPA, SPB, SPC, 3V, 5V, 8V) с соответствующими таблицами данных.
*   Разделение данных по производителям и сериям ремней (через загрузку JSON/CSV-файлов).
*   Добавление данных для поликлиновых и зубчатых ремней.
""")

st.subheader("2.2. Модуль Расчетов (`calculations.py`)")
st.markdown("""
**Назначение:** Инкапсулирует всю математическую и инженерную логику калькулятора. Полностью независим от пользовательского интерфейса.

**Содержимое (ключевые функции):**
*   `calculate_design_power(P, Kp)`: Вычисляет расчетную мощность $P_{расч} = P \\times K_p$.
*   `determine_belt_section(P_design, n1_rpm)`: Определяет рекомендуемое сечение ремня (A, B, C...) по расчетной мощности.
*   `find_nearest_standard_value(...)`: Находит ближайшее стандартное значение в списке (для шкивов и длин ремней).
*   `calculate_belt_length(a, d1, d2)`: Вычисляет теоретическую длину ремня по геометрической формуле.
*   `calculate_actual_center_distance(Lp, d1, d2)`: Вычисляет уточненное межосевое расстояние по стандартной длине ремня.
*   `calculate_belt_speed(n1, d1)`: Вычисляет окружную скорость ремня $V = (\\pi \\cdot d_1 \\cdot n_1) / 60000$.
*   `get_p0_value(...)`: Возвращает номинальную мощность $P_0$ одного ремня, учитывая скорость и материал.
*   `calculate_angle_of_wrap(a, d1, d2)`: Вычисляет угол обхвата меньшего шкива.
*   `get_cl_value(...)`, `get_calpha_value(...)`, `get_cz_value(...)`: Возвращают поправочные коэффициенты $C_L$, $C_{\\alpha}$, $C_Z$ из таблиц.
*   `calculate_number_of_belts(...)`: Выполняет итоговый расчет требуемого количества ремней с итеративным уточнением $C_Z$.

**Точки расширения:**
*   Реализация более сложной логики выбора шкивов (например, с оптимизацией по габаритам или стоимости).
*   Добавление расчетов натяжения ремней и силы на вал.
*   Добавление расчета долговечности (ресурса) ремня.
*   Оптимизация подбора (например, поиск наиболее компактного или экономичного решения из нескольких возможных).
""")

st.subheader("2.3. Модуль Приложения/Интерфейса (`1_Калькулятор.py`)")
st.markdown("""
**Назначение:** Точка входа в приложение. Ответственен за взаимодействие с пользователем, сбор данных, вызов расчетных функций и наглядное представление результатов.

**Содержимое:**
*   **Импорты:** `streamlit`, все необходимые функции из `calculations.py` и данные из `data.py`.
*   **Конфигурация страницы:** `st.set_page_config` для заголовка, иконки и макета.
*   **Заголовок и описание:** `st.title`, `st.header`, `st.markdown`.
*   **Раздел ввода данных:**
    *   Использование виджетов `st.number_input`, `st.selectbox`, `st.radio` для сбора входных параметров от пользователя (мощность, обороты, межосевое расстояние, тип нагрузки, материал ремня).
*   **Кнопка расчета:** `st.button("Выполнить расчет")`.
*   **Логика обработки ввода и вызова расчетов:**
    *   При нажатии кнопки, весь код выполняется внутри блока `if`.
    *   Происходит последовательный вызов функций из `calculations.py` для выполнения всех этапов расчета.
    *   Используются `try...except` блоки для отлова и отображения возможных ошибок расчета.
*   **Раздел вывода результатов:**
    *   Использование `st.write`, `st.markdown`, `st.success`, `st.warning`, `st.error` для форматированного отображения всех полученных результатов и сообщений.

**Точки расширения:**
*   Реализация различных режимов работы (например, "упрощенный" и "экспертный").
*   Динамический выбор производителя и серии ремней в интерфейсе.
*   Визуализация привода (простая схема шкивов и ремней с помощью `matplotlib` или `plotly`).
*   Возможность сохранения отчета о расчете в PDF.
""")

st.write("---")

# --- Раздел 3 и 4: Взаимодействие и технологии ---
st.header("3. Используемые технологии")
st.markdown("""
*   **Python:** Основной язык программирования.
*   **Streamlit:** Фреймворк для быстрого создания интерактивного веб-интерфейса.
*   **Стандартная библиотека `math`:** Для математических операций (`pi`, `sqrt`, `ceil` и др.).
*   **Базовые структуры данных:** Словари и списки для хранения и обработки справочных данных.
""")

st.info("Эта модульная архитектура обеспечивает хорошую читаемость, простоту поддержки и легкость дальнейшего расширения функционала приложения.")

