from sql import db

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    identity = db.Column(db.String(255), nullable=False)
    user_image = db.Column(db.LargeBinary, nullable=True)
    WebURL = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<User {self.user_id} {self.username}>"