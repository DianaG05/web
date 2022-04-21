import datetime
from flask import Flask, render_template, g, request
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import redirect

SECRET_KEY = 'yandexlyceum_secret_key'
DEBUG = True
DATABASE = ''

app = Flask(__name__)

app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)


class UserLogin:  # для входа в аккаунт
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonimous(self):
        return False

    def get_id(self):
        return str(self.__user['id'])


@login_manager.user_loader
def load_user(user_id):
    global dbase
    print('load_user')
    return UserLogin().fromDB(user_id, dbase)


# действия с базой данных
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()

    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
    db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


# класс для работы с базой данных
class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def addUser(self, name, e_mail, hash, type_reg, info_dop):  # добавление в базу данных пользователя
        try:
            if type_reg == 'Ученик':
                self.__cur.execute(f"SELECT COUNT() as 'count' FROM users WHERE email LIKE '{e_mail}'")
                res = self.__cur.fetchone()
                if res['count'] > 0:
                    print('такой пользователь есть')
                    return False
                self.__cur.execute("INSERT INTO users(name, email, password, dop_info, type_reg) VALUES(?, ?, ?, ?, ?)",
                                   (name, e_mail, hash, info_dop, type_reg))

            elif type_reg == 'Компания':
                self.__cur.execute(f"SELECT COUNT() as 'count' FROM users WHERE email LIKE '{e_mail}'")
                res = self.__cur.fetchone()
                if res['count'] > 0:
                    print('такой пользователь есть')
                    return False
                self.__cur.execute(
                    "INSERT INTO users(name, email, password, dop_info, type_reg) VALUES(?, ?, ?, ?, ?)",
                    (name, e_mail, hash, info_dop, type_reg))

            elif type_reg == 'Администратор':
                self.__cur.execute(f"SELECT COUNT() as 'count' FROM users WHERE email LIKE '{e_mail}'")
                res = self.__cur.fetchone()
                if res['count'] > 0:
                    print('такой пользователь есть')
                    return False
                self.__cur.execute("INSERT INTO users(name, email, password, type_reg) VALUES(?, ?, ?, ?)",
                                   (name, e_mail, hash, type_reg))
            self.__db.commit()
        except sqlite3.Error as e:
            print('ошибка добавления в базу данных', str(e))
            return False
        return True

    def addProject(self, name_project, name_company, dates, about, fail):  # добавление в бд проекта
        try:
            self.__cur.execute(
                "INSERT INTO projects(name_project, name_company_creat, dates, about, fail, show_yes_or_not) VALUES(?, ?, ?, ?, ?, ?)",
                (name_project, name_company, dates, about, fail, 0))
            self.__db.commit()
        except sqlite3.Error as e:
            print('ошибка добавления в базу данных', str(e))
            return False
        return True

    def getUser(self, user_id):  # получение пользователя по id
        try:
            self.__cur.execute(f'SELECT * FROM users WHERE id = {user_id} LIMIT 1')
            res = self.__cur.fetchone()
            print('getuser res:', res)
            if not res:
                print('Пользователь не найден')
                return False
            return res
        except sqlite3.Error as e:
            print('ошибка поиска в базу данных', str(e))
        return False

    def getUserByEmail(self, email):  # получение данных при входе по email
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            print('getuserbyemail:', res)
            if not res:
                print('Пользователь не найден')
                return False
            print('в getuserbyemail', res)
            return res

        except sqlite3.Error as e:
            print('ошибка поиска в базу данных', str(e))
        return False

    def getlist_project_no(self):  # отображение проектов в админе (не одобренные)
        self.__cur.execute(f'SELECT * FROM projects WHERE show_yes_or_not = 0')
        res = self.__cur.fetchall()
        if not res:
            return []
        else:
            return res

    def getlist_project_ok(self):  # отображение проектов в ученике
        self.__cur.execute(f'SELECT * FROM projects WHERE show_yes_or_not = 1')
        res = self.__cur.fetchall()
        if not res:
            return []
        else:
            return res

    def show_profile(self, id):  # показ профиля
        self.__cur.execute(f'SELECT * FROM users WHERE id = {id} LIMIT 1')
        res = self.__cur.fetchone()
        print(res)
        if not res:
            print('ошибка')
        else:

            return res

    def show(self, id):  # показ проекта подробно
        self.__cur.execute(f'SELECT * FROM projects WHERE id = {id} LIMIT 1')
        res = self.__cur.fetchone()
        if not res:
            print('ошибка')
        else:
            return res

    def delete(self, id):  # удаление проекта
        self.__cur.execute(f'DELETE from projects WHERE id = {id}')
        self.__db.commit()

    def ok(self, id):  # одобрение проекта
        self.__cur.execute(f'UPDATE projects SET show_yes_or_not = 1 WHERE id = {id}')
        self.__db.commit()

    def subs(self, id):  # подписка не сделана
        global id_us
        try:
            id_user = current_user.get_id()
            print(id_user, id_us)
            self.__cur.execute(f"SELECT * FROM users WHERE id = ? LIMIT 1", (id_us,))
            res = self.__cur.fetchall()
            print('подписаться на проект', res)

            if res:
                f = res.split(';')
                if str(id) not in f:
                    f.append(str(id))
                    list_id_project = ';'.join(f)

                    self.__cur.execute(
                        f"UPDATE users SET project_story='{list_id_project}' WHERE id='{id_us}'")
            else:
                print(4, id_us, id)
                self.__cur.execute(f"UPDATE users SET project_story='{str(id)}' WHERE id='{id_us}'")
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            print('ошибка в базу данных', str(e))
        return False

    def nosubs(self, id):  # подписка сделана
        try:
            self.__cur.execute(f'SELECT project_story FROM users id = {current_user.get_id()}')
            res = self.__cur.fetchone()
            if res:
                f = res.split(';')
                if str(id) in f:
                    del f[f.index(str(id))]
                    list_id_project = ';'.join(f)
                    self.__cur.execute(
                        f'UPDATE users SET project_story = {list_id_project} WHERE id = {current_user.get_id()}')

            self.__db.commit()
        except sqlite3.Error as e:
            print('ошибка в базу данных', str(e))

    def show_pr_profail(self, el):  # показ название проекта по id
        try:
            self.__cur.execute(f'SELECT name_project FROM projects WHERE id = {el} LIMIT 1')
            res = self.__cur.fetchone()
            print('показ название проекта по id', res)
            return str(res)
        except sqlite3.Error as e:
            print('ошибка  данных', str(e))

    def getlist_project_ok_company(self):  # показ проекта по имени компании
        global id_us
        try:
            self.__cur.execute('SELECT name FROM users WHERE id = ?', (id_us,))
            name = self.__cur.fetchone()
            print('getlist_project_ok_company name', name)
            self.__cur.execute(f'SELECT * FROM projects WHERE show_yes_or_not = 1 and name_company_creat = ?',
                               (str(name)))
            res = self.__cur.fetchall()
            print('getlist_project_ok_company res', res)
            if not res:
                return []
            else:
                return res

        except sqlite3.Error as e:
            print('ошибка  данных', str(e))
            return []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/secret_reg_for_admin_ds', methods=['POST', 'GET'])
