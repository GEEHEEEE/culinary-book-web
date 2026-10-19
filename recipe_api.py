import requests
import time
from deep_translator import GoogleTranslator

def search_meal_by_name(meal_name):
    """Ищет рецепт в TheMealDB и переводит его с паузами."""
    try:
        translator = GoogleTranslator(source='auto', target='en')
        meal_name_en = translator.translate(meal_name)
        time.sleep(1) # ПАУЗА 1 СЕКУНДА

        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={meal_name_en}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if not data.get("meals"):
            return None

        meal = data["meals"][0]
        
        translator_ru = GoogleTranslator(source='en', target='ru')
        meal_name_ru = translator_ru.translate(meal["strMeal"])
        time.sleep(1) # ПАУЗА

        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")
            if ing and ing.strip():
                ing_ru = translator_ru.translate(ing)
                ingredients.append(f"{ing_ru} — {measure}")
                time.sleep(1) # ПАУЗА МЕЖДУ ИНГРЕДИЕНТАМИ

        instructions_ru = translator_ru.translate(meal["strInstructions"])

        return {
            "name": meal_name_ru,
            "image": meal["strMealThumb"],
            "ingredients": ingredients,
            "instructions": instructions_ru
        }
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None
