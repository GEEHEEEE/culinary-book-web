import pandas as pd
import os
import re

DATASET_PATH = "rurecipes.parquet"
df = None

if os.path.exists(DATASET_PATH):
    print("Загрузка русского датасета рецептов...")
    try:
        df = pd.read_parquet(DATASET_PATH)
        print(f"Успешно загружено {len(df)} рецептов.")
    except Exception as e:
        print(f"Ошибка загрузки датасета: {e}")
else:
    print("Внимание: файл rurecipes.parquet не найден!")

def extract_equipment(text):
    if not text: return ""
    text = text.lower()
    equipment_keywords = {
        "духовк": "Духовка", "печь": "Печь", "печк": "Печь",
        "сковород": "Сковорода", "кастрюл": "Кастрюля", "казан": "Казан",
        "блендер": "Блендер", "миксер": "Миксер", "мясорубк": "Мясорубка",
        "мультиварк": "Мультиварка", "микроволнов": "Микроволновка",
        "плит": "Плита"
    }
    found = set()
    for keyword, name in equipment_keywords.items():
        if keyword in text:
            found.add(name)
    return ", ".join(sorted(found))

def search_meals_by_name(meal_name):
    """Ищет ВСЕ рецепты по запросу и возвращает список."""
    if df is None: return []
    
    search_query = meal_name.lower().strip()
    name_col = 'name' if 'name' in df.columns else 'title'
    
    # Ищем все совпадения
    matches = df[df[name_col].str.lower().str.contains(search_query, na=False)]
    
    # Берем первые 20 результатов (чтобы страница не тормозила)
    results = []
    for _, recipe in matches.head(20).iterrows():
        ingredients_raw = recipe.get('ingredients', [])
        if isinstance(ingredients_raw, str):
            ingredients_list = [i.strip() for i in ingredients_raw.split('\n') if i.strip()]
        else:
            ingredients_list = [str(i) for i in ingredients_raw]

        instructions = recipe.get('instructions', '')
        equipment = extract_equipment(instructions)

        results.append({
            "name": recipe[name_col],
            "image": recipe.get('image_url', ''),
            "ingredients_display": ingredients_list,
            "ingredients_raw": ingredients_list,
            "instructions": instructions if instructions else "Инструкция не указана.",
            "equipment": equipment
        })
    return results
