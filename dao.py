import db

# ---------------------------------------------------------
# 1. DAO для Категорий
# ---------------------------------------------------------
class CategoryDAO:
    @staticmethod
    def get_all():
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def insert(name):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def update(cat_id, name):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE categories SET name = ? WHERE id = ?", (name, cat_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(cat_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()

# ---------------------------------------------------------
# 2. DAO для Ингредиентов
# ---------------------------------------------------------
class IngredientDAO:
    @staticmethod
    def get_all():
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, unit FROM ingredients ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def insert(name, unit):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO ingredients (name, unit) VALUES (?, ?)", (name, unit))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def update(ing_id, name, unit):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE ingredients SET name = ?, unit = ? WHERE id = ?", (name, unit, ing_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(ing_id):
        conn = db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM ingredients WHERE id = ?", (ing_id,))
            conn.commit()
        except db.sqlite3.IntegrityError:
            # Срабатывает ограничение ON DELETE RESTRICT
            raise Exception("Нельзя удалить ингредиент, так как он используется в рецептах!")
        finally:
            conn.close()

# ---------------------------------------------------------
# 3. DAO для Рецептов
# ---------------------------------------------------------
class RecipeDAO:
    @staticmethod
    def get_all(search_text="", category_id=None):
        conn = db.get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT r.id, r.title, c.name as category_name, r.default_servings 
            FROM recipes r
            LEFT JOIN categories c ON r.category_id = c.id
            WHERE 1=1
        """
        params = []
        
        if search_text:
            query += " AND r.title LIKE ?"
            params.append(f"%{search_text}%")
            
        if category_id:
            query += " AND r.category_id = ?"
            params.append(category_id)
            
        query += " ORDER BY r.title"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_by_id(recipe_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def insert(title, description, category_id, servings, ingredients_list):
        conn = db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO recipes (title, description, category_id, default_servings) VALUES (?, ?, ?, ?)",
                (title, description, category_id, servings)
            )
            recipe_id = cur.lastrowid
            
            for ing_id, amount in ingredients_list:
                cur.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount) VALUES (?, ?, ?)",
                    (recipe_id, ing_id, amount)
                )
            conn.commit()
            return recipe_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update(recipe_id, title, description, category_id, servings, ingredients_list):
        """Обновляет рецепт и полностью перезаписывает его состав."""
        conn = db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE recipes SET title = ?, description = ?, category_id = ?, default_servings = ? WHERE id = ?",
                (title, description, category_id, servings, recipe_id)
            )
            
            cur.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
            
            for ing_id, amount in ingredients_list:
                cur.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount) VALUES (?, ?, ?)",
                    (recipe_id, ing_id, amount)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete(recipe_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        conn.close()

# ---------------------------------------------------------
# 4. DAO для Состава рецепта и Генерации списка покупок
# ---------------------------------------------------------
class RecipeIngredientDAO:
    @staticmethod
    def get_by_recipe(recipe_id):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id, i.name, i.unit, ri.amount
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.id = ri.ingredient_id
            WHERE ri.recipe_id = ?
            ORDER BY i.name
        """, (recipe_id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def generate_shopping_list(recipes_data):
        if not recipes_data:
            return []

        conn = db.get_connection()
        cur = conn.cursor()
        
        unions = []
        params = []
        
        for item in recipes_data:
            unions.append("SELECT ? AS recipe_id, ? AS target_servings")
            params.extend([item['id'], item['servings']])
            
        union_sql = " UNION ALL ".join(unions)
        
        query = f"""
            SELECT i.name, i.unit, SUM(ri.amount * (s.target_servings * 1.0 / r.default_servings)) AS total_amount
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.id = ri.ingredient_id
            JOIN recipes r ON r.id = ri.recipe_id
            JOIN ({union_sql}) s ON s.recipe_id = ri.recipe_id
            GROUP BY i.id, i.name, i.unit
            ORDER BY i.name
        """
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows