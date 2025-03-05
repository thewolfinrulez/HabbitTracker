
import config as cfg
from flask import Flask, request, render_template, make_response, jsonify
import requests
from db_controller import db
import auth_controller as auth
from keycloak.keycloak_admin import KeycloakAdmin
from keycloak.openid_connection import KeycloakOpenIDConnection
from models import TUser, TGroup, TGroupUser, TTask
import jwt
from sqlalchemy import desc


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = cfg.db_url
    app.config['SQLALCHEMY_ECHO'] = False
    db.init_app(app)
    return app


app = create_app()


@app.route("/")
def index():
    return 'Working...'


@app.route("/register", methods=['POST'])
def register():
    payload = request.json
    check_username = TUser.query.filter(TUser.u_username == payload['username'])
    if check_username.count() > 0:
        return make_response("This username is already taken", 449)
    check_email = TUser.query.filter(TUser.u_email == payload["email"])
    if check_email.count() > 0:
        return make_response("This email is already registered", 449)
    new_user = TUser(u_username=payload['username'], u_name=payload["name"], u_email=payload['email'],
                     u_lastname=payload['lastname'], u_score=0)
    db.session.add(new_user)
    keycloak_connection = KeycloakOpenIDConnection(
        server_url=cfg.auth_url,
        realm_name=cfg.realm_name,
        client_id=cfg.client_id,
        client_secret_key=cfg.client_secret_key,
        verify=True)

    keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
    resp = keycloak_admin.create_user({"email": payload["email"], "username": payload['username'],
                                       "enabled": True,
                                       "firstName": payload["name"],
                                       "lastName": payload['lastname'],
                                       "credentials": [{"value": payload["password"], "type": "password", }]},
                                      exist_ok=False)
    db.session.commit()
    user = keycloak_admin.get_user_id(payload["email"])
    return make_response('Registration successful', 200)


@app.route("/login", methods=['POST'])
def login():
    payload = request.json
    data = f'grant_type=password&client_id=admin&client_secret={cfg.client_secret_key}&username={payload["username"]}&password={payload["password"]}'
    response = requests.post(cfg.auth_url + "realms/TaskManager/protocol/openid-connect/token", data=data, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    print(response.json())
    if 'error' in response.json():
        return make_response(response.json(), 500)
    return make_response(response.json(), 200)


@app.route("/create_group", methods=['POST'])
def create_group():
    payload = request.json
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    user = user.first()
    new_group = TGroup(g_owner_id=user.u_id, g_name=payload['name'])
    db.session.add(new_group)
    db.session.flush()
    new_group_user = TGroupUser(gu_group_id=new_group.g_id, gu_user_id=user.u_id, gu_score=0)
    db.session.add(new_group_user)
    db.session.commit()
    return make_response(new_group.as_obj(), 200)


@app.route("/groups", methods=['GET'])
@app.route("/groups/<group_id>", methods=['GET'])
def get_groups(group_id=None):
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    user = user.first()
    final_json = []
    if group_id:
        group_users = TGroupUser.query.filter(TGroupUser.gu_group_id == group_id)
        for group_user in group_users:
            final_json.append(group_user.as_obj())
    else:
        groups = TGroupUser.query.filter(TGroupUser.gu_user_id == user.u_id)
        for group in groups:
            final_json.append(TGroup.query.filter(TGroup.g_id == group.gu_group_id).first().as_obj())
    return make_response(final_json, 200)


@app.route("/add_user_to_group", methods=['POST'])
def add_user_to_group():
    payload = request.json
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    group = TGroup.query.filter(TGroup.g_id == payload['group_id'])
    if group.count() == 0:
        return make_response("Group not found", 449)
    group = group.first()
    user_to_add = TUser.query.filter(TUser.u_username == payload['username'])
    if user_to_add.count() == 0:
        return make_response("User not found", 449)
    user_to_add = user_to_add.first()
    group_user = TGroupUser(gu_group_id=group.g_id, gu_user_id=user_to_add.u_id, gu_score=0)
    db.session.add(group_user)
    db.session.commit()
    return make_response("Success", 200)


@app.route("/add_task", methods=['POST'])
def add_task():
    payload = request.json
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    group = TGroup.query.filter(TGroup.g_id == payload['group_id'])
    if group.count() == 0:
        return make_response("Group not found", 449)
    new_task = TTask(t_group_id=payload['group_id'], t_score_amount=payload['score_amount'], t_name=payload['name'])
    db.session.add(new_task)
    db.session.commit()
    return make_response(new_task.as_obj(), 200)


@app.route("/tasks", methods=['GET'])
def get_task():
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи
        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    user = user.first()
    groups = TGroupUser.query.filter(TGroupUser.gu_user_id == user.u_id)
    final_json = []
    for group in groups:
        tasks = TTask.query.filter(TTask.t_group_id == group.gu_group_id)
        for task in tasks:
            final_json.append(task.as_obj())
    return make_response(final_json, 200)


@app.route("/complete_task", methods=['POST'])
def complete_task():
    payload = request.json
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    user = TUser.query.filter(TUser.u_email == email)
    if user.count() == 0:
        return make_response("Invalid auth", 401)
    user = user.first()
    task = TTask.query.filter(TTask.t_id == payload['task_id'])
    if task.count() == 0:
        return make_response("Task not found", 449)
    task = task.first()
    group_user = TGroupUser.query.filter(TGroupUser.gu_group_id == task.t_group_id).filter(
        TGroupUser.gu_user_id == user.u_id)
    if group_user.count() == 0:
        return make_response("User is not in group", 449)
    group_user = group_user.first()
    user.u_score += task.t_score_amount
    group_user.gu_score += task.t_score_amount
    db.session.commit()
    return make_response(user.as_obj(), 200)


@app.route("/leaderboard", methods=['GET'])
def leaderboard():
    group_id = request.args.get('group_id', default=None, type=str)
    try:
        token_info = auth.check_auth(request.headers)
        if not token_info:
            return make_response("Invalid auth", 401)
        decoded_token = jwt.decode(token_info, options={"verify_signature": False})  # Отключаем верификацию подписи

        email = decoded_token.get("email")
    except:
        return make_response("Invalid auth", 401)
    result_json = []
    if group_id:
        group_users = TGroupUser.query.filter(TGroupUser.gu_group_id == group_id).order_by(desc(
            TGroupUser.gu_score))
        for group_user in group_users:
            user_info = TUser.query.filter(TUser.u_id == group_user.gu_user_id).first()
            result_json.append({"username": user_info.u_username, "name": user_info.u_name,
                                "lastname": user_info.u_lastname, "score": group_user.gu_score})
    else:
        users_info = TUser.query.order_by(desc(TUser.u_score))
        for user_info in users_info:
            result_json.append({"username": user_info.u_username, "name": user_info.u_name,
                                "lastname": user_info.u_lastname, "score": user_info.u_score})
    return make_response(result_json, 200)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=9128)
