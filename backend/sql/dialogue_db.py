from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from sql import db

class Dialogue(db.Model):
    __tablename__ = 'dialogue'

    dialogue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.storyline_id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.plot_id'), nullable=False)
    dialogue_content = db.Column(db.JSON, nullable=False)

    # 关系
    storyline = relationship('Storyline', backref='dialogues')
    plot = relationship('Plot', backref='dialogues')
    

    def __repr__(self):
        return f"<Dialogue {self.dialogue_id} {self.dialogue_content}>"

    @staticmethod
    def create_dialogue_core(
            user_id,
            storyline_id,
            plot_id,
            dialogue_content
    ):
        """
        创建新的对话（显式参数版本）

        参数:
            user_id: 用户ID
            storyline_id: 关联的故事概要ID（必填）
            plot_id: 关联的情节ID（必填）
            dialogue_content: 对话内容JSON（必填）

        返回:
            成功: 新创建的对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Plot, Opera
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not storyline_id:
                return ("Missing required field: storyline_id", 400)
            if not plot_id:
                return ("Missing required field: plot_id", 400)
            if not dialogue_content:
                return ("Missing required field: dialogue_content", 400)

            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            # 验证情节是否存在
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)

            # 验证情节是否属于指定的故事概要
            if plot.storyline_id != storyline_id:
                return ("Plot does not belong to the specified storyline", 400)

            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this storyline", 403)

            # 验证对话内容格式（应该是有效的JSON格式）
            if not isinstance(dialogue_content, (dict, list)):
                return ("Dialogue content must be a valid JSON object or array", 400)

            # 创建新对话
            new_dialogue = Dialogue(
                user_id=user_id,
                storyline_id=storyline_id,
                plot_id=plot_id,
                dialogue_content=dialogue_content
            )

            # 保存到数据库
            db.session.add(new_dialogue)
            db.session.commit()

            return new_dialogue  # 成功时返回对话对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def get_dialogue_by_id_core(user_id, dialogue_id):
        """
        根据ID获取指定的对话信息

        参数:
            user_id: 用户ID
            dialogue_id: 要获取的对话ID

        返回:
            成功: 对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera

            # 验证必填参数
            if not dialogue_id:
                return ("Missing required field: dialogue_id", 400)

            # 查找对话
            dialogue = Dialogue.query.get(dialogue_id)
            if not dialogue:
                return ("Dialogue not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权
            storyline = Storyline.query.get(dialogue.storyline_id)
            if not storyline:
                return ("Associated storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this dialogue", 403)

            return dialogue

        except SQLAlchemyError as e:
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def get_dialogue_by_plot_id_core(user_id, plot_id):
        """
        根据 plot_id 获取指定的对话信息

        参数:
            user_id: 用户ID
            plot_id: 剧情ID

        返回:
            成功: 对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera, Plot

            # 验证必填参数
            if not plot_id:
                return ("Missing required field: plot_id", 400)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证剧情是否存在
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)

            # 验证所有权
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Associated storyline not found", 404)
            
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this plot", 403)
            
            # 查找对话
            dialogue = Dialogue.query.filter_by(plot_id=plot_id).first()
            if not dialogue:
                return ("Dialogue not found for this plot", 404)
            
            return dialogue

        except SQLAlchemyError as e:
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def update_dialogue_core(
            user_id,
            dialogue_id,
            dialogue_content=None
    ):
        """
        更新对话内容（显式参数版本）

        参数:
            user_id: 用户ID
            dialogue_id: 要更新的对话ID（必填）
            dialogue_content: 新的对话内容JSON（可选，None表示不更新）

        返回:
            成功: 更新后的对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 验证必填参数
            if not dialogue_id:
                return ("Missing required field: dialogue_id", 400)

            # 查找要更新的对话
            dialogue = Dialogue.query.get(dialogue_id)
            if not dialogue:
                return ("Dialogue not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            storyline = Storyline.query.get(dialogue.storyline_id)
            if not storyline:
                return ("Associated storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this dialogue", 403)

            # 更新字段（只更新提供的字段）
            if dialogue_content is not None:
                # 验证对话内容格式
                if not isinstance(dialogue_content, (dict, list)):
                    return ("Dialogue content must be a valid JSON object or array", 400)
                dialogue.dialogue_content = dialogue_content

            # 提交到数据库
            db.session.commit()

            return dialogue  # 成功时返回更新后的对话对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def delete_dialogue_core(user_id, dialogue_id):
        """
        删除指定的对话（显式参数版本）

        参数:
            user_id: 用户ID
            dialogue_id: 要删除的对话ID

        返回:
            成功: 被删除的对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 验证必填参数
            if not dialogue_id:
                return ("Missing required field: dialogue_id", 400)

            # 查找要删除的对话
            dialogue = Dialogue.query.get(dialogue_id)
            if not dialogue:
                return ("Dialogue not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            storyline = Storyline.query.get(dialogue.storyline_id)
            if not storyline:
                return ("Associated storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this dialogue", 403)

            # 保存对话信息用于返回
            deleted_dialogue = dialogue

            # 从数据库删除对话
            db.session.delete(dialogue)
            db.session.commit()

            return deleted_dialogue  # 成功时返回被删除的对话对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def generate_dialogue_from_plot_core(user_id, plot_id):
        """
        根据情节ID生成对话并保存到数据库

        参数:
            user_id: 用户ID
            plot_id: 情节ID（必填）

        返回:
            成功: 新创建的对话对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Plot, Storyline, Opera, Character
            from agent.llm import global_llm
            import json
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not plot_id:
                return ("Missing required field: plot_id", 400)

            # 验证情节是否存在
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)

            # 验证故事概要是否存在
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this plot", 403)

            # 获取该故事概要下的所有角色
            characters = Character.query.filter_by(storyline_id=storyline.storyline_id).all()
            
            # 构建角色列表信息
            character_list = []
            for char in characters:
                character_info = {
                    "name": char.character_name,
                    "personality": char.personality or "",
                    "appearance": char.appearance or ""
                }
                if char.related:
                    character_info["related"] = char.related
                character_list.append(character_info)

            # 构建情节信息
            plot_info = {
                "plotName": plot.plot_name,
                "abstract": plot.abstract or "",
                "character": plot.characters or []
            }

            # 构建故事概要信息
            storyline_info = {
                "theme": storyline.theme or "",
                "classtype": storyline.classtype or "",
                "education": storyline.education or "",
                "level": storyline.level or "",
                "storyline_name": storyline.storyline_name or "",
                "storyline_content": storyline.storyline_content or ""
            }

            # 获取对话生成提示词
            dialogue_prompt = global_llm.setting_dialogue_create
            
            # 构建用户输入内容，包含所有必要信息
            user_input = f"""
###PLOT###
{json.dumps(plot_info, ensure_ascii=False, indent=2)}

###CHARACTERLIST###
{json.dumps(character_list, ensure_ascii=False, indent=2)}

###STORYLINE###
{json.dumps(storyline_info, ensure_ascii=False, indent=2)}
"""

            # 调用global_llm的ask方法生成对话
            print(f"正在为情节 '{plot.plot_name}' 生成对话...")
            dialogue_response = global_llm.ask(
                question=user_input,
                prompt=dialogue_prompt,
                user_id=user_id,
                opera_id=opera.opera_id,
                save_history=False
            )

            # 解析LLM返回的JSON格式对话
            try:
                dialogue_content = global_llm.analyze_answer(dialogue_response)
                
                # 验证对话内容格式
                if not isinstance(dialogue_content, list):
                    return ("Generated dialogue content must be a list", 500)
                
                # 验证每个对话项的格式
                for dialogue_item in dialogue_content:
                    if not isinstance(dialogue_item, dict):
                        return ("Each dialogue item must be a dictionary", 500)
                    if "character" not in dialogue_item or "content" not in dialogue_item:
                        return ("Each dialogue item must contain 'character' and 'content' fields", 500)

            except Exception as e:
                return (f"Failed to parse generated dialogue: {str(e)}", 500)

            # 创建新对话记录
            new_dialogue = Dialogue(
                user_id=user_id,
                storyline_id=storyline.storyline_id,
                plot_id=plot_id,
                dialogue_content=dialogue_content
            )

            # 保存到数据库
            db.session.add(new_dialogue)
            db.session.commit()

            print(f"成功生成并保存对话，包含 {len(dialogue_content)} 条对话内容")
            return new_dialogue  # 成功时返回对话对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)