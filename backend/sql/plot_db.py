from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from sql import db
from sql import scene_db

class Plot(db.Model):
    __tablename__ = 'plot'
    plot_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.storyline_id'), nullable=False)
    abstract = db.Column(db.String(200))
    plot_name = db.Column(db.String(50))
    characters = db.Column(JSON)

    # 关系：每个情节大纲属于一个故事概要
    storyline = relationship('Storyline', backref='plots')

    def __repr__(self):
        return f"<Plot {self.plot_id} {self.plot_name}>"

    @staticmethod
    # 核心业务逻辑函数：创建剧情大纲
    def create_plot_core(
            user_id,
            storyline_id,
            plot_name,
            abstract="",
            characters=None
    ):
        """
        创建新的剧情大纲（显式参数版本）

        参数:
            user_id: 用户ID
            storyline_id: 关联的故事概要ID（必填）
            plot_name: 剧情名称（必填）
            abstract: 剧情摘要（可选，默认空字符串）
            characters: 角色信息JSON（可选，默认空列表）

        返回:
            成功: 新创建的剧情大纲对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 处理character默认值
            if characters is None:
                characters = []

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not storyline_id:
                return ("Missing required field: storyline_id", 400)
            if not plot_name:
                return ("Missing required field: plot_name", 400)

            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this storyline", 403)

            # 字段长度校验
            if len(plot_name) > 50:
                return ("Plot name must be less than 50 characters", 400)
            if len(abstract) > 200:
                return ("Abstract must be less than 200 characters", 400)

            # 创建新剧情大纲
            new_plot = Plot(
                user_id=user_id,
                storyline_id=storyline_id,
                plot_name=plot_name,
                abstract=abstract,
                characters=characters
            )

            # 保存到数据库
            db.session.add(new_plot)
            db.session.commit()

            return new_plot  # 成功时返回剧情大纲对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def get_plots_by_storyline(user_id, storyline_id):
        """
        获取指定storyline下的所有剧情大纲
        
        参数:
            user_id: 用户ID
            storyline_id: 故事概要ID
            
        返回:
            成功: 剧情大纲列表
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)
                
            # 验证必填参数
            if not storyline_id:
                return ("Missing required field: storyline_id", 400)
                
            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
                
            # 验证所有权（通过故事概要关联的剧本）
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this storyline", 403)
                
            # 查询该storyline下的所有剧情大纲
            plots = Plot.query.filter_by(storyline_id=storyline_id).order_by(Plot.plot_id.asc()).all()
            
            # 构建返回数据
            plot_list = []
            for plot in plots:
                plot_data = {
                    'plot_id': plot.plot_id,
                    'plot_name': plot.plot_name,
                    'abstract': plot.abstract,
                    'characters': plot.characters,
                    'storyline_id': plot.storyline_id,
                    'user_id': plot.user_id
                }
                plot_list.append(plot_data)
                
            return plot_list
            
        except SQLAlchemyError as e:
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def update_plot_core(user_id, plot_id, plot_name=None, abstract=None, characters=None):
        """
        更新指定的剧情大纲
        
        参数:
            user_id: 用户ID
            plot_id: 剧情大纲ID（必填）
            plot_name: 剧情名称（可选）
            abstract: 剧情摘要（可选）
            characters: 角色信息JSON（可选）
            
        返回:
            成功: 更新后的剧情大纲对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Storyline, Opera
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)
                
            # 验证必填参数
            if not plot_id:
                return ("Missing required field: plot_id", 400)
                
            # 查询指定的剧情大纲
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)
                
            # 验证所有权（直接检查plot的user_id）
            if plot.user_id != user_id:
                return ("Permission denied: You do not own this plot", 403)
                
            # 字段长度校验
            if plot_name is not None:
                if not plot_name.strip():
                    return ("Plot name cannot be empty", 400)
                if len(plot_name) > 50:
                    return ("Plot name must be less than 50 characters", 400)
                    
            if abstract is not None and len(abstract) > 200:
                return ("Abstract must be less than 200 characters", 400)
                
            # 更新字段（只更新提供的字段）
            if plot_name is not None:
                plot.plot_name = plot_name.strip()
            if abstract is not None:
                plot.abstract = abstract
            if characters is not None:
                plot.characters = characters
                
            # 保存到数据库
            db.session.commit()
            
            return plot  # 成功时返回更新后的剧情大纲对象
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            db.session.rollback()
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def delete_plots_by_storyline(user_id, storyline_id):
        """
        删除指定storyline下的所有剧情大纲

        参数:
            user_id: 用户ID
            storyline_id: 故事概要ID

        返回:
            成功: (True, "Plots deleted successfully")
            失败: (False, 错误信息)
        """
        try:
            from sql import User, Storyline, Opera
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return (False, "User not found")

            # 验证必填参数
            if not storyline_id:
                return (False, "Missing required field: storyline_id")

            # 验证故事概要是否存在
            storyline = Storyline.query.get(storyline_id)
            if not storyline:
                return (False, "Storyline not found")

            # 验证所有权
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return (False, "Permission denied: You do not own this storyline")

            # 找到所有相关的 plot_id
            plots_to_delete = Plot.query.filter_by(storyline_id=storyline_id).all()
            if not plots_to_delete:
                return (True, "No plots to delete") # 如果没有plot，也算成功

            plot_ids = [plot.plot_id for plot in plots_to_delete]
            
            # 删除所有关联的 Scene
            scene_db.Scene.delete_scenes_by_plot_ids(user_id, plot_ids)
            
            # 删除该storyline下的所有剧情大纲
            Plot.query.filter_by(storyline_id=storyline_id).delete()
            
            db.session.commit()

            return (True, "Plots and associated scenes deleted successfully")

        except SQLAlchemyError as e:
            db.session.rollback()
            return (False, f'Database error: {str(e)}')
        except Exception as e:
            db.session.rollback()
            return (False, f'Server error: {str(e)}')