import os
import csv

TEXT_DIR = "parsed_text"
TABLE_DIR = "parsed_tables"
IMG_DIR = "parsed_images"

# Ключевые слова для поиска в тексте и таблицах
KEYWORDS = [
    "power", "dimension", "diameter", "length", "coefficient", "factor", "wrap", "angle", "installation",
    "maintenance", "formula", "chart", "table", "selection", "standard", "min", "max", "rpm", "kw", "speed",
    "Pb", "Pd", "profile", "section", "belt", "pulley"
]

def scan_texts():
    print("=== Оглавление по текстовым страницам ===")
    for fname in sorted(os.listdir(TEXT_DIR)):
        if not fname.endswith(".txt"):
            continue
        with open(os.path.join(TEXT_DIR, fname), encoding="utf-8") as f:
            text = f.read().lower()
            found = [word for word in KEYWORDS if word in text]
            if found:
                print(f"{fname}: {', '.join(found)}")

def scan_tables():
    print("\n=== Оглавление по таблицам ===")
    for fname in sorted(os.listdir(TABLE_DIR)):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(TABLE_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = [next(reader) for _ in range(3)]  # первые 3 строки
                header = ' | '.join(rows[0]) if rows else ""
                row1 = ' | '.join(rows[1]) if len(rows) > 1 else ""
                row2 = ' | '.join(rows[2]) if len(rows) > 2 else ""
                # Простая эвристика: если в заголовке или первых строках есть ключевые слова или числа
                content = " ".join([header, row1, row2]).lower()
                found = [word for word in KEYWORDS if word in content]
                has_numbers = any(any(c.isdigit() for c in cell) for cell in rows[0])
                if found or has_numbers:
                    print(f"{fname}: {', '.join(found)}")
                    print(f"  Заголовок: {header}")
        except Exception as e:
            print(f"{fname}: ошибка чтения ({e})")

def scan_images():
    print("\n=== Оглавление по изображениям ===")
    for fname in sorted(os.listdir(IMG_DIR)):
        print(fname)

if __name__ == "__main__":
    scan_texts()
    scan_tables()
    scan_images()
