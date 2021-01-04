import sqlite3
import pandas

COCKTAILS_CSV = r"C:\python_course\coctkails_project\cocktails.csv"

cocktails = pandas.read_csv(COCKTAILS_CSV)
cocktails.columns = [c.replace(' ', '_') for c in
                     cocktails.columns]  # this changes cocktail name to cocktail_name so that is can be called (cocktail.cocktail_name)

# print(cocktails[['Cocktail_Name', 'Ingredients', 'Garnish', 'Glassware', 'Preparation']])

db = sqlite3.connect("C:\python_course\coctkails_project\cocktails.db")

cursor = db.cursor()


def double_apostrophe(string):
    final = ''
    for c in string:
        if c == "'":
            final += "'" * 2
        else:
            final += c
    return final


def create_db():
    create_commands = """CREATE TABLE IF NOT EXISTS cocktail_garnishes
    (
      cocktail_id INTEGER,
      garnish_id    INTEGER,
      FOREIGN KEY(cocktail_id) REFERENCES cocktails(id)
      FOREIGN KEY(garnish_id) REFERENCES garnishes(id)
    );
    
    CREATE TABLE IF NOT EXISTS cocktail_ingredients
    (
      cocktail_id INTEGER,
      ingredient_id    INTEGER,
      FOREIGN KEY(cocktail_id) REFERENCES cocktails(id)
      FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
    );
    
    CREATE TABLE IF NOT EXISTS cocktails
    (
      id        INTEGER,
      name      TEXT NOT NULL,
      glass     TEXT,
      prep      TEXT,
      PRIMARY KEY (id)
    );
    
    CREATE TABLE IF NOT EXISTS garnishes
    (
      id   INTEGER,
      name TEXT NOT NULL,
      PRIMARY KEY (id)
    );
    
    CREATE TABLE IF NOT EXISTS ingredients
    (
      id   INTEGER,
      name TEXT NOT NULL,
      PRIMARY KEY (id)
    );"""

    cursor.executescript(create_commands)


def initial_table_insert(dataset, table_name):
    for ele in dataset:
        ele = ele.strip()
        db.execute(f"INSERT INTO {table_name} VALUES (:id, :name)", {'id': None, 'name': ele})
        db.commit()


def normalize_rows(column):
    item_set = set()
    for row in column:
        if type(row) != float:
            list_row = row.split(',')
            if len(list_row) == 1:
                item_set.add(row)
            else:
                for ele in list_row:
                    item_set.add(ele)
    return item_set


def insert_data_into_cocktails():
    for n in cocktails.Cocktail_Name:
        cursor.execute('INSERT INTO cocktails VALUES (:id, :name, :glass, :prep)',
                       {'id': None, 'name': n, 'glass': None, 'prep': None})
        db.commit()
    current_id = 1
    for g in cocktails.Glassware:
        cursor.execute(f'UPDATE cocktails SET glass = :glass WHERE id = :id', {'glass': g, 'id': current_id})
        db.commit()
        current_id += 1
    current_id = 1
    for p in cocktails.Preparation:
        cursor.execute(f'UPDATE cocktails SET prep = :prep WHERE id = :id', {'prep': p, 'id': current_id})
        db.commit()
        current_id += 1


def insert_cocktail_garnishes():
    current_id = 1
    for garnish in cocktails.Garnish:
        if type(garnish) != float:
            garnish_list = garnish.split(',')
            for ele in garnish_list:
                if "'" in ele:
                    ele = double_apostrophe(string=ele)
                ele = f" '{ele.strip()}' "
                cursor.execute(f'''SELECT id from garnishes WHERE name = {ele}; ''')
                garnish_id = cursor.fetchone()[0]
                cursor.execute('INSERT INTO cocktail_garnishes VALUES (:cocktail_id, :garnish_id)',
                               {'cocktail_id': current_id, 'garnish_id': garnish_id})
                db.commit()
        current_id += 1


def insert_cocktail_ingredients():
    current_id = 1
    for ingredient in cocktails.Ingredients:
        if type(ingredient) != float:
            ingredient_list = ingredient.split(',')
            for ele in ingredient_list:
                if "'" in ele:
                    ele = double_apostrophe(string=ele)
                ele = f" '{ele.strip()}' "
                cursor.execute(f'''SELECT id from ingredients WHERE name = {ele}; ''')
                ingredient_id = cursor.fetchone()[0]
                cursor.execute('INSERT INTO cocktail_ingredients VALUES (:cocktail_id, :ingredient_id)',
                               {'cocktail_id': current_id, 'ingredient_id': ingredient_id})
                db.commit()
        current_id += 1


def add_user_tables():
    print('running')
    create_commands = '''CREATE TABLE saved_cocktails
    (
      user_id     INTEGER,
      cocktail_id INTEGER,
      FOREIGN KEY(user_id) REFERENCES users(id)
      FOREIGN KEY(cocktail_id) REFERENCES cocktails(id)
    );
    
    CREATE TABLE users
    (
      id       INTEGER,
      username TEXT,
      password TEXT,
      PRIMARY KEY (id)
    );'''

    cursor.executescript(create_commands)
    db.commit()


# create_db()
# initial_table_insert(dataset=normalize_rows(column=cocktails.Garnish), table_name='garnishes')
# initial_table_insert(dataset=normalize_rows(column=cocktails.Ingredients), table_name='ingredients')
# insert_data_into_cocktails()
# insert_cocktail_garnishes()
# insert_cocktail_ingredients()
# add_user_tables()
db.close()