def secret_reg():
    if request.method == 'POST':
        name = request.form['name']
        e_mail = request.form['email']
        Password = request.form['Password']
        Password2 = request.form['Password2']
        type_reg = 'Администратор'
        info_dop = ''

        if Password == Password2 and len(Password) > 5:
            hash = generate_password_hash(Password)
            res = dbase.addUser(name, e_mail, hash, type_reg, info_dop)
            if res:
                return redirect('/door')
    return render_template('secret_reg.html')


id_us = 0


@app.route('/door', methods=['POST', 'GET'])
def door():
    global id_us
    if request.method == "POST":
        try:
            password = request.form['password']
            e_mail = request.form['email']
            type_reg = request.form['type_reg']

            user = dbase.getUserByEmail(e_mail)
            id_us = user[0]
            print(id_us, type_reg)  # проверка нашёл ли id

            if user and check_password_hash(user['password'], password):
                userlogin = UserLogin().create(user)
                rm = True if request.form.get('remainme') else False
                login_user(userlogin, remember=rm)
                if type_reg == 'Администратор':
                    return redirect('/show_project_for_approval')
                elif type_reg == 'Ученик':
                    return redirect('/show_project_for_student')
                elif type_reg == 'Компания':
                    return redirect('/show_project_for_company')
        except:
            print('не удалось войти')

    return render_template('door.html')


