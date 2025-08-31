from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from sql import db

class Storyline(db.Model):
    __tablename__ = 'storyline'
    storyline_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    opera_id = db.Column(db.Integer, db.ForeignKey('opera.opera_id'), nullable=False)
    theme = db.Column(db.String(500))
    classtype = db.Column(db.String(500))
    education = db.Column(db.String(500))
    level = db.Column(db.String(500))
    storyline_name = db.Column(db.String(500))
    storyline_content = db.Column(db.String(500))
    # 主要角色信息，使用 JSON 存储
    maincharacter = db.Column(db.JSON, nullable=True, default=dict)
    # 关系：每个故事概要属于一个剧本
    opera = relationship('Opera', backref='storylines')

    def __repr__(self):
        return f"<Storyline {self.storyline_id} {self.theme}>"

    # 核心业务逻辑函数：获取故事概要
    @staticmethod
    def get_storyline_core(storyline_id, user_id):
        """
        获取指定ID的故事概要，并验证权限

        参数:
            storyline_id: 故事概要ID
            user_id: 当前用户ID（用于权限验证）

        返回:
            成功: 故事概要对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 查询指定ID的故事概要
            storyline = Storyline.query.get(storyline_id)

            # 检查故事概要是否存在
            if not storyline:
                return (f'故事概要 {storyline_id} 不存在', 404)

            # 验证权限：确保当前用户是该故事概要的所有者
            if storyline.user_id != user_id:
                return ("没有权限访问该故事概要", 403)

            return storyline  # 成功时返回故事概要对象

        except SQLAlchemyError as e:
            return (f'数据库错误: {str(e)}', 500)
        except Exception as e:
            return (f'服务器错误: {str(e)}', 500)