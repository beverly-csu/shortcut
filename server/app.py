import hashlib
import re
import time
from flask_cors import CORS
import requests
from flask import Flask, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
import jwt
import locale
from datetime import datetime, timedelta

CODE_SUCCESS = {'code': 1000}
CODE_ERROR_VALUE = {'code': 1300}
CODE_ERROR_TOKEN = {'code': 1301}
CODE_ERROR_DATA = {'code': 1302}
CODE_DATABASE_ERROR = {'code': 1500}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shcut.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cors = CORS(app, resources={r"/*": {"origins": "*"}})
db = SQLAlchemy(app)
SECRET_KEY = 'test'

locale.setlocale(locale.LC_TIME, "ru_RU.utf8")


class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(512), nullable=True)
    email = db.Column(db.String(64), unique=True)
    date_reg = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    token = db.Column(db.String(512))


class Links(db.Model):
    link_id = db.Column(db.Integer, primary_key=True)
    short_url = db.Column(db.String(128), unique=True)
    full_url = db.Column(db.String(512))
    title = db.Column(db.String(64))
    date_create = db.Column(db.DateTime, default=datetime.utcnow)
    access = db.Column(db.String(32))
    secret_code = db.Column(db.String(32))
    owner = db.Column(db.String(32))


class LinksAdditional(db.Model):
    link_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Text)
    redirects = db.Column(db.Text)


def debug(message):
    print('DEBUG: ', message)


def get_user_data(login):
    if available_login(login) is False:
        user_data = Users.query.filter_by(login=login).first()
        return {
            'code': 1000,
            'profile': {
                'login': login,
                'email': user_data.email,
                'date_reg': user_data.date_reg,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name
            },
        }
    else:
        return CODE_ERROR_VALUE


def get_profile(login):
    if available_login(login) is False:
        user_data = Users.query.filter_by(login=login).first()
        return {
            'code': 1000,
            'login': login,
            'full_name': user_data.first_name + " " + user_data.last_name,
            'email': user_data.email,
            'date_reg': time.strftime('%d %B %Y %H:%M', datetime.timetuple(user_data.date_reg))
        }
    else:
        return CODE_ERROR_VALUE


def available_short(url):
    try:
        status = Links.query.filter_by(short_url=url).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def available_login(login):
    try:
        status = Users.query.filter_by(login=login).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def available_email(email):
    try:
        status = Users.query.filter_by(email=email).all()
        if len(status) == 0:
            return True
        else:
            return False
    except Exception as error:
        debug(error)
        return False


def get_user(login):
    try:
        user_data = Users.query.filter_by(login=login).first()
        user_data = dict(
            code=1000,
            login=user_data.login,
            email=user_data.email,
            password=user_data.password
        )
        return user_data
    except Exception as error:
        debug(error)
        return CODE_DATABASE_ERROR


def create_user(data):
    try:
        if available_login(data['login']) and available_email(data['email']):
            user_instance = Users(login=data['login'], password=data['password'], email=data['email'],
                                  first_name=data['first_name'], last_name=data['last_name'])
            db.session.add(user_instance)
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def update_user(login, data):
    try:
        if available_login(login) is False:
            Users.query.filter_by(login=login).update(
                dict(password=data['password'], first_name=data['first_name'], last_name=data['last_name']))
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def delete_user(login):
    try:
        if available_login(login) is False:
            Users.query.filter_by(login=login).delete()
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def delete_link(login, link_id):
    try:
        link_data = Links.query.filter_by(link_id=link_id).first()
        if link_data.owner == login:
            Links.query.filter_by(link_id=link_id).delete()
            LinksAdditional.query.filter_by(link_id=link_id).delete()
            db.session.commit()
            return {'code': 1000}
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        db.session.rollback()
        return {'code': 1500}


def auth_user(data):
    try:
        res = get_user(data['login'])
        if res['code'] == 1000:
            if res['password'] == data['password']:
                token = jwt.encode({'login': data['login']}, SECRET_KEY, algorithm='HS256')
                return {'code': 1000, 'token': token}
            else:
                return CODE_ERROR_DATA
        else:
            return CODE_ERROR_DATA
    except Exception as error:
        debug(error)
        return CODE_DATABASE_ERROR