@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        name = request.form['nps']
        e_mail = request.form['e_mail']
        Password = request.form['Password']
        Password2 = request.form['Password2']
        type_reg = request.form['type_reg']
        info_dop = request.form['info_dop']

        if Password == Password2 and len(Password) > 5:
            hash = generate_password_hash(Password)
            res = dbase.addUser(name, e_mail, hash, type_reg, info_dop)
            if res:
                pass
        else:
            return redirect('/door')

    return render_template('registration.html')


@app.route('/create_project', methods=['POST', 'GET'])
# @login_required
def create_project():
    try:
        if request.method == 'POST':
            name_project = request.form['name_project']
            name_company = request.form['name_company']
            dates = datetime.date.today()
            about = request.form['about']
            fail = request.form['fail']
            if name_project != '' and name_company != '' and about != '' and fail != '':
                res = dbase.addProject(name_project, name_company, dates, about, fail)
                return redirect('/show_project_for_company')

        return render_template('creat_project.html')
    except:
        redirect('/door')


@app.route('/show_project_for_approval')
# @login_required
def show_project_for_approval():
    res = dbase.getlist_project_no()

    return render_template('show_project_admin.html', project_t=res)


@app.route('/show_project_for_student')
# @login_required
def show_project_for_student():
    res = dbase.getlist_project_ok()
    return render_template('show_project_student.html', project_t2=res)


@app.route('/projects/<int:id>/sub')
# @login_required
def show_project_sub(id):
    try:
        el = dbase.subs(str(id))
        if el:
            return redirect('/show_project_for_student')
    except:
        redirect('/door')


@app.route('/projects/<int:id>/nosub')
# @login_required
def show_project_nosub(id):
    try:
        el = dbase.nosubs(str(id))
        if el:
            return redirect('/show_project_for_student')
    except:
        redirect('/door')


@app.route('/show_project_for_company')
# @login_required
def show_project_for_company():
    try:
        res = dbase.getlist_project_ok_company()
        return render_template('project_for_company.html', project_t3=res)
    except:
        redirect('/door')


@app.route('/project/<int:id>')  # показ проекта подробно
# @login_required
def show_project(id):
    try:
        show = dbase.show(id)
        print(show)
        return render_template('show_project.html', name=show[1], about=show[5], name_company=show[2],
                               dates=show[4], fail=show[6])
    except:
        redirect('/door')


@app.route('/project/<int:id>/ok')
# @login_required
def show_project_ok(id):
    dbase.ok(id)
    return redirect('/show_project_for_approval')


@app.route('/project/<int:id>/no')
# @login_required
def show_project_no(id):
    dbase.delete(id)

    return redirect('/show_project_for_approval')


@app.route('/profile')
def profile():
    global id_us
    try:
        show = dbase.show_profile(id_us)
        if show[5]:
            res_5 = list()
            f = str(show[5]).split(';')
            for el in f:
                res_k = dbase.show_pr_profail(el)
                res_5.append(res_k)
            print(res_5)
            res_5 = '; '.join(res_5)

        else:
            res_5 = 'Нет проектов'

        return render_template('profile.html', name=show[1], dop_info=show[4], email=show[2],
                               type_reg=show[6], project_story=res_5)
    except:
        redirect('/door')


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


dbase = None


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


if __name__ == "__main__":
    app.run(debug=True)
