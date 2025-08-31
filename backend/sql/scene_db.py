from sqlalchemy.exc import SQLAlchemyError
from sql import db

class Scene(db.Model):
    __tablename__ = 'scene'

    scene_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    plot_id = db.Column(db.Integer, db.ForeignKey('plot.plot_id'), nullable=False)
    scene_name = db.Column(db.String(255), nullable=False)
    scene_content = db.Column(db.String(500))
    scene_object = db.Column(db.JSON)
    location = db.Column(db.String(255))

    def __repr__(self):
        return f"<ScenePlot scene_id={self.scene_id} plot_id={self.plot_id}>"

    @staticmethod
    def create_scene_core(
        user_id,
        plot_id,
        scene_name,
        scene_content="",
        scene_object=None,
        location=""
    ):
        """
        创建新的场景

        参数:
            user_id: 用户ID
            plot_id: 关联的剧情大纲ID（必填）
            scene_name: 场景名称（必填）
            scene_content: 场景内容（可选）
            scene_object: 场景对象（JSON，可选）
            location: 场景位置（可选）

        返回:
            成功: 新创建的 Scene 对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import User, Plot, Storyline, Opera

            # 默认值
            if scene_object is None:
                scene_object = {}

            # 校验用户
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 校验必填
            if not plot_id:
                return ("Missing required field: plot_id", 400)
            if not scene_name:
                return ("Missing required field: scene_name", 400)

            # 校验关联与权限
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)

            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)

            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this plot", 403)

            # 字段长度校验
            if len(scene_name) > 255:
                return ("Scene name must be less than 255 characters", 400)
            if scene_content is not None and len(scene_content) > 500:
                return ("Scene content must be less than 500 characters", 400)
            if location is not None and len(location) > 255:
                return ("Location must be less than 255 characters", 400)

            new_scene = Scene(
                user_id=user_id,
                plot_id=plot_id,
                scene_name=scene_name,
                scene_content=scene_content,
                scene_object=scene_object,
                location=location
            )

            db.session.add(new_scene)
            db.session.commit()

            return new_scene

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            db.session.rollback()
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def update_scene_core(
        user_id,
        scene_id,
        scene_name=None,
        scene_content=None,
        scene_object=None,
        location=None
    ):
        """
        更新场景

        参数:
            user_id: 用户ID
            scene_id: 场景ID（必填）
            scene_name, scene_content, scene_object, location: 可选更新字段

        返回:
            成功: 更新后的 Scene 对象
            失败: (错误信息, 状态码)
        """
        try:
            from sql import User, Plot, Storyline, Opera

            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            if not scene_id:
                return ("Missing required field: scene_id", 400)

            scene = Scene.query.get(scene_id)
            if not scene:
                return ("Scene not found", 404)

            # 权限校验（通过剧情链或直接比较所有者）
            if scene.user_id != user_id:
                plot = Plot.query.get(scene.plot_id)
                if not plot:
                    return ("Plot not found", 404)
                storyline = Storyline.query.get(plot.storyline_id)
                if not storyline:
                    return ("Storyline not found", 404)
                opera = Opera.query.get(storyline.opera_id)
                if not opera or opera.user_id != user_id:
                    return ("Permission denied: You do not own this scene", 403)

            # 校验长度
            if scene_name is not None:
                if not scene_name.strip():
                    return ("Scene name cannot be empty", 400)
                if len(scene_name) > 255:
                    return ("Scene name must be less than 255 characters", 400)
            if scene_content is not None and len(scene_content) > 500:
                return ("Scene content must be less than 500 characters", 400)
            if location is not None and len(location) > 255:
                return ("Location must be less than 255 characters", 400)

            # 更新
            if scene_name is not None:
                scene.scene_name = scene_name.strip()
            if scene_content is not None:
                scene.scene_content = scene_content
            if scene_object is not None:
                scene.scene_object = scene_object
            if location is not None:
                scene.location = location

            db.session.commit()
            return scene

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            db.session.rollback()
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def delete_scene_core(user_id, scene_id):
        """
        删除指定场景，并级联删除该场景下的所有场景图片

        参数:
            user_id: 用户ID
            scene_id: 场景ID

        返回:
            成功: 被删除的 Scene 对象
            失败: (错误信息, 状态码)
        """
        try:
            from sql import User, Plot, Storyline, Opera
            from sql.scene_image_db import SceneImage

            if not scene_id:
                return ("Missing required field: scene_id", 400)

            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            scene = Scene.query.get(scene_id)
            if not scene:
                return ("Scene not found", 404)

            # 权限校验
            if scene.user_id != user_id:
                plot = Plot.query.get(scene.plot_id)
                if not plot:
                    return ("Plot not found", 404)
                storyline = Storyline.query.get(plot.storyline_id)
                if not storyline:
                    return ("Storyline not found", 404)
                opera = Opera.query.get(storyline.opera_id)
                if not opera or opera.user_id != user_id:
                    return ("Permission denied: You do not own this scene", 403)

            deleted_scene = scene

            # 先删除该场景的所有图片
            images = SceneImage.query.filter_by(scene_id=scene.scene_id).all()
            for img in images:
                db.session.delete(img)

            # 再删除场景
            db.session.delete(scene)
            db.session.commit()

            return deleted_scene

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            db.session.rollback()
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def get_scenes_by_plot(user_id, plot_id):
        """
        获取指定剧情大纲(plot_id)下的所有场景列表

        参数:
            user_id: 用户ID（用于权限校验）
            plot_id: 剧情大纲ID

        返回:
            成功: [ { scene 数据字典 }, ... ]
            失败: (错误信息, 状态码)
        """
        try:
            from sql import User, Plot, Storyline, Opera

            # 校验入参
            if not plot_id:
                return ("Missing required field: plot_id", 400)

            # 用户存在性
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 权限链路
            plot = Plot.query.get(plot_id)
            if not plot:
                return ("Plot not found", 404)
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this plot", 403)

            # 查询场景
            scenes = Scene.query.filter_by(plot_id=plot_id).order_by(Scene.scene_id.asc()).all()
            scene_list = []
            for sc in scenes:
                scene_list.append({
                    'scene_id': sc.scene_id,
                    'plot_id': sc.plot_id,
                    'user_id': sc.user_id,
                    'scene_name': sc.scene_name,
                    'scene_content': sc.scene_content,
                    'scene_object': sc.scene_object,
                    'location': sc.location
                })

            return scene_list

        except SQLAlchemyError as e:
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def get_scene_core(user_id, scene_id):
        """
        获取单个场景详情

        参数:
            user_id: 用户ID（用于权限校验）
            scene_id: 场景ID

        返回:
            成功: Scene 对象
            失败: (错误信息, 状态码)
        """
        try:
            from sql import User, Plot, Storyline, Opera

            if not scene_id:
                return ("Missing required field: scene_id", 400)

            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            scene = Scene.query.get(scene_id)
            if not scene:
                return ("Scene not found", 404)

            # 权限校验（链路）
            if scene.user_id != user_id:
                plot = Plot.query.get(scene.plot_id)
                if not plot:
                    return ("Plot not found", 404)
                storyline = Storyline.query.get(plot.storyline_id)
                if not storyline:
                    return ("Storyline not found", 404)
                opera = Opera.query.get(storyline.opera_id)
                if not opera or opera.user_id != user_id:
                    return ("Permission denied: You do not own this scene", 403)

            return scene

        except SQLAlchemyError as e:
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def delete_scenes_by_plot_ids(user_id, plot_ids):
        """
        删除指定 plot_ids 列表下的所有场景

        参数:
            user_id: 用户ID
            plot_ids: 剧情大纲ID列表

        返回:
            成功: (True, "Scenes deleted successfully")
            失败: (False, 错误信息)
        """
        try:
            from sql import User, Plot, Storyline, Opera
            from sql.scene_image_db import SceneImage
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return (False, "User not found")

            # 验证必填参数
            if not plot_ids:
                return (True, "No plot_ids provided")

            # 验证所有权
            plots = Plot.query.filter(Plot.plot_id.in_(plot_ids)).all()
            for plot in plots:
                if plot.user_id != user_id:
                    return (False, f"Permission denied: You do not own plot {plot.plot_id}")

            # 找到所有相关的 scene_id
            scenes_to_delete = Scene.query.filter(Scene.plot_id.in_(plot_ids)).all()
            if not scenes_to_delete:
                return (True, "No scenes to delete")

            scene_ids = [scene.scene_id for scene in scenes_to_delete]

            # 删除所有关联的 SceneImage
            SceneImage.query.filter(SceneImage.scene_id.in_(scene_ids)).delete(synchronize_session=False)

            # 删除所有相关的 Scene
            Scene.query.filter(Scene.plot_id.in_(plot_ids)).delete(synchronize_session=False)
            
            db.session.commit()

            return (True, "Scenes and associated images deleted successfully")

        except SQLAlchemyError as e:
            db.session.rollback()
            return (False, f'Database error: {str(e)}')
        except Exception as e:
            db.session.rollback()
            return (False, f'Server error: {str(e)}')