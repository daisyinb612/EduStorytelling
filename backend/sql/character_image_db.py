from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
import requests
import base64
import os
import uuid
import time

from sql import db, User, Character

class CharacterImage(db.Model):
    __tablename__ = 'character_image'

    character_image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.character_id'), nullable=False)
    character_prompt = db.Column(db.String(500))
    style = db.Column(db.String(500))  # 新增的风格字段
    character_image =  db.Column(db.String(1000), nullable=False)

    # 关系：每个角色图片属于一个角色
    character = relationship('Character', backref='images')

    def __repr__(self):
        return f"<CharacterImage {self.character_image_id}>"

    @staticmethod
    # 核心业务逻辑函数：创建角色图片数据
    def create_character_image_core(
            user_id,
            character_id,
            character_prompt="",
            style="",
            character_image=None
    ):
        """
        创建新的角色图片数据（显式参数版本）

        参数:
            user_id: 用户ID
            character_id: 关联的角色ID（必填）
            character_prompt: 角色描述提示词（可选，默认空字符串）
            style: 图片风格（可选，默认空字符串）
            character_image: 图片二进制数据（可选，默认None）

        返回:
            成功: 新创建的角色图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证必填参数
            if not character_id:
                return ("Missing required field: character_id", 400)

            # 验证角色是否存在
            character = Character.query.get(character_id)
            if not character:
                return ("Character not found", 404)

            # 验证所有权（确保用户拥有这个角色）
            if character.user_id != user_id:
                return ("Permission denied: You do not own this character", 403)

            # 字段长度校验
            if len(character_prompt) > 500:
                return ("Character prompt must be less than 500 characters", 400)
            if len(style) > 500:
                return ("Style must be less than 500 characters", 400)

            # 创建新的角色图片记录
            new_character_image = CharacterImage(
                user_id=user_id,
                character_id=character_id,
                character_prompt=character_prompt,
                style=style,
                character_image=character_image
            )

            # 保存到数据库
            db.session.add(new_character_image)
            db.session.commit()

            return new_character_image  # 成功时返回角色图片对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：更新角色图片数据
    def update_character_image_core(
            user_id,
            character_image_id,
            character_prompt=None,
            style=None,
            character_image=None
    ):
        """
        更新角色图片数据（显式参数版本）

        参数:
            user_id: 用户ID
            character_image_id: 要更新的角色图片ID（必填）
            character_prompt: 新的角色描述提示词（可选，None表示不更新）
            style: 新的图片风格（可选，None表示不更新）
            character_image: 新的图片二进制数据（可选，None表示不更新）

        返回:
            成功: 更新后的角色图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 验证必填参数
            if not character_image_id:
                return ("Missing required field: character_image_id", 400)

            # 查找要更新的角色图片
            character_image_obj = CharacterImage.query.get(character_image_id)
            if not character_image_obj:
                return ("Character image not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（确保用户拥有这个角色图片）
            if character_image_obj.user_id != user_id:
                return ("Permission denied: You do not own this character image", 403)

            # 验证关联的角色是否存在
            character = Character.query.get(character_image_obj.character_id)
            if not character:
                return ("Associated character not found", 404)

            # 字段长度校验（只校验提供的字段）
            if character_prompt is not None and len(character_prompt) > 500:
                return ("Character prompt must be less than 500 characters", 400)
            if style is not None and len(style) > 500:
                return ("Style must be less than 500 characters", 400)

            # 更新字段（只更新提供的字段）
            if character_prompt is not None:
                character_image_obj.character_prompt = character_prompt
            if style is not None:
                character_image_obj.style = style
            if character_image is not None:
                character_image_obj.character_image = character_image

            # 提交到数据库
            db.session.commit()

            return character_image_obj  # 成功时返回更新后的角色图片对象

        except SQLAlchemyError as e:
            db.session.rollback()
            return (f'Database error: {str(e)}', 500)
        except Exception as e:
            return (f'Server error: {str(e)}', 500)

    @staticmethod
    # 核心业务逻辑函数：删除角色图片
    def delete_character_image_core(user_id, character_image_id):
        """
        删除指定的角色图片（显式参数版本）

        参数:
            user_id: 用户ID
            character_image_id: 要删除的角色图片ID

        返回:
            成功: 被删除的角色图片对象
            失败: (错误信息, 状态码)
        """
        try:
            # 验证必填参数
            if not character_image_id:
                return ("Missing required field: character_image_id", 400)

            # 查找要删除的角色图片
            character_image = CharacterImage.query.get(character_image_id)
            if not character_image:
                return ("Character image not found", 404)

            # 验证用户是否存在
            user = User.query.get(user_id)
            if not user:
                return ("User not found", 404)

            # 验证所有权（确保用户拥有这个角色图片）
            if character_image.user_id != user_id:
                return ("Permission denied: You do not own this character image", 403)

            # 验证关联的角色是否存在
            character = Character.query.get(character_image.character_id)
            if not character:
                return ("Associated character not found", 404)

            # 保存角色图片信息用于返回
            deleted_character_image = character_image

            # 从数据库删除角色图片
            db.session.delete(character_image)
            db.session.commit()

            return deleted_character_image  # 成功时返回被删除的角色图片对象

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
            target_dir = target_dir.strip("/")
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