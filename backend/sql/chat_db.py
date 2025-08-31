from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import DateTime  # 导入DateTime类型
from datetime import datetime
from sql import db

class Chat(db.Model):
    __tablename__ = 'chat'

    chat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    opera_id = db.Column(db.Integer, db.ForeignKey('opera.opera_id'), nullable=False)
    chat_AI = db.Column(JSON)
    chat_time = db.Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship('User', backref='chats')
    opera = relationship('Opera', backref='chats')

    def __repr__(self):
        return f"<Chat {self.chat_id} user_id={self.user_id} opera_id={self.opera_id}>"

    @staticmethod
    def create_chat(user_id, opera_id, chat_AI):
        """
        创建新的聊天记录

        参数:
            user_id: 用户ID
            chat_data: 包含聊天记录信息的字典，需包含'opera_id'和'chat_AI'

        返回:
            成功: 新创建的聊天记录对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 创建新聊天记录
            new_chat = Chat(
                user_id=user_id,
                opera_id=opera_id,
                chat_AI=chat_AI,
                # 可以指定时间，否则不指定则使用默认的utc时间
                chat_time=datetime.utcnow()
            )

            # 保存到数据库
            db.session.add(new_chat)
            db.session.commit()

            return new_chat  # 成功时返回新创建的聊天记录对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'数据库错误: {str(e)}', 500)
        except Exception as e:
            return (f'服务器错误: {str(e)}', 500)

    @staticmethod
    def get_chat_by_id(chat_id, user_id):
        """
        从数据库查询指定ID的聊天记录，并验证权限

        参数:
            chat_id: 聊天记录ID
            user_id: 当前用户ID（用于权限验证）

        返回:
            成功: 聊天记录对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 查询聊天记录
            chat = Chat.query.get(chat_id)
            if not chat:
                return (f'聊天记录 {chat_id} 不存在', 404)

            # 验证权限
            if chat.user_id != user_id:
                return ("没有权限访问该聊天记录", 403)

            return chat  # 成功时返回聊天记录对象

        except SQLAlchemyError as e:
            return f'数据库错误: {str(e)}', 500
        except Exception as e:
            return (f'服务器错误: {str(e)}', 500)

    @staticmethod
    def update_chat_by_id(chat_id, user_id, update_data):
        """
        更新指定ID的聊天记录，并验证权限

        参数:
            chat_id: 聊天记录ID
            user_id: 当前用户ID（用于权限验证）
            update_data: 包含要更新字段的字典

        返回:
            成功: 更新后的聊天记录对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 查询聊天记录
            chat = Chat.query.get(chat_id)
            if not chat:
                return (f'聊天记录 {chat_id} 不存在', 404)

            # 验证权限
            if chat.user_id != user_id:
                return ("没有权限更新该聊天记录", 403)

            # 允许更新的字段列表，防止恶意更新不允许修改的字段
            allowed_fields = ['chat_AI']

            # 应用更新
            for field in allowed_fields:
                if field in update_data:
                    setattr(chat, field, update_data[field])

            # 更新时间可以选择是否更新为当前时间
            if 'update_time' in update_data and update_data['update_time']:
                chat.chat_time = datetime.utcnow()

            # 提交更改
            db.session.commit()

            return chat  # 成功时返回更新后的聊天记录对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'数据库错误: {str(e)}', 500)
        except Exception as e:
            return (f'服务器错误: {str(e)}', 500)