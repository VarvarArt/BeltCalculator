# debug_pdf.py
import fitz

PDF_PATH = "catalog.pdf"
# Давайте посмотрим на страницу 24 (индекс 23), где должна быть таблица для профиля "C"
PAGE_TO_INSPECT = 23

print(f"--- Анализирую текст на странице {PAGE_TO_INSPECT + 1} файла {PDF_PATH} ---")

try:
    with fitz.open(PDF_PATH) as doc:
        page = doc[PAGE_TO_INSPECT]
        text = page.get_text("text") # Извлекаем текст

        # Печатаем весь извлеченный текст
        print("="*50)
        print(text)
        print("="*50)

except Exception as e:
    print(f"Произошла ошибка: {e}")

print("--- Анализ завершен ---")