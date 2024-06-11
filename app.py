from flask import Flask, send_from_directory, jsonify, request, session
from datetime import datetime
from db_models import db, Users, Chatrooms, Messages
import uuid

from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
CORS(app)

# db_user = 'root'
# db_password = ''
# db_host = 'localhost'
# db_name = 'bestdb'
db_user = 'crisppbacon'
db_password = 'Blacks132'
db_host = 'crisppbacon.mysql.pythonanywhere-services.com'
db_name = 'crisppbacon$thebestdatabase'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{db_user}:{db_password}@{db_host}/{db_name}"

db.init_app(app)

app.secret_key = '74679e8244cf2b2869902f183ce3d864ba0c63e02585a21f4e10c5fc064eee05'
app.config['SECRET_KEY'] = '74679e8244cf2b2869902f183ce3d864ba0c63e02585a21f4e10c5fc064eee05'
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173", async_mode='threading')

@app.route('/')
def index():
    return send_from_directory('react-app', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('react-app', 'index.html')


@app.route('/api/auth', methods=["POST"])
def auth():
    if request.method == "POST":
        data = request.json

        signup_data = data.get('signup')
        login_data = data.get('login')
        checkSession = data.get('checkSession')

        if login_data:
            uid = login_data.get('uid', '').lower()
            pwd = login_data.get('pwd', '')

            if not (uid or pwd):
                return jsonify({'error': "Please enter your username and password"});

            data = Users.query.filter_by(username=uid).first()

            if not data:
                return jsonify({'error': "User does not exist!"})

            if pwd != data.password:
                return jsonify({'error': 'Password incorrect!'})

            userdata = {
                '_id': data.uuid,
                'username': data.username,
                'fullname': data.fullname.title(),
                'email': data.email
            }

            session['userdata'] = userdata
            return jsonify(session['userdata'])

        elif signup_data:
            firstname = signup_data.get('firstname', '')
            lastname = signup_data.get('lastname', '')
            email = signup_data.get('email', '').lower()
            uid = signup_data.get('uid', '').lower()
            pwd = signup_data.get('pwd', '')
            confirm_pwd = signup_data.get('confirmPwd', '')

            if pwd != confirm_pwd:
                return jsonify({'error': 'Password does not match!'})

            if not all([firstname, lastname, email, uid, pwd, confirm_pwd]):
                return jsonify({'error': 'Please fill in everything'})

            user_exist = Users.query.filter_by(username=uid).first()
            email_exist = Users.query.filter_by(email=email).first()
            if user_exist:
                return jsonify({'error': 'Username already exist'})
            if email_exist:
                return jsonify({'error': 'Email already exiss'})

            new_user = Users(
                uuid=uuid.uuid4(),
                fullname=f"{firstname.upper()} {lastname.upper()}",
                username=uid,
                email=email,
                password=pwd
            )
            try:
                # Add the new user to the database
                db.session.add(new_user)
                db.session.commit()
                return jsonify({'success': 'User created successfully'})
            except Exception as e:
                print(f"Error while creating user: {e}")
                db.session.rollback()
                return jsonify({'error': 'Internal server error'})

        elif checkSession:
            if 'userdata' not in session or '_id' not in session['userdata']:
                return jsonify({'error': 'No session found'})

            _id = session['userdata']['_id']

            check_session_data = request.json.get('checkSession', {})
            if _id != check_session_data.get('_id'):
                return jsonify({'error': 'Invalid session ID!'})

            return jsonify(session['userdata'])

        elif "logout" in data:
            session.clear()
            return jsonify({'success': 'You have logged out!'})

    return jsonify({"error": "Auth Routing"})

@app.route('/api/rooms', methods=["POST"])
def rooms():
    if request.method != "POST":
        return jsonify({"error": "Rooms Routing"})

    getRoom = request.json.get('getRoom');
    getMessages = request.json.get('getMessages')

    if getRoom:
        sender_id = getRoom.get('user_id')
        receiver_id = getRoom.get('person_id')

        if len(sender_id) != 36 or len(receiver_id) != 36:
            return jsonify({'error': 'IDs must be 36 characters long'})

        receiver_exist = Users.query.filter_by(uuid=receiver_id).first()
        sender_exist = Users.query.filter_by(uuid=sender_id).first()

        if not sender_exist:
            return jsonify({'error': "Sender user doesn't exist"})
        if not receiver_exist:
            return jsonify({'error': "Receiver user doesn't exist"})

        chatroom = Chatrooms.query.filter(
            (
                Chatrooms.members.contains([sender_id, receiver_id])
            )
            | (
                Chatrooms.members.contains([receiver_id, sender_id])
            )
        ).first()
        if chatroom:
            return jsonify(chatroom.serialize())

        new_chatroom = Chatrooms(
            _id=str(uuid.uuid4()),
            name="Private",
            members=[sender_id, receiver_id],
            created_at=datetime.now()
        )

        try:
            db.session.add(new_chatroom)
            db.session.commit()
            return jsonify(new_chatroom.serialize())
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Internal server error'})



    if getMessages:
        chatroom_id = getMessages.get('room_id', None)
        if not chatroom_id:
            return jsonify({'error': 'Invalid chatroom id!'})

        data = Messages.query.filter_by(chatroom_id=chatroom_id).all()

        if len(data) > 0:
            serialized_data = [msg.serialize() for msg in data]
        else:
            serialized_data = []
        return jsonify(serialized_data)


@app.route('/hello')
def hello():
    return "HELLO"

@app.route('/api/users', methods=["POST"])
def users():
    search = request.json.get('search', None)

    if search:
        search_value = search.get('searchValue', '')
        if not search_value:
            return jsonify([])

        # Query the database
        usersdata = Users.query.filter(
            db.or_(
                Users.fullname.ilike(f'%{search_value}%'),
                Users.username.ilike(f'%{search_value}%')
            )
        ).all()

        data = []
        for user in usersdata:
            user.fullname = user.fullname.title()
            data.append({
                '_id': user.uuid,
                'fullname': user.fullname,
                'username': user.username,
                'email': user.email
            })

        return jsonify(data)

@socketio.on('connect')
def handle_connect():
    print("User Connected:", request.sid)
    print("CONNECTED HERE!!!!")

@socketio.on('disconnect')
def handle_disconnect():
    print("User disconnected:", request.sid)

@socketio.on('join_room')
def handle_join_room(room_id):
    print("User joined the room", room_id)
    join_room(room_id)

@socketio.on('leave_room')
def handle_leave_room(room_id):
    print("User left the room", room_id)
    leave_room(room_id)

@socketio.on('send_message')
def handle_send_message(data):
    if not data.get('message'):
        return

    room_id = data.get("room_id")
    sender_id = data.get('sender_id')
    message = data.get('message')

    new_message = Messages(
        _id=str(uuid.uuid4()),
        chatroom_id=room_id,
        sender_id=sender_id,
        content=message,
        timestamp=datetime.now()  # Use datetime object or timestamp value
    )
    try:
        db.session.add(new_message)
        db.session.commit()
        print("MESSAGE SENT SUCCESSFULLY!")
    except Exception as e:
        print("Error while saving new document:", e)
        db.session.rollback()

    emit('received_message', new_message.serialize(), room=data.get('room_id'))
    emit('new_message', new_message.serialize(), room=data.get('receiver_id'))
    emit('new_message', new_message.serialize(), room=data.get('sender_id'))
    # Sending callback response
    emit('message_sent_response', new_message.serialize(), room=request.sid)

if __name__ == '__main__':
    # app.run(port=3500)
    socketio.run(app, port=3500, debug=True)





