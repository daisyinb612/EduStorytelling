from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from agent.llm import global_llm
from sql import *
import requests
import base64
from . import api_bp
from agent.prompt import PROMPT
from sql.character_image_db import CharacterImage
from sql import db


@api_bp.route('/character/generate_image', methods=['POST'])
@jwt_required()
def generate_character_image_route():
    """
    生成角色图片的接口
    
    请求参数:
        character_id: 角色ID（必填）
        character_prompt: 角色描述提示词（可选）
        style: 图片风格（可选）
    
    返回:
        成功: 201状态码和新创建的角色图片信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    character_id = data.get('character_id')
    character_prompt = data.get('character_prompt', '')
    style = data.get('style', '')
    
    # 验证必填参数
    if not character_id:
        return jsonify({'msg': 'Missing required field: character_id'}), 400
    
    try:
        # 验证角色是否存在并获取角色信息
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'msg': 'Character not found'}), 404
        
        # 验证用户权限
        if character.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this character'}), 403
        
        # 构建完整的图片生成提示词
        full_prompt = character_prompt or f"A character named {character.character_name}"
        if character.appearance:
            full_prompt += f", appearance: {character.appearance}"
        if character.personality:
            full_prompt += f", personality: {character.personality}"
        if style:
            full_prompt += f", style: {style}"
        
        # 获取故事概要信息用于传递给LLM
        storyline = Storyline.query.get(character.storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
        
        # 调用LLM生成图片
        image_url = global_llm.create_picture(
            prompt=full_prompt,
            user_id=current_user_id,
            opera_id=storyline.opera_id
        )
        
        if not image_url:
            print('Failed to generate image')
            return jsonify({'msg': 'Failed to generate image'}), 500
        
        # 上传到代码仓库并获取可访问的 URL
        try:
            ok, uploaded_url_or_err = CharacterImage.upload_picture(
                image_url=image_url,
                target_dir='character_image'
            )
            if not ok:
                print('Failed to upload image to repo: ', uploaded_url_or_err)
                return jsonify({'msg': uploaded_url_or_err}), 500
            uploaded_url = uploaded_url_or_err
        except Exception as e:
            print('Failed to upload image to repo: ', e)
            return jsonify({'msg': f'Failed to upload image to repository: {str(e)}'}), 500
        
        # 调用核心函数创建角色图片记录（直接保存为 URL 字符串）
        result = CharacterImage.create_character_image_core(
            user_id=current_user_id,
            character_id=character_id,
            character_prompt=full_prompt,
            style=style,
            character_image=uploaded_url
        )
        
        if isinstance(result, CharacterImage):
            # 成功创建，返回角色图片信息
            return jsonify({
                'msg': 'Character image generated successfully',
                'character_image': {
                    'character_image_id': result.character_image_id,
                    'character_id': result.character_id,
                    'character_prompt': result.character_prompt,
                    'style': result.style,
                    'image_url': uploaded_url,
                    'character_name': character.character_name
                }
            }), 201
        else:
            # 创建失败，返回错误信息
            message, status_code = result
            print('create character image failed: ', message)
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        print('create character image failed: ', e)
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/character/get_image/<int:character_image_id>', methods=['GET'])
@jwt_required()
def get_character_image_route(character_image_id):
    """
    获取角色图片的接口
    
    参数:
        character_image_id: 角色图片ID（路径参数）
    
    返回:
        成功: 200状态码和角色图片的base64编码数据
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        # 查找角色图片
        character_image = CharacterImage.query.get(character_image_id)
        if not character_image:
            return jsonify({'msg': 'Character image not found'}), 404
        
        # 验证用户权限
        if character_image.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this character image'}), 403
        
        # 获取关联的角色信息
        character = Character.query.get(character_image.character_id)
        
        # 角色图片字段为 URL：下载并转为 base64
        image_base64 = None
        if character_image.character_image:
            image_url = str(character_image.character_image).strip()
            try:
                resp = requests.get(image_url, timeout=30)
                resp.raise_for_status()
                image_base64 = base64.b64encode(resp.content).decode('utf-8')
            except Exception as e:
                return jsonify({'msg': f'Failed to download image from url: {str(e)}'}), 500
        
        return jsonify({
            'msg': 'Character image retrieved successfully',
            'character_image': {
                'character_image_id': character_image.character_image_id,
                'character_id': character_image.character_id,
                'character_name': character.character_name if character else None,
                'character_prompt': character_image.character_prompt,
                'style': character_image.style,
                'image_url': str(character_image.character_image) if character_image.character_image else None,
                'image_data': image_base64
            }
        }), 200
        
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/character/get_images/<int:character_id>', methods=['GET'])
@jwt_required()
def get_character_images_by_character_route(character_id):
    """
    获取指定角色的所有图片列表
    
    参数:
        character_id: 角色ID（路径参数）
    
    返回:
        成功: 200状态码和角色图片列表
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        # 验证角色是否存在
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'msg': 'Character not found'}), 404
        
        # 验证用户权限
        if character.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this character'}), 403
        
        # 查询该角色的所有图片
        character_images = CharacterImage.query.filter_by(character_id=character_id).order_by(CharacterImage.character_image_id.desc()).all()
        
        # 构造返回数据
        image_list = []
        for img in character_images:
            image_list.append({
                'character_image_id': img.character_image_id,
                'character_id': img.character_id,
                'character_prompt': img.character_prompt,
                'style': img.style,
                'image_url': str(img.character_image) if img.character_image else None
            })
        
        return jsonify({
            'msg': 'Character images retrieved successfully',
            'character_id': character_id,
            'character_name': character.character_name,
            'total_images': len(image_list),
            'images': image_list
        }), 200
        
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/character/update_image/<int:character_image_id>', methods=['PUT'])
@jwt_required()
def update_character_image_route(character_image_id):
    """
    更新角色图片的接口（更新prompt、style并重新生成图片）
    
    参数:
        character_image_id: 角色图片ID（路径参数）
    
    请求参数:
        character_prompt: 新的角色描述提示词（可选）
        style: 新的图片风格（可选）
        regenerate_image: 是否重新生成图片（可选，默认true）
    
    返回:
        成功: 200状态码和更新后的角色图片信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    character_prompt = data.get('character_prompt')
    style = data.get('style')
    regenerate_image = data.get('regenerate_image', True)  # 默认重新生成图片
    
    try:
        # 首先获取现有的角色图片记录
        character_image = CharacterImage.query.get(character_image_id)
        if not character_image:
            return jsonify({'msg': 'Character image not found'}), 404
        
        # 验证用户权限
        if character_image.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this character image'}), 403
        
        # 获取关联的角色信息
        character = Character.query.get(character_image.character_id)
        if not character:
            return jsonify({'msg': 'Associated character not found'}), 404
        
        # 准备更新的数据（URL 方式）
        new_image_url = None
        
        # 如果需要重新生成图片
        if regenerate_image:
            # 构建完整的图片生成提示词
            # 使用新的prompt，如果没有提供则使用现有的
            full_prompt = character_prompt or character_image.character_prompt
            if not full_prompt:
                full_prompt = f"A character named {character.character_name}"
            
            # 添加角色的基本信息
            if character.appearance:
                full_prompt += f", appearance: {character.appearance}"
            if character.personality:
                full_prompt += f", personality: {character.personality}"
            
            # 使用新的风格，如果没有提供则使用现有的
            current_style = style if style is not None else character_image.style
            if current_style:
                full_prompt += f", style: {current_style}"
            
            # 获取故事概要信息用于传递给LLM
            storyline = Storyline.query.get(character.storyline_id)
            if not storyline:
                return jsonify({'msg': 'Storyline not found'}), 404
            
            # 调用LLM生成新图片 URL
            image_url = global_llm.create_picture(
                prompt=full_prompt,
                user_id=current_user_id,
                opera_id=storyline.opera_id
            )
            
            if not image_url:
                return jsonify({'msg': 'Failed to generate new image'}), 500
            
            # 上传到代码仓库，得到可访问 URL
            try:
                ok, uploaded_url_or_err = CharacterImage.upload_picture(
                    image_url=image_url,
                    target_dir='character_image'
                )
                if not ok:
                    return jsonify({'msg': uploaded_url_or_err}), 500
                new_image_url = uploaded_url_or_err
            except Exception as e:
                return jsonify({'msg': f'Failed to upload image to repository: {str(e)}'}), 500
        
        # 调用核心函数更新角色图片记录（以 URL 字符串存入 character_image 字段）
        result = CharacterImage.update_character_image_core(
            user_id=current_user_id,
            character_image_id=character_image_id,
            character_prompt=character_prompt,
            style=style,
            character_image=new_image_url
        )
        
        if isinstance(result, CharacterImage):
            # 成功更新，构建返回数据
            response_data = {
                'msg': 'Character image updated successfully',
                'character_image': {
                    'character_image_id': result.character_image_id,
                    'character_id': result.character_id,
                    'character_prompt': result.character_prompt,
                    'style': result.style,
                    'character_name': character.character_name
                }
            }
            
            # 如果重新生成了图片，包含新的图片URL
            if regenerate_image and new_image_url:
                response_data['character_image']['new_image_url'] = new_image_url
                response_data['msg'] = 'Character image updated and regenerated successfully'
            
            return jsonify(response_data), 200
        else:
            # 更新失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/character/delete_image/<int:character_image_id>', methods=['DELETE'])
@jwt_required()
def delete_character_image_route(character_image_id):
    """
    删除指定角色图片的接口
    
    参数:
        character_image_id: 要删除的角色图片ID（路径参数）
    
    返回:
        成功: 200状态码和删除成功的消息
        失败: 相应的错误状态码和错误消息
    """
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())
    
    # 调用核心删除函数
    result = CharacterImage.delete_character_image_core(
        user_id=current_user_id,
        character_image_id=character_image_id
    )
    
    if isinstance(result, CharacterImage):
        # 成功删除，返回被删除的角色图片信息
        # 获取关联的角色信息
        character = Character.query.get(result.character_id)
        
        return jsonify({
            'msg': 'Character image deleted successfully',
            'deleted_character_image': {
                'character_image_id': result.character_image_id,
                'character_id': result.character_id,
                'character_name': character.character_name if character else None,
                'character_prompt': result.character_prompt,
                'style': result.style,
                'had_image_data': result.character_image is not None
            }
        }), 200
    else:
        # 删除失败，返回错误信息
        message, status_code = result
        return jsonify({'msg': message}), status_code
