from flask import Flask, render_template, request, redirect, url_for, session as f_session
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
import random
import os


app = Flask(__name__)
app.secret_key = os.environ.get('COCKTAILS_FLASK_KEY')
ENV = 'prod'

if ENV == 'dev':
    password = os.environ.get('POSTGRE_PASS')
    app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://postgres:{password}@localhost:5432/cocktailpg'
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')


db = SQLAlchemy(app)
table_names = db.engine.table_names()
Base = automap_base()
Base.prepare(db.engine, reflect=True)


cocktails = Base.classes.cocktails
garnishes = Base.classes.garnishes
ingredients = Base.classes.ingredients
users = Base.classes.users


def delete_user_cocktail(cocktail_name):
    user = db.session.query(users).filter(users.username == f_session['username'])[0]
    cocktail = db.session.query(cocktails).filter(cocktails.name == cocktail_name)[0]
    user.cocktails_collection.remove(cocktail)
    db.session.commit()


def get_user_cocktails():
    user = db.session.query(users).filter(users.username == f_session['username'])[0]
    return user.cocktails_collection


def display_cocktail(chosen):  # return list of lists which can be formatted into the html template
    main_items = [chosen.name, chosen.glass, chosen.prep]
    chosen_garnishes = [g.name for g in chosen.garnishes_collection]
    chosen_ingredients = [i.name for i in chosen.ingredients_collection]
    cocktail_info = [main_items, chosen_garnishes, chosen_ingredients]
    return cocktail_info


def random_cocktail():
    cocktail_query = db.session.query(cocktails).all()
    chosen = random.choice(cocktail_query)
    cocktail_info = display_cocktail(chosen)
    return cocktail_info


def search_validity(user_input):
    if len(user_input) < 3:
        return False
    return True


def name_search_results(user_input):
    cocktail_query = db.session.query(cocktails).filter(func.lower(cocktails.name).contains(user_input)).all()
    ingredient_query = db.session.query(ingredients).filter(func.lower(ingredients.name).contains(user_input)).all()
    garnish_query = db.session.query(garnishes).filter(func.lower(garnishes.name).contains(user_input)).all()
    result_names = []
    for cocktail in cocktail_query:
        result_names.append(cocktail.name)
    for ingredient in ingredient_query:
        query = db.session.query(cocktails).filter(cocktails.ingredients_collection.contains(ingredient)).all()
        for cocktail in query:
            result_names.append(cocktail.name)
    for garnish in garnish_query:
        query = db.session.query(cocktails).filter(cocktails.garnishes_collection.contains(garnish)).all()
        for cocktail in query:
            result_names.append(cocktail.name)
    return result_names


def selection_query(selection):
    query = db.session.query(cocktails).filter(cocktails.name == selection).all()
    chosen = query[0]
    cocktail_info = display_cocktail(chosen)
    return cocktail_info


def check_for_user(input_username, input_password):
    user_query = db.session.query(users).all()
    for user in user_query:
        if user.__dict__['username'] == input_username and user.__dict__['password'] == input_password:
            return True
    return False


def user_store_cocktail(cocktail_name):
    user = db.session.query(users).filter(users.username == f_session['username'])[0]
    cocktail = db.session.query(cocktails).filter(cocktails.name == cocktail_name)[0]
    user.cocktails_collection.append(cocktail)
    db.session.commit()


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if f_session['login_success']:
        username = f_session['username']
        if request.method == 'POST':
            if request.form.get('search'):
                if search_validity(request.form['search']):
                    names = name_search_results(request.form['search'])
                    return render_template("profile.html", names=names, username=username)
                else:
                    return render_template("profile.html", username=username)
            if request.form.get('select') or request.form.get('random'):
                if request.form.get('select'):
                    cocktail = selection_query(request.form['select'])
                    f_session['last_displayed'] = cocktail
                else:
                    cocktail = random_cocktail()
                    f_session['last_displayed'] = cocktail
            if request.form.get('store'):
                cocktail = f_session['last_displayed']
                cocktail_name = cocktail[0][0]
                user_store_cocktail(cocktail_name)
            return render_template("profile.html", content=cocktail, username=username)
    return render_template("profile.html", username=username)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            if check_for_user(username, password):
                f_session['login_success'] = True
                f_session['username'] = username
                return redirect(url_for('profile'))
            else:
                return redirect(url_for('login'))
    return render_template("login.html")


@app.route('/profile/logout')
def logout():
    f_session.clear() # f_session has all cached data and this clears it
    return redirect(url_for('login'))


@app.route('/stored', methods=['GET', 'POST'])
def stored():
    if f_session['login_success']:
        if request.method == 'POST':
            if request.form.get('delete-one'):
                to_delete = request.form.getlist('delete-one')
                for cocktail in to_delete:
                    delete_user_cocktail(cocktail_name=cocktail)
        cocktails = get_user_cocktails()
        if request.form.get('delete'):
            return render_template("stored.html", cocktails=cocktails, delete_mode=True)
        else:
            return render_template("stored.html", cocktails=cocktails)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'new_username' in request.form and 'new_password' in request.form:
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            if len(new_username) > 0 and len(new_password) > 0:
                new_user = users(username=new_username, password=new_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("login"))
    return render_template("register.html")


# if __name__ == '__main__':
#     app.run()
