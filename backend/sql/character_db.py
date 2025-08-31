from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from sql import db

class Character(db.Model):
    __tablename__ = 'character'
    character_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.storyline_id'), nullable=False)
    character_name = db.Column(db.String(50), nullable=False)
    appearance = db.Column(db.String(200))
    personality = db.Column(db.String(200))
    related = db.Column(JSON)

    # 关系：每个角色属于一个故事概要
    storyline = relationship('Storyline', backref='characters')

    def __repr__(self):
        return f"<Character {self.character_id} {self.character_name}>"

    @staticmethod
    # 核心业务逻辑函数：使用显式参数创建角色
    def create_character_core(
            user_id,
            storyline_id,
            character_name,
            appearance="",
            personality="",
            related=None
    ):
        """
        创建新的角色（显式参数版本）

        参数:
            user_id: 用户ID
            storyline_id: 关联的故事概要ID（必填）
            character_name: 角色名称（必填）
            appearance: 角色外貌描述（可选，默认空字符串）
            personality: 角色性格描述（可选，默认空字符串）
            related: 关联角色信息（可选，默认空字典）

        返回:
            成功: 新创建的角色对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 处理related默认值
            if related is None:
                related = {}

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not storyline_id:
                return ("Missing required field: storyline_id", 400)
            if not character_name:
                return ("Missing required field: character_name", 400)

            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this storyline", 403)

            # 字段长度校验
            if len(character_name) > 50:
                return ("Character name must be less than 50 characters", 400)
            if len(appearance) > 200:
                return ("Appearance must be less than 200 characters", 400)
            if len(personality) > 200:
                return ("Personality must be less than 200 characters", 400)

            # 创建新角色
            new_character = Character(
                user_id=user_id,
                storyline_id=storyline_id,
                character_name=character_name,
                appearance=appearance,
                personality=personality,
                related=related
            )

            # 保存到数据库
            db.session.add(new_character)
            db.session.commit()

            return new_character  # 成功时返回角色对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：按故事概要批量删除角色
    def delete_characters_by_storyline_core(user_id, storyline_id):
        """
        删除指定故事概要（storyline_id）下的所有角色。

        参数:
            user_id: 用户ID（用于权限校验）
            storyline_id: 故事概要ID

        返回:
            成功: {"deleted_count": 被删除的数量, "deleted_ids": [被删除的角色ID列表]}
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera

            # 校验必填参数
            if not storyline_id:
                return ("Missing required field: storyline_id", 400)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this storyline", 403)

            # 查询并删除角色
            characters = Character.query.filter_by(storyline_id=storyline_id).all()
            if not characters:
                return {"deleted_count": 0, "deleted_ids": []}

            deleted_ids = [c.character_id for c in characters]
            for character in characters:
                db.session.delete(character)

            db.session.commit()
            return {"deleted_count": len(deleted_ids), "deleted_ids": deleted_ids}

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：删除角色
    def delete_character_core(user_id, character_id):
        """
        删除指定的角色（显式参数版本）

        参数:
            user_id: 用户ID
            character_id: 要删除的角色ID

        返回:
            成功: 被删除的角色对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 验证必填参数
            if not character_id:
                return ("Missing required field: character_id", 400)

            # 查找要删除的角色
            character = Character.query.get(character_id)
            if not character:
                return ("Character not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            storyline = Storyline.query.get(character.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
            
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this character", 403)

            # 保存角色信息用于返回
            deleted_character = character

            # 从数据库删除角色
            db.session.delete(character)
            db.session.commit()

            return deleted_character  # 成功时返回被删除的角色对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)