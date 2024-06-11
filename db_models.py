from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'

    uuid = db.Column(db.String(36), primary_key=True, nullable=False)
    fullname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def serialize(self):
        return {
            'uuid': self.uuid,
            'fullname': self.fullname,
            'username': self.username,
            'email': self.email
        }

class Chatrooms(db.Model):
    __tablename__ = 'chatrooms'

    _id = db.Column(db.String(36), primary_key=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    members = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)

    def serialize(self):
        return {
            '_id': self._id,
            'name': self.name,
            'members': self.members,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Messages(db.Model):
    __tablename__ = 'messages'

    _id = db.Column(db.String(36), primary_key=True, nullable=False)
    chatroom_id = db.Column(db.String(36), nullable=False)
    sender_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    def serialize(self):
        return {
            '_id': self._id,
            'chatroom_id': self.chatroom_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
