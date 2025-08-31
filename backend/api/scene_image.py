from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from agent.llm import global_llm
from sql import *
import requests
import base64
from . import api_bp
from agent.prompt import PROMPT
from sql.scene_image_db import SceneImage
from sql import db


@api_bp.route('/scene/generate_image', methods=['POST'])
@jwt_required()
def generate_scene_image_route():
    """
    生成场景图片的接口
    
    请求参数:
        scene_id: 场景ID（必填）
        scene_prompt: 场景描述提示词（可选）
        style: 图片风格（可选）
    
    返回:
        成功: 201状态码和新创建的场景图片信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    scene_id = data.get('scene_id')
    scene_prompt = data.get('scene_prompt', '')
    style = data.get('style', '')
    
    # 验证必填参数
    if not scene_id:
        return jsonify({'msg': 'Missing required field: scene_id'}), 400
    
    try:
        # 验证场景是否存在并获取场景信息
        scene = Scene.query.get(scene_id)
        if not scene:
            return jsonify({'msg': 'Scene not found'}), 404
        
        # 获取关联的情节信息
        plot = Plot.query.get(scene.plot_id)
        if not plot:
            return jsonify({'msg': 'Plot not found'}), 404
        
        # 获取故事概要信息
        storyline = Storyline.query.get(plot.storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
        
        # 验证用户权限（通过剧本验证）
        opera = Opera.query.get(storyline.opera_id)
        if not opera or opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this scene'}), 403
        
        # 构建完整的图片生成提示词
        full_prompt = scene_prompt or f"A scene from plot '{plot.plot_name}'"
        if plot.abstract:
            full_prompt += f", plot description: {plot.abstract}"
        if storyline.theme:
            full_prompt += f", theme: {storyline.theme}"
        if storyline.classtype:
            full_prompt += f", type: {storyline.classtype}"
        if storyline.storyline_name:
            full_prompt += f", name: {storyline.storyline_name}"
        if style:
            full_prompt += f", style: {style}"
        
        # 调用LLM生成图片
        image_url = global_llm.create_picture(
            prompt=full_prompt,
            user_id=current_user_id,
            opera_id=opera.opera_id
        )
        
        if not image_url:
            return jsonify({'msg': 'Failed to generate image'}), 500
        
        # 上传到代码仓库并获取可访问URL
        try:
            ok, uploaded_url_or_err = SceneImage.upload_picture(
                image_url=image_url,
                target_dir='scene_image'
            )
            if not ok:
                print('Failed to upload scene image to repo: ', uploaded_url_or_err)
                return jsonify({'msg': uploaded_url_or_err}), 500
            uploaded_url = uploaded_url_or_err
        except Exception as e:
            return jsonify({'msg': f'Failed to upload image to repository: {str(e)}'}), 500
        
        # 调用核心函数创建场景图片记录（保存 URL 字符串）
        result = SceneImage.create_scene_image_core(
            user_id=current_user_id,
            scene_id=scene_id,
            scene_prompt=full_prompt,
            style=style,
            scene_image=uploaded_url
        )
        
        if isinstance(result, SceneImage):
            # 成功创建，返回场景图片信息
            return jsonify({
                'msg': 'Scene image generated successfully',
                'scene_image': {
                    'scene_image_id': result.scene_image_id,
                    'scene_id': result.scene_id,
                    'scene_prompt': result.scene_prompt,
                    'style': result.style,
                    'image_url': uploaded_url,
                    'plot_name': plot.plot_name,
                    'storyline_theme': storyline.theme
                }
            }), 201
        else:
            # 创建失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/scene/get_image/<int:scene_image_id>', methods=['GET'])
@jwt_required()
def get_scene_image_route(scene_image_id):
    """
    获取场景图片的接口
    
    参数:
        scene_image_id: 场景图片ID（路径参数）
    
    返回:
        成功: 200状态码和场景图片的base64编码数据
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        # 查找场景图片
        scene_image = SceneImage.query.get(scene_image_id)
        if not scene_image:
            return jsonify({'msg': 'Scene image not found'}), 404
        
        # 验证用户权限（通过场景->情节->故事概要->剧本的关联链验证）
        scene = Scene.query.get(scene_image.scene_id)
        if not scene:
            return jsonify({'msg': 'Scene not found'}), 404
            
        plot = Plot.query.get(scene.plot_id)
        if not plot:
            return jsonify({'msg': 'Plot not found'}), 404
            
        storyline = Storyline.query.get(plot.storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
            
        opera = Opera.query.get(storyline.opera_id)
        if not opera or opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this scene image'}), 403
        
        # 将 URL 下载后转为 base64
        image_base64 = None
        if scene_image.scene_image:
            image_url = str(scene_image.scene_image).strip()
            try:
                resp = requests.get(image_url, timeout=30)
                resp.raise_for_status()
                image_base64 = base64.b64encode(resp.content).decode('utf-8')
            except Exception as e:
                return jsonify({'msg': f'Failed to download image from url: {str(e)}'}), 500
        
        return jsonify({
            'msg': 'Scene image retrieved successfully',
            'scene_image': {
                'scene_image_id': scene_image.scene_image_id,
                'scene_id': scene_image.scene_id,
                'plot_name': plot.plot_name,
                'storyline_theme': storyline.theme,
                'scene_prompt': scene_image.scene_prompt,
                'style': scene_image.style,
                'image_url': str(scene_image.scene_image) if scene_image.scene_image else None,
                'image_data': image_base64
            }
        }), 200
        
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/scene/get_images/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_scene_images_by_scene_route(scene_id):
    """
    获取指定场景的所有图片列表
    
    参数:
        scene_id: 场景ID（路径参数）
    
    返回:
        成功: 200状态码和场景图片列表
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        # 验证场景是否存在
        scene = Scene.query.get(scene_id)
        if not scene:
            return jsonify({'msg': 'Scene not found'}), 404
        
        # 获取关联的情节信息
        plot = Plot.query.get(scene.plot_id)
        if not plot:
            return jsonify({'msg': 'Plot not found'}), 404
        
        # 获取故事概要信息
        storyline = Storyline.query.get(plot.storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
        
        # 验证用户权限（通过剧本验证）
        opera = Opera.query.get(storyline.opera_id)
        if not opera or opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this scene'}), 403
        
        # 查询该场景的所有图片
        scene_images = SceneImage.query.filter_by(scene_id=scene_id).order_by(SceneImage.scene_image_id.desc()).all()
        
        # 构造返回数据（包含每张图片的 base64）
        image_list = []
        for img in scene_images:
            item = {
                'scene_image_id': img.scene_image_id,
                'scene_id': img.scene_id,
                'scene_prompt': img.scene_prompt,
                'style': img.style,
                'scene_image_url': str(img.scene_image) if img.scene_image else None
            }
            image_base64 = None
            if item['scene_image_url']:
                try:
                    resp = requests.get(item['scene_image_url'], timeout=30)
                    resp.raise_for_status()
                    image_base64 = base64.b64encode(resp.content).decode('utf-8')
                except Exception:
                    image_base64 = None
            item['image_data'] = image_base64
            image_list.append(item)
        
        return jsonify({
            'msg': 'Scene images retrieved successfully',
            'scene_id': scene_id,
            'plot_name': plot.plot_name,
            'storyline_theme': storyline.theme,
            'total_images': len(image_list),
            'images': image_list
        }), 200
        
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/scene/update_image/<int:scene_image_id>', methods=['PUT'])
@jwt_required()
def update_scene_image_route(scene_image_id):
    """
    更新场景图片的接口（更新prompt、style并重新生成图片）
    
    参数:
        scene_image_id: 场景图片ID（路径参数）
    
    请求参数:
        scene_prompt: 新的场景描述提示词（可选）
        style: 新的图片风格（可选）
        regenerate_image: 是否重新生成图片（可选，默认true）
    
    返回:
        成功: 200状态码和更新后的场景图片信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    scene_prompt = data.get('scene_prompt')
    style = data.get('style')
    regenerate_image = data.get('regenerate_image', True)  # 默认重新生成图片
    
    try:
        # 首先获取现有的场景图片记录
        scene_image = SceneImage.query.get(scene_image_id)
        if not scene_image:
            return jsonify({'msg': 'Scene image not found'}), 404
        
        # 获取关联的场景、情节、故事概要和剧本信息
        scene = Scene.query.get(scene_image.scene_id)
        if not scene:
            return jsonify({'msg': 'Scene not found'}), 404
            
        plot = Plot.query.get(scene.plot_id)
        if not plot:
            return jsonify({'msg': 'Plot not found'}), 404
            
        storyline = Storyline.query.get(plot.storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
            
        opera = Opera.query.get(storyline.opera_id)
        if not opera or opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this scene image'}), 403
        
        # 准备更新的数据（URL 方式）
        new_image_url = None
        image_url = None
        
        # 如果需要重新生成图片
        if regenerate_image:
            # 构建完整的图片生成提示词
            # 使用新的prompt，如果没有提供则使用现有的
            full_prompt = scene_prompt or scene_image.scene_prompt
            if not full_prompt:
                full_prompt = f"A scene from plot '{plot.plot_name}'"
            
            # 添加情节和故事的基本信息
            if plot.abstract:
                full_prompt += f", plot description: {plot.abstract}"
            if storyline.theme:
                full_prompt += f", theme: {storyline.theme}"
            if storyline.classtype:
                full_prompt += f", type: {storyline.classtype}"
            if storyline.storyline_name:
                full_prompt += f", name: {storyline.storyline_name}"
            
            # 使用新的风格，如果没有提供则使用现有的
            current_style = style if style is not None else scene_image.style
            if current_style:
                full_prompt += f", style: {current_style}"
            
            # 调用LLM生成新图片（返回 URL）
            image_url = global_llm.create_picture(
                prompt=full_prompt,
                user_id=current_user_id,
                opera_id=opera.opera_id
            )
            
            if not image_url:
                return jsonify({'msg': 'Failed to generate new image'}), 500
            
            # 上传到代码仓库并获取可访问URL
            try:
                ok, uploaded_url_or_err = SceneImage.upload_picture(
                    image_url=image_url,
                    target_dir='scene_image'
                )
                if not ok:
                    print('Failed to upload scene image to repo: ', uploaded_url_or_err)
                    return jsonify({'msg': uploaded_url_or_err}), 500
                new_image_url = uploaded_url_or_err
            except Exception as e:
                return jsonify({'msg': f'Failed to upload image to repository: {str(e)}'}), 500
        
        # 调用核心函数更新场景图片记录（以 URL 字符串存入 scene_image 字段）
        result = SceneImage.update_scene_image_core(
            user_id=current_user_id,
            scene_image_id=scene_image_id,
            scene_prompt=scene_prompt,
            style=style,
            scene_image=new_image_url
        )
        
        if isinstance(result, SceneImage):
            # 成功更新，构建返回数据
            response_data = {
                'msg': 'Scene image updated successfully',
                'scene_image': {
                    'scene_image_id': result.scene_image_id,
                    'scene_id': result.scene_id,
                    'scene_prompt': result.scene_prompt,
                    'style': result.style,
                    'plot_name': plot.plot_name,
                    'storyline_theme': storyline.theme
                }
            }
            
            # 如果重新生成了图片，包含新的图片URL
            if regenerate_image and new_image_url:
                response_data['scene_image']['new_image_url'] = new_image_url
                response_data['msg'] = 'Scene image updated and regenerated successfully'
            
            return jsonify(response_data), 200
        else:
            # 更新失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/scene/delete_image/<int:scene_image_id>', methods=['DELETE'])
@jwt_required()
def delete_scene_image_route(scene_image_id):
    """
    删除指定场景图片的接口
    
    参数:
        scene_image_id: 要删除的场景图片ID（路径参数）
    
    返回:
        成功: 200状态码和删除成功的消息
        失败: 相应的错误状态码和错误消息
    """
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())
    
    # 调用核心删除函数
    result = SceneImage.delete_scene_image_core(
        user_id=current_user_id,
        scene_image_id=scene_image_id
    )
    
    if isinstance(result, SceneImage):
        # 成功删除，返回被删除的场景图片信息
        # 获取关联的场景和情节信息
        scene = Scene.query.get(result.scene_id)
        plot = None
        storyline = None
        if scene:
            plot = Plot.query.get(scene.plot_id)
            if plot:
                storyline = Storyline.query.get(plot.storyline_id)
        
        return jsonify({
            'msg': 'Scene image deleted successfully',
            'deleted_scene_image': {
                'scene_image_id': result.scene_image_id,
                'scene_id': result.scene_id,
                'plot_name': plot.plot_name if plot else None,
                'storyline_theme': storyline.theme if storyline else None,
                'scene_prompt': result.scene_prompt,
                'style': result.style,
                'had_image_data': result.scene_image is not None
            }
        }), 200
    else:
        # 删除失败，返回错误信息
        message, status_code = result
        return jsonify({'msg': message}), status_code
