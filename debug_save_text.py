# debug_save_text.py

import fitz  # PyMuPDF
import os

# --- НАСТРОЙКИ ---
PDF_PATH = "catalog.pdf"
OUTPUT_FILENAME = "parsed_data/debug_output.txt"
PAGES_TO_READ = [37, 38, 39, 40]  # Страницы 38, 39, 40, 41


def save_raw_text():
    """
    Читает текст с указанных страниц и сохраняет его в один файл
    для последующего анализа.
    """
    print("--- Запуск скрипта диагностики ---")

    if not os.path.exists(PDF_PATH):
        print(f"ОШИБКА: Файл '{PDF_PATH}' не найден.")
        return

    combined_text = ""
    print(f"Читаю страницы: {[p + 1 for p in PAGES_TO_READ]}")

    try:
        with fitz.open(PDF_PATH) as doc:
            for page_num in PAGES_TO_READ:
                if page_num < len(doc):
                    page = doc[page_num]
                    combined_text += f"--- СОДЕРЖИМОЕ СТРАНИЦЫ {page_num + 1} ---\n"
                    combined_text += page.get_text("text")
                    combined_text += "\n\n"
                else:
                    print(f"Предупреждение: Страница {page_num + 1} не найдена в PDF.")

        # Сохраняем весь извлеченный текст в файл
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(combined_text)

        print(f"\nУСПЕХ! Весь извлеченный текст сохранен в файл: {OUTPUT_FILENAME}")
        print("Пожалуйста, скопируйте содержимое этого файла и отправьте его для анализа.")

    except Exception as e:
        print(f"\nПроизошла критическая ошибка: {e}")


if __name__ == "__main__":
    save_raw_text()