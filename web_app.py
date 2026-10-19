from flask import Flask, render_template, request
import db
import dao
import recipe_api

app = Flask(__name__)

@app.route('/')
def index():
    search = request.args.get('search', '')
    cat_id = request.args.get('category_id', type=int)
    recipes = dao.RecipeDAO.get_all(search_text=search, category_id=cat_id)
    categories = dao.CategoryDAO.get_all()
    return render_template('index.html', recipes=recipes, categories=categories, search=search, selected_cat=cat_id)

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = dao.RecipeDAO.get_by_id(recipe_id)
    ingredients = dao.RecipeIngredientDAO.get_by_recipe(recipe_id)
    return render_template('recipe.html', recipe=recipe, ingredients=ingredients)

@app.route('/recipe/<int:recipe_id>/web')
def recipe_from_web(recipe_id):
    # Получаем название нашего рецепта из БД
    recipe = dao.RecipeDAO.get_by_id(recipe_id)
    if not recipe:
        return "Рецепт не найден", 404
    
    # Ищем его в интернете
    web_data = recipe_api.search_meal_by_name(recipe["title"])
    
    return render_template('web_recipe.html', recipe=recipe, web_data=web_data)

@app.route('/shopping', methods=['GET', 'POST'])
def shopping():
    recipes = dao.RecipeDAO.get_all()
    shopping_list = []
    if request.method == 'POST':
        selected_ids = request.form.getlist('recipe_ids')
        if selected_ids:
            recipes_data = []
            for r_id in selected_ids:
                servings = int(request.form.get(f'servings_{r_id}', 1))
                recipes_data.append({'id': int(r_id), 'servings': servings})
            shopping_list = dao.RecipeIngredientDAO.generate_shopping_list(recipes_data)
    return render_template('shopping.html', recipes=recipes, shopping_list=shopping_list)

if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
