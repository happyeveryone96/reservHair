from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# client = MongoClient('mongodb://test:test@localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.revHair


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        user_info = db.users.find_one({"username": payload['id']})
        return render_template('index.html', username=user_info["username"])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)




@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token, 'user_id': result['username'], 'gender': result['gender']})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    gender_receive = request.form['gender_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,
        'gender': gender_receive,
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})



# 리뷰
## HTML 화면 보여주기
@app.route('/Review')
def MyhairShop():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload['id']})
        return render_template('reviewIndex.html', username=user_info["username"])
        return render_template('reviewIndex.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))


@app.route('/review', methods=['POST'])
def save_order():
    hairstyle_receive = request.form['hairStyle_give']
    content_receive = request.form['content_give']
    doc = {
        'hairStyle': hairstyle_receive,
        'content': content_receive,
        'like': 0
    }
    db.revHair.insert_one(doc)

    return jsonify({'result': 'success', 'msg': '작성 완료!'})


@app.route('/review', methods=['GET'])
def view_orders():
    review = list(db.revHair.find({}, {'_id': False}).sort("like", -1))
    return jsonify({'result': 'success', 'review': review})


@app.route('/api/like', methods=['POST'])
def like_orders():
    content_receive = request.form['content_give']

    target_like = db.revHair.find_one({'content': content_receive})
    current_like = target_like['like']

    new_like = current_like + 1

    db.revHair.update_one({'content': content_receive}, {'$set': {'like': new_like}})

    return jsonify({'result': 'success'})


# 홈페이지 info
@app.route('/Info')
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload['id']})
        return render_template('InfoIndex.html', username=user_info["username"])
        return render_template('InfoIndex.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))


# 예약하기
@app.route('/reservation_history', methods=['GET'])
def reservation_get():
    userId = request.args.get('user_id')
    reservation_history = list(db.reservation.find({'user_id': userId}, {'_id': False}))
    return jsonify(reservation_history)


# 유저 id
@app.route('/reservation_confirm', methods=['POST'])
def reservation_post():
    db = client.revHair
    hair = request.form.get('hair');
    time = request.form.get('time');
    date = request.form.get('date');
    etc = request.form.get('etc');
    user_id = request.form.get('user_id');

    doc = {'hair': hair, 'time': time, 'date': date, 'etc': etc, 'user_id': user_id}
    db.reservation.insert_one(doc)

    return jsonify({'result': 'success', 'msg': '예약이 완료되었습니다!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
