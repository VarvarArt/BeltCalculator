import fitz
import pandas as pd
import os

PDF_PATH = "catalog.pdf"
OUTPUT_DIR = "parsed_data"

def main():
    print("===== Парсер таблицы через find_tables() (v16) =====")
    page_num = 39  # 40 в просмотрщике = 39 в PyMuPDF
    with fitz.open(PDF_PATH) as doc:
        page = doc[page_num]
        tabs = page.find_tables()
        if not tabs.tables:
            print("Таблица не найдена методом find_tables()!")
            return
        # Извлечь первую таблицу
        table = tabs.tables[0]
        table_data = table.extract()
        df = pd.DataFrame(table_data)
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output_filename = f"{OUTPUT_DIR}/power_data_C_Pb_findtables.csv"
        df.to_csv(output_filename, index=False, header=False)
        print(f"УСПЕШНО: Таблица извлечена методом find_tables().")
        print(f"Файл сохранен: {output_filename}")

if __name__ == "__main__":
    main()
