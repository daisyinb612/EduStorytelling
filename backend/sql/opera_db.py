from sqlalchemy.orm import relationship
from sqlalchemy.types import Date
from sql import db

class Opera(db.Model):
    __tablename__ = 'opera'
    opera_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    opera_name = db.Column(db.String(50), nullable=False)
    create_time = db.Column(Date, nullable=False)
    opera_image = db.Column(db.LargeBinary, nullable=True)

    # 关系：每个剧本属于一个用户
    user = relationship('User', backref='operas')

    def __repr__(self):
        return f"<Opera {self.opera_id} {self.opera_name}>"