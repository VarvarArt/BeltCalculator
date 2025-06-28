import fitz
import os
import pandas as pd

PDF_PATH = "catalog.pdf"
TEXT_DIR = "parsed_text"
TABLE_DIR = "parsed_tables"
IMG_DIR = "parsed_images"

os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(TABLE_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

with fitz.open(PDF_PATH) as doc:
    for page_num in range(len(doc)):
        page = doc[page_num]

        # 1. Сохраняем текст страницы
        text = page.get_text("text")
        with open(f"{TEXT_DIR}/page_{page_num+1:03}.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # 2. Сохраняем все таблицы этой страницы (если есть)
        tables = page.find_tables()
        for t_idx, table in enumerate(tables.tables):
            table_data = table.extract()
            df = pd.DataFrame(table_data)
            df.to_csv(f"{TABLE_DIR}/page_{page_num+1:03}_table_{t_idx+1}.csv", index=False, header=False)

        # 3. Сохраняем все изображения этой страницы (если есть)
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            img_path = f"{IMG_DIR}/page_{page_num+1:03}_img_{img_idx+1}.png"
            if pix.n < 5:
                pix.save(img_path)
            else:
                pix0 = fitz.Pixmap(fitz.csRGB, pix)
                pix0.save(img_path)
                pix0 = None
            pix = None

print("Дамп каталога завершён!")