def check_token(token):
    try:
        token = token.split()[1]
        token_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {'code': 1000, 'login': token_data['login']}
    except Exception:
        return {'code': 1301}


def check_available(data, keys):
    if data is not None:
        for key in keys:
            if key not in data:
                return False
        return True
    else:
        return False


def link_validator(url):
    if url.startswith(('https://', 'http://')):
        return url
    else:
        return 'http://' + url


def get_week():
    date_format = '%d %B %Y'
    today = datetime.now()
    week = [today.strftime(date_format), (today - timedelta(days=1)).strftime(date_format),
            (today - timedelta(days=2)).strftime(date_format), (today - timedelta(days=3)).strftime(date_format),
            (today - timedelta(days=4)).strftime(date_format), (today - timedelta(days=5)).strftime(date_format),
            (today - timedelta(days=6)).strftime(date_format)]
    return list(reversed(week))


def get_today():
    date_format = '%d %B %Y'
    today = datetime.now().strftime(date_format)
    return today


def get_link(url):
    if available_short(url) is False:
        link_data = Links.query.filter_by(short_url=url).first()
        return {
            'code': 1000,
            'link_id': link_data.link_id,
            'short_url': link_data.short_url,
            'full_url': link_data.full_url,
            'title': link_data.title,
            'date_create': time.strftime('%d %B %Y %H:%M', datetime.timetuple(link_data.date_create)),
            'access': link_data.access,
            'secret_code': link_data.secret_code,
            'owner': link_data.owner,
        }
    else:
        return CODE_ERROR_VALUE


def get_link_update(login, link_id):
    link_data = Links.query.filter_by(link_id=link_id).first()
    if link_data.owner == login:
        return {
            'code': 1000,
            'short_url': link_data.short_url,
            'full_url': link_data.full_url,
            'title': link_data.title,
            'access': link_data.access,
        }
    else:
        return CODE_ERROR_VALUE


def update_redirects(link_id):
    info_redirects = LinksAdditional.query.filter_by(link_id=link_id).first()
    redirects = eval(info_redirects.redirects)
    between = datetime.strptime(get_today(), "%d %B %Y") - datetime.strptime(eval(info_redirects.date)[6], "%d %B %Y")
    if eval(info_redirects.date)[6] == get_today():
        redirects[6] += 1
        try:
            LinksAdditional.query.filter_by(link_id=link_id).update(dict(redirects=str(redirects)))
            db.session.commit()
            return {'code': 1000}
        except Exception as error:
            debug(error)
            db.session.rollback()
            return {'code': 1500}
    elif between >= timedelta(7):
        try:
            LinksAdditional.query.filter_by(link_id=link_id).update(
                dict(redirects=str([0, 0, 0, 0, 0, 0, 0]), date=str(get_week())))
            db.session.commit()
            return {'code': 1000}
        except Exception as error:
            debug(error)
            db.session.rollback()
            return {'code': 1500}
    elif between < timedelta(7):
        if between == timedelta(1):
            redirects = [redirects[1], redirects[2], redirects[3], redirects[4], redirects[5], redirects[6], 1]
        elif between == timedelta(2):
            redirects = [redirects[2], redirects[3], redirects[4], redirects[5], redirects[6], 0, 1]
        elif between == timedelta(3):
            redirects = [redirects[3], redirects[4], redirects[5], redirects[6], 0, 0, 1]
        elif between == timedelta(4):
            redirects = [redirects[4], redirects[5], redirects[6], 0, 0, 0, 1]
        elif between == timedelta(5):
            redirects = [redirects[5], redirects[6], 0, 0, 0, 0, 1]
        elif between == timedelta(5):
            redirects = [redirects[6], 0, 0, 0, 0, 0, 1]
        try:
            LinksAdditional.query.filter_by(link_id=link_id).update(
                dict(redirects=str(redirects), date=str(get_week())))
            db.session.commit()
            return {'code': 1000}
        except Exception as error:
            debug(error)
            db.session.rollback()
            return {'code': 1500}


