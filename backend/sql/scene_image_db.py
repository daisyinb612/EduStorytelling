from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
import requests
import base64
import os
import uuid
import time

from sql import db, User, Scene

class SceneImage(db.Model):
    __tablename__ = 'scene_image'

    scene_image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.scene_id'), nullable=False)
    scene_prompt = db.Column(db.String(500))
    style = db.Column(db.String(500))  # 新增的风格字段
    scene_image = db.Column(db.String(500))

    # 关系：每个场景图片属于一个场景
    scene = relationship('Scene', backref='images')

    def __repr__(self):
        return f"<SceneImage {self.scene_image_id}>"

    @staticmethod
    # 核心业务逻辑函数：创建场景图片数据
    def create_scene_image_core(
            user_id,
            scene_id,
            scene_prompt="",
            style="",
            scene_image=None
    ):
        """
        创建新的场景图片数据（显式参数版本）

        参数:
            user_id: 用户ID
            scene_id: 关联的场景ID（必填）
            scene_prompt: 场景描述提示词（可选，默认空字符串）
            style: 图片风格（可选，默认空字符串）
            scene_image: url

        返回:
            成功: 新创建的场景图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import Plot, Storyline, Opera
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not scene_id:
                return ("Missing required field: scene_id", 400)

            # 验证场景是否存在
            scene = Scene.query.get(scene_id)
            if not scene:
                return ("Scene not found", 404)

            # 验证所有权（通过场景->情节->故事概要->剧本的关联链验证）
            plot = Plot.query.get(scene.plot_id)
            if not plot:
                return ("Plot not found", 404)
                
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this scene", 403)

            # 字段长度校验
            if len(scene_prompt) > 500:
                return ("Scene prompt must be less than 500 characters", 400)
            if len(style) > 500:
                return ("Style must be less than 500 characters", 400)

            # 创建新的场景图片记录
            new_scene_image = SceneImage(
                user_id=user_id,
                scene_id=scene_id,
                scene_prompt=scene_prompt,
                style=style,
                scene_image=scene_image
            )

            # 保存到数据库
            db.session.add(new_scene_image)
            db.session.commit()

            return new_scene_image  # 成功时返回场景图片对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：更新场景图片数据
    def update_scene_image_core(
            user_id,
            scene_image_id,
            scene_prompt=None,
            style=None,
            scene_image=None
    ):
        """
        更新场景图片数据（显式参数版本）

        参数:
            user_id: 用户ID
            scene_image_id: 场景图片ID（必填）
            scene_prompt: 新的场景描述提示词（可选）
            style: 新的图片风格（可选）
            scene_image: 新的图片二进制数据（可选）

        返回:
            成功: 更新后的场景图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import Plot, Storyline, Opera
            
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not scene_image_id:
                return ("Missing required field: scene_image_id", 400)

            # 查询指定的场景图片
            scene_image = SceneImage.query.get(scene_image_id)
            if not scene_image:
                return ("Scene image not found", 404)

            # 验证所有权（通过场景->情节->故事概要->剧本的关联链验证）
            scene = Scene.query.get(scene_image.scene_id)
            if not scene:
                return ("Scene not found", 404)
                
            plot = Plot.query.get(scene.plot_id)
            if not plot:
                return ("Plot not found", 404)
                
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this scene image", 403)

            # 字段长度校验
            if scene_prompt is not None and len(scene_prompt) > 500:
                return ("Scene prompt must be less than 500 characters", 400)
            if style is not None and len(style) > 500:
                return ("Style must be less than 500 characters", 400)

            # 更新字段（只更新提供的字段）
            if scene_prompt is not None:
                scene_image.scene_prompt = scene_prompt
            if style is not None:
                scene_image.style = style
            if scene_image is not None:
                scene_image.scene_image = scene_image

            # 保存到数据库
            db.session.commit()

            return scene_image  # 成功时返回更新后的场景图片对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：删除场景图片
    def delete_scene_image_core(user_id, scene_image_id):
        """
        删除指定的场景图片（显式参数版本）

        参数:
            user_id: 用户ID
            scene_image_id: 要删除的场景图片ID

        返回:
            成功: 被删除的场景图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 运行时导入避免循环导入
            from sql import Plot, Storyline, Opera
            
            # 验证必填参数
            if not scene_image_id:
                return ("Missing required field: scene_image_id", 400)

            # 查找要删除的场景图片
            scene_image = SceneImage.query.get(scene_image_id)
            if not scene_image:
                return ("Scene image not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（通过场景->情节->故事概要->剧本的关联链验证）
            scene = Scene.query.get(scene_image.scene_id)
            if not scene:
                return ("Scene not found", 404)
                
            plot = Plot.query.get(scene.plot_id)
            if not plot:
                return ("Plot not found", 404)
                
            storyline = Storyline.query.get(plot.storyline_id)
            if not storyline:
                return ("Storyline not found", 404)
                
            opera = Opera.query.get(storyline.opera_id)
            if not opera or opera.user_id != user_id:
                return ("Permission denied: You do not own this scene image", 403)

            # 保存场景图片信息用于返回
            deleted_scene_image = scene_image

            # 从数据库删除场景图片
            db.session.delete(scene_image)
            db.session.commit()

            return deleted_scene_image  # 成功时返回被删除的场景图片对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    def upload_picture(image_url, file_name=None, target_dir=None, branch=None):
        """
        从给定的 image_url 下载图片，上传到指定的 GitHub 仓库路径下，并返回上传后的下载链接。

        参数:
            image_url: 需要上传的图片 URL
            file_name: 目标文件名（可选；若不传将自动生成唯一名）
            branch: 分支名（可选，默认从环境变量读取，否则 'main'）

        返回:
            (True, download_url) 或 (False, error_message)
        """
        try:
            # 0) 从环境变量读取目标仓库配置
            repo_owner = os.getenv("GITHUB_REPO_OWNER")
            repo_name = os.getenv("GITHUB_REPO_NAME")
            token = os.getenv("GITHUB_TOKEN")
            branch = branch or os.getenv("GITHUB_BRANCH", "main")

            if not repo_owner or not repo_name or not token:
                return (False, "Missing required env: GITHUB_REPO_OWNER/GITHUB_REPO_NAME/GITHUB_TOKEN")

            # 1) 下载图片
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            file_data = resp.content

            # 2) 生成唯一文件名（固定使用 .png 扩展名）
            if not file_name:
                file_name = f"{int(time.time()*1000)}_{uuid.uuid4().hex}.png"

            # 3) 目标路径拼接
            target_dir = target_dir.strip("/") if target_dir else None
            remote_path = f"{target_dir}/{file_name}" if target_dir else file_name

            # 4) GitHub API URL
            api_base = "https://api.github.com"
            contents_url = f"{api_base}/repos/{repo_owner}/{repo_name}/contents/{remote_path}"

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            }

            # 5) 读取现有文件（若存在则需要 sha）
            sha = None
            get_params = {"ref": branch}
            get_resp = requests.get(contents_url, headers=headers, params=get_params)
            if get_resp.status_code == 200:
                sha = get_resp.json().get("sha")

            # 6) 组装上传数据
            content_b64 = base64.b64encode(file_data).decode("utf-8")
            payload = {
                "message": f"upload {remote_path}",
                "content": content_b64,
                "branch": branch,
            }
            if sha:
                payload["sha"] = sha

            put_resp = requests.put(contents_url, headers=headers, json=payload)
            if put_resp.status_code not in (200, 201):
                return (False, f"GitHub upload failed: {put_resp.status_code} {put_resp.text}")

            content_obj = put_resp.json().get("content") or {}
            download_url = content_obj.get("download_url")
            if not download_url:
                # 兜底用 raw 链接
                download_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{remote_path}"

            return (True, download_url)

        except Exception as e:
            return (False, f"upload_picture error: {str(e)}")