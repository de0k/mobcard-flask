from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# 환경 변수에서 데이터베이스 연결 정보와 API 키 가져오기
db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '기본-연결-문자열')
kakao_api_key = os.getenv('KAKAO_API_KEY', '기본-API-키')

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 회원 모델 정의
class Membership(db.Model):
    __tablename__ = 'membership'
    email = db.Column(db.String(255), primary_key=True)
    pw = db.Column(db.String(255))

    def __repr__(self):
        return '<User %r>' % self.email

# 스킨(템플릿) 모델 정의
class Skin(db.Model):
    __tablename__ = 'skin'
    email = db.Column(db.String(255), db.ForeignKey('membership.email'), primary_key=True)
    skin = db.Column(db.String(10))

    def __repr__(self):
        return f'<Skin {self.skin}>'

# 회원가입 엔드포인트
@app.route('/signup', methods=['POST'])
def signup():
    email = request.json['email']
    pw = request.json['pw']

    # 이메일 중복 체크
    existing_user = Membership.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': '이미 존재하는 이메일입니다. 다시 입력해주세요.'}), 409

    # 새로운 사용자 생성
    new_user = Membership(email=email, pw=pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# 로그인 엔드포인트
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    pw = request.json['pw']
    user = Membership.query.filter_by(email=email, pw=pw).first()

    if user:
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# 회원 탈퇴 엔드포인트
@app.route('/delete_account', methods=['POST'])
def delete_account():
    email = request.json['email']
    pw = request.json['pw']
    user = Membership.query.filter_by(email=email).first()

    if user:
        # 비밀번호가 일치하는지 확인
        if user.pw == pw:
            # 해당 이메일과 연관된 'skin' 테이블의 행을 먼저 삭제합니다.
            Skin.query.filter_by(email=email).delete()
            # 이후 'membership' 테이블에서 회원 정보를 삭제합니다.
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'Account deleted successfully'}), 200
        else:
            return jsonify({'message': '비밀번호가 일치하지 않습니다. 다시 입력해주세요.'}), 401
    else:
        return jsonify({'message': '비밀번호가 일치하지 않습니다. 다시 입력해주세요.'}), 401


# 템플릿 선택 저장 엔드포인트
@app.route('/api/saveTemplateSelection', methods=['POST'])
def save_template_selection():
    data = request.json
    email = data.get('email')
    selected_skin = data.get('skin') 

    # Membership 테이블에서 해당 이메일 확인
    user = Membership.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Skin 테이블에 데이터 삽입 또는 업데이트
    skin_record = Skin.query.filter_by(email=email).first()
    if skin_record:
        skin_record.skin = selected_skin
    else:
        new_skin = Skin(email=email, skin=selected_skin)
        db.session.add(new_skin)
    db.session.commit()

    return jsonify({'message': 'Template selection saved successfully'}), 200

class Contact(db.Model):
    __tablename__ = 'name'  # 테이블 이름 지정
    email = db.Column(db.String(255), db.ForeignKey('membership.email'), primary_key=True)  # membership 테이블의 email 필드를 참조
    name = db.Column(db.String(50))
    hp = db.Column(db.String(50))  # 문자열로 변경
    address = db.Column(db.String(50))
    fax = db.Column(db.String(50))  # 문자열로 변경
    url = db.Column(db.String(50))
    produc = db.Column(db.String(50))
    rank = db.Column(db.String(50))
    cname = db.Column(db.String(50))
    imgurl = db.Column(db.String(50))

@app.route('/api/contact', methods=['POST'])
def submit_contact_form():
    data = request.json
    # email 값을 기반으로 기존 데이터 조회
    contact = Contact.query.get(data.get('email'))
    if contact:
        # 기존 데이터 업데이트
        for key, value in data.items():
            setattr(contact, key, value)
    else:
        # 새 데이터 생성
        new_contact = Contact(**data)
        db.session.add(new_contact)
    db.session.commit()
    return jsonify({"message": "저장되었습니다"}), 200

@app.route('/api/contact/<email>', methods=['GET'])
def get_contact(email):
    contact = Contact.query.filter_by(email=email).first()
    if contact:
        return jsonify({
            'email': contact.email,
            'name': contact.name,
            'hp': contact.hp,
            'fax': contact.fax,
            'address': contact.address,
            'url': contact.url,
            'produc': contact.produc,
            'rank': contact.rank,
            'cname': contact.cname,
            'imgurl': contact.imgurl
        })
    else:
        return jsonify({'error': 'User not found'}), 404



@app.route('/api/get-coordinates', methods=['GET'])
def get_coordinates():
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'No address provided'}), 400

    headers = {
        'Authorization': f'KakaoAK {KAKAO_API_KEY}'
    }
    response = request.get(
        'https://dapi.kakao.com/v2/local/search/address.json',
        headers=headers,
        params={'query': address}
    )
    if response.status_code != 200:
        return jsonify({'error': 'Error from Kakao API'}), response.status_code

    data = response.json()
    if not data['documents']:
        return jsonify({'error': 'No results found'}), 404

    result = data['documents'][0]
    return jsonify({
        'latitude': result['y'],
        'longitude': result['x']
    })

@app.route('/api/get-user-skin', methods=['GET'])
def get_user_skin():
    email = request.args.get('email')  # 현재 로그인한 사용자의 이메일을 받아옵니다.
    if email is None:
        return jsonify({'error': 'No email provided'}), 400

    user_skin = Skin.query.filter_by(email=email).first()
    if user_skin:
        return jsonify({'skin': user_skin.skin})
    else:
        return jsonify({'error': 'Skin not found for the user'}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 이제 이 코드는 앱 컨텍스트 내에서 실행됩니다
    app.run(debug=False)