def all_redirects(login):
    all_reds = [0, 0, 0, 0, 0, 0, 0]
    try:
        link_data = Links.query.filter_by(owner=login).all()
        count_redirects = 0
        for item in link_data:
            print(item)
            item_data = LinksAdditional.query.filter_by(link_id=item.link_id).first()
            redirects = eval(item_data.redirects)
            all_reds = [all_reds[0] + redirects[0], all_reds[1] + redirects[1], all_reds[2] + redirects[2],
                        all_reds[3] + redirects[3], all_reds[4] + redirects[4], all_reds[5] + redirects[5],
                        all_reds[6] + redirects[6]]
            count_redirects += redirects[0] + redirects[1] + redirects[2] + redirects[3] + redirects[4] + redirects[5] + \
                               redirects[6]
        return {
            'code': 1000,
            'date': eval(item_data.date),
            'redirects': all_reds,
            'links_count': len(link_data),
            'all_count': count_redirects
        }
    except Exception as error:
        debug(error)
        return CODE_ERROR_DATA


def link_redirects(login, link_id):
    try:
        link_data = Links.query.filter_by(link_id=link_id).first()
        if link_data.owner == login:
            link_data = LinksAdditional.query.filter_by(link_id=link_id).first()
            return {
                'code': 1000,
                'date': eval(link_data.date),
                'redirects': eval(link_data.redirects)
            }
        else:
            return CODE_ERROR_VALUE
    except Exception as error:
        debug(error)
        return CODE_ERROR_DATA


def link_update(data, login):
    link_data = Links.query.filter_by(link_id=data['link_id']).first()
    if link_data.owner == login:
        try:
            Links.query.filter_by(link_id=data['link_id']).update(
                dict(short_url=data['short_url'], full_url=data['full_url'], access=data['access']))
            db.session.commit()
            return {'code': 1000}
        except Exception as error:
            debug(error)
            db.session.rollback()
            return {'code': 1500}
    else:
        return CODE_ERROR_VALUE


def get_link_info(full_url, login):
    match = re.search('<title>(.*?)</title>', requests.get(full_url).text)
    title = match.group(1) if match else 'Заголовок отсутствует'
    hash_len = 8
    while True:
        short_url = hashlib.sha1(str(login + full_url).encode("UTF-8"))
        short_url = short_url.hexdigest()
        short_url = short_url[:hash_len]
        link_data = get_link(short_url)
        if link_data['code'] == 1000 and link_data['owner'] != login:
            hash_len += 1
        elif link_data['code'] == 1000 and link_data['owner'] == login:
            return CODE_ERROR_VALUE
        else:
            return {
                'code': 1000,
                'title': title,
                'short_url': short_url,
                'full_url': full_url,
            }


def get_all_links(login):
    all_links = []
    try:
        links_data = Links.query.filter_by(owner=login).all()
        for item in links_data:
            if item.access == 'public':
                item.access = "Публичный"
            elif item.access == 'authorized':
                item.access = "Необходима регистрация"
            if item.access == 'code':
                item.access = "Необходим код доступа"
            all_links.append([item.link_id, item.title, item.full_url,
                              "<a target='_blank' href='https://shcut.gq/" + item.short_url + "'>shcut.gq/" + item.short_url + "</a>",
                              time.strftime('%d %B %Y %H:%M', datetime.timetuple(item.date_create)), item.access])
    except Exception as error:
        debug(error)
    return {"links": all_links}


def create_link(data, login):
    data['full_url'] = link_validator(data['full_url'])
    redirects = [0, 0, 0, 0, 0, 0, 0]
    try:
        link_data = Links(short_url=data['short_url'], full_url=data['full_url'], title=data['title'],
                          access=data['access'], owner=login, secret_code=data['secret_code'])
        link_additional = LinksAdditional(date=str(get_week()), redirects=str(redirects))
        db.session.add(link_data)
        db.session.add(link_additional)
        db.session.commit()
        return CODE_SUCCESS
    except Exception as error:
        db.session.rollback()
        print('DEBUG:', error)
        return CODE_DATABASE_ERROR


@app.route('/user', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def user():
    token_data = check_token(request.headers.get('Authorization'))
    data = request.json
    if request.method == 'POST':
        if check_available(data, ['login', 'password']):
            print(auth_user(data))
            return jsonify(auth_user(data))
        else:
            return jsonify(CODE_ERROR_DATA)
    if token_data['code'] == 1000:
        if request.method == 'GET':
            return jsonify(get_profile(token_data['login']))
        elif request.method == 'PATCH':
            if check_available(data, ['password', 'first_name', 'last_name']):
                return jsonify(update_user(token_data['login'], data))
            else:
                return jsonify(CODE_ERROR_DATA)
        elif request.method == 'DELETE':
            return jsonify(delete_user(token_data['login']))
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/reg', methods=['POST'])
def user_reg():
    if request.method == 'POST':
        data = request.json
        if check_available(data, ['login', 'password', 'email', 'first_name', 'last_name']):
            return jsonify(create_user(data))
        else:
            return jsonify(CODE_ERROR_DATA)


@app.route('/link', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def link():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'GET':
            args = request.args.get('link_id')
            return jsonify(get_link_update(token_data['login'], args))
        elif request.method == 'POST':
            data = request.json
            if check_available(data, ['full_url', 'short_url', 'title', 'access', 'secret_code']):
                return jsonify(create_link(data, token_data['login']))
            else:
                return jsonify(CODE_ERROR_DATA)
        elif request.method == 'PATCH':
            data = request.json
            if check_available(data, ['link_id', 'full_url', 'short_url', 'access']):
                return jsonify(link_update(data, token_data['login']))
            else:
                return jsonify(CODE_ERROR_DATA)
        elif request.method == 'DELETE':
            data = request.json
            if check_available(data, ['link_id']):
                return jsonify(delete_link(token_data['login'], data['link_id']))
            else:
                return jsonify(CODE_ERROR_DATA)
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/get_links', methods=['GET'])
def all_user_links():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        return jsonify(get_all_links(token_data['login']))
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/link_info', methods=['POST'])
def link_info():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'POST':
            data = request.json
            if check_available(data, ['full_url']):
                return jsonify(get_link_info(data['full_url'], token_data['login']))
            else:
                return jsonify(CODE_ERROR_DATA)
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/link_stats', methods=['POST'])
def link_stats():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'POST':
            data = request.json
            if check_available(data, ['link_id']):
                return jsonify(link_redirects(token_data['login'], data['link_id']))
            else:
                return jsonify(CODE_ERROR_DATA)
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/links_stats', methods=['GET'])
def all_link_stats():
    token_data = check_token(request.headers.get('Authorization'))
    if token_data['code'] == 1000:
        if request.method == 'GET':
            data = request.json
            return jsonify(all_redirects(token_data['login']))
    else:
        return jsonify(CODE_ERROR_TOKEN)


@app.route('/available', methods=['POST'])
def available():
    if request.method == 'POST':
        data = request.json
        if check_available(data, ['email']):
            if available_email(data['email']):
                return CODE_SUCCESS
            else:
                return CODE_ERROR_VALUE
        elif check_available(data, ['login']):
            if available_login(data['login']):
                return CODE_SUCCESS
            else:
                return CODE_ERROR_VALUE
        elif check_available(data, ['short_url']):
            if available_short(data['short_url']):
                return CODE_SUCCESS
            else:
                return CODE_ERROR_VALUE


@app.route('/<short_url>')
def user_redirect(short_url):
    if request.method == 'GET':
        link_data = get_link(short_url)
        if link_data['code'] == 1000:
            if link_data['access'] == 'public':
                update_redirects(link_data['link_id'])
                return redirect(link_data['full_url'])
            elif link_data['access'] == 'authorized':
                cookies = request.cookies.get('token')
                token_data = check_token("bearer " + str(cookies))
                if token_data['code'] == 1000:
                    update_redirects(link_data['link_id'])
                    return redirect(link_data['full_url'])
                else:
                    return 'You dont have access for this link. Please login.'
            elif link_data['access'] == 'self':
                cookies = request.cookies.get('token')
                token_data = check_token("bearer " + str(cookies))
                if token_data['code'] == 1000:
                    if token_data['login'] == link_data['owner']:
                        update_redirects(link_data['link_id'])
                        return redirect(link_data['full_url'])
                    else:
                        return 'You dont have access for this link.'
                else:
                    return 'You dont have access for this link.'
        else:
            return 'Sorry, We didnt find this link.'


if __name__ == '__main__':
    app.run()
