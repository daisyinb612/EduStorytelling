from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from agent.llm import global_llm
from sql import *
from . import api_bp
from agent.prompt import PROMPT
from sql.plot_db import Plot
from sql import db
import json
from datetime import datetime


@api_bp.route('/plot/list/<int:storyline_id>', methods=['GET'])
@jwt_required()
def get_plots_by_storyline_route(storyline_id):
    """
    获取指定storyline下的所有剧情大纲接口
    
    路径参数:
        storyline_id: 故事概要ID（必填）
    
    返回:
        成功: 200状态码和剧情大纲列表
        失败: 相应的错误状态码和错误消息
    """
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())
    
    try:
        # 调用数据库核心逻辑函数
        result = Plot.get_plots_by_storyline(current_user_id, storyline_id)
        
        # 检查是否返回错误
        if isinstance(result, tuple):
            error_msg, status_code = result
            return jsonify({'msg': error_msg}), status_code
        
        # 成功获取数据
        plot_list = result
        
        return jsonify({
            'success': True,
            'message': f'Successfully retrieved {len(plot_list)} plots',
            'storyline_id': storyline_id,
            'plots': plot_list,
            'total_count': len(plot_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving plots: {str(e)}'
        }), 500


@api_bp.route('/plot/create', methods=['POST'])
@jwt_required()
def create_plot_route():
    """
    创建新的剧情大纲接口
    
    请求参数:
        storyline_id: 故事概要ID（必填）
        plot_name: 剧情名称（必填）
        abstract: 剧情摘要（可选）
        character: 角色信息JSON（可选）
    
    返回:
        成功: 201状态码和创建的剧情信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    storyline_id = data.get('storyline_id')
    plot_name = data.get('plot_name')
    abstract = data.get('abstract', '')
    character = data.get('character', [])
    
    try:
        # 调用数据库核心逻辑函数
        result = Plot.create_plot_core(
            user_id=current_user_id,
            storyline_id=storyline_id,
            plot_name=plot_name,
            abstract=abstract,
            characters=character
        )
        
        # 检查是否返回错误
        if isinstance(result, tuple):
            error_msg, status_code = result
            return jsonify({'msg': error_msg}), status_code
        
        # 成功创建剧情
        new_plot = result
        
        return jsonify({
            'success': True,
            'message': 'Plot created successfully',
            'plot': {
                'plot_id': new_plot.plot_id,
                'plot_name': new_plot.plot_name,
                'abstract': new_plot.abstract,
                'characters': new_plot.characters,
                'storyline_id': new_plot.storyline_id,
                'user_id': new_plot.user_id
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating plot: {str(e)}'
        }), 500


@api_bp.route('/plot/update/<int:plot_id>', methods=['PUT'])
@jwt_required()
def update_plot_route(plot_id):
    """
    更新剧情大纲接口
    
    路径参数:
        plot_id: 剧情大纲ID（必填）
    
    请求参数:
        plot_name: 剧情名称（可选）
        abstract: 剧情摘要（可选）
        character: 角色信息JSON（可选）
    
    返回:
        成功: 200状态码和更新后的剧情信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段（都是可选的）
    plot_name = data.get('plot_name')
    abstract = data.get('abstract')
    character = data.get('character')
    
    # 检查是否至少提供了一个要更新的字段
    if plot_name is None and abstract is None and character is None:
        return jsonify({'msg': 'At least one field must be provided for update'}), 400
    
    try:
        # 调用数据库核心逻辑函数
        result = Plot.update_plot_core(
            user_id=current_user_id,
            plot_id=plot_id,
            plot_name=plot_name,
            abstract=abstract,
            characters=character
        )
        
        # 检查是否返回错误
        if isinstance(result, tuple):
            error_msg, status_code = result
            return jsonify({'msg': error_msg}), status_code
        
        # 成功更新剧情
        updated_plot = result
        
        return jsonify({
            'success': True,
            'message': 'Plot updated successfully',
            'plot': {
                'plot_id': updated_plot.plot_id,
                'plot_name': updated_plot.plot_name,
                'abstract': updated_plot.abstract,
                'characters': updated_plot.characters,
                'storyline_id': updated_plot.storyline_id,
                'user_id': updated_plot.user_id
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating plot: {str(e)}'
        }), 500


@api_bp.route('/plot/generate', methods=['POST'])
@jwt_required()
def generate_plot_route():
    """
    生成剧情大纲的接口
    
    请求参数:
        opera_id: 剧本ID（必填）
        storyline_id: 故事概要ID（必填）
    
    返回:
        成功: 201状态码和生成的剧情大纲信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取各字段
    opera_id = data.get('opera_id')
    storyline_id = data.get('storyline_id')
    
    # 验证必填参数
    if not opera_id:
        return jsonify({'msg': 'Missing required field: opera_id'}), 400
    if not storyline_id:
        return jsonify({'msg': 'Missing required field: storyline_id'}), 400
    
    try:
        # 验证剧本是否存在并属于当前用户
        opera = Opera.query.get(opera_id)
        if not opera:
            return jsonify({'msg': 'Opera not found'}), 404
        if opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this opera'}), 403
        
        # 验证故事概要是否存在并属于指定剧本
        storyline = Storyline.query.get(storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404
        if storyline.opera_id != opera_id:
            return jsonify({'msg': 'Storyline does not belong to the specified opera'}), 400
        
        # 查找该故事概要下的所有角色
        characters = Character.query.filter_by(storyline_id=storyline_id).order_by(Character.character_id.asc()).all()
        
        if not characters:
            return jsonify({'msg': 'No characters found for this storyline. Please create characters first.'}), 400
        
        # 创建角色名称到ID的映射
        character_name_to_id = {char.character_name: char.character_id for char in characters}
        
        # 整理角色信息为大模型输入格式
        character_list = []
        for char in characters:
            character_info = {
                "name": char.character_name,
                "personality": char.personality or "",
                "appearance": char.appearance or "",
                "related": char.related or []
            }
            character_list.append(character_info)
        
        # 构建输入给大模型的问题
        # 格式：###LOGLINE###: 故事概要内容
        # ###CHARACTERLIST###: 角色列表JSON
        question = f"""###LOGLINE###: {storyline.storyline_content}

###CHARACTERLIST###: {character_list}"""
        
        # 调用LLM生成剧情大纲
        plot_outline = global_llm.ask(
            question,
            global_llm.OUTLINE_PROMPT,
            current_user_id,
            opera_id,
            chat_id=None,
            save_history=True
        )
        
        # 解析LLM返回结果
        plots = global_llm.analyze_answer(plot_outline)
        
        # 验证LLM返回结果
        if not isinstance(plots, list) or len(plots) == 0:
            return jsonify({
                'success': False,
                'message': 'Failed to generate plot outline from LLM'
            }), 500
        
        # 删除旧的plots
        success, message = Plot.delete_plots_by_storyline(current_user_id, storyline_id)
        if not success:
            return jsonify({'success': False, 'message': message}), 500

        created_plots = []
        failed_creations = []
        # 记录索引与成功创建的 plot_id 的映射，便于后续创建场景
        idx_to_plot_id = {}
        
        # 批量创建剧情大纲
        for idx, plot in enumerate(plots):
            try:
                plot_name = plot.get("plotName", f"Plot_{idx + 1}")
                abstract = plot.get("beat", "")
                character_data = plot.get("characters", [])
                
                # 将角色名称列表转换为角色ID列表
                character_ids = [character_name_to_id[name] for name in character_data if name in character_name_to_id]
                
                # 调用创建剧情的核心函数（会自动查询角色）
                result = Plot.create_plot_core(
                    user_id=current_user_id,
                    storyline_id=storyline_id,
                    plot_name=plot_name,
                    characters=character_ids,
                    abstract=abstract
                )
                
                if isinstance(result, Plot):
                    created_plots.append({
                        'plot_id': result.plot_id,
                        'plot_name': result.plot_name,
                        'abstract': result.abstract
                    })
                    idx_to_plot_id[idx] = result.plot_id
                else:
                    err_msg, _ = result
                    failed_creations.append({
                        'plot_name': plot_name,
                        'error': err_msg
                    })
                    
            except Exception as e:
                failed_creations.append({
                    'plot_name': plot.get("plotName", f"Plot_{idx + 1}"),
                    'error': str(e)
                })
        
        # 基于 LLM 输出读取所有场景，去重后逐一新建
        created_scenes = []
        failed_scenes = []
        seen_scene_keys = set()

        for idx, plot in enumerate(plots):
            try:
                scene_obj = (plot or {}).get("scene") or {}
                scene_name = (scene_obj.get("name") or "").strip()
                scene_content = (scene_obj.get("content") or "").strip()

                # 必须有对应成功创建的 plot 才能创建 scene
                if idx not in idx_to_plot_id:
                    continue

                # 去重 key：name + content
                key = f"{scene_name.lower()}||{scene_content.lower()}"
                if not scene_name:
                    continue
                if key in seen_scene_keys:
                    continue

                seen_scene_keys.add(key)

                scene_result = Scene.create_scene_core(
                    user_id=current_user_id,
                    plot_id=idx_to_plot_id[idx],
                    scene_name=scene_name,
                    scene_content=scene_content,
                    scene_object=scene_obj,
                    location=""
                )

                if isinstance(scene_result, Scene):
                    created_scenes.append({
                        'scene_id': scene_result.scene_id,
                        'plot_id': scene_result.plot_id,
                        'scene_name': scene_result.scene_name
                    })
                else:
                    err_msg, _ = scene_result
                    failed_scenes.append({
                        'scene_name': scene_name or f"Scene_{idx+1}",
                        'error': err_msg
                    })
            except Exception as e:
                failed_scenes.append({
                    'scene_name': (plot or {}).get('scene', {}).get('name', f"Scene_{idx+1}"),
                    'error': str(e)
                })

        # 构建最终响应
        return jsonify({
            'success': len(created_plots) > 0,
            'message': f"Successfully generated {len(created_plots)} plots. {len(failed_creations)} failed.",
            'storyline': {
                'storyline_id': storyline_id,
                'storyline_name': storyline.storyline_name,
                'storyline_content': storyline.storyline_content
            },
            'characters_used': [{'name': char['name'], 'personality': char['personality']} for char in character_list],
            'created_plots': created_plots,
            'failed_plots': failed_creations,
            'created_scenes': created_scenes,
            'failed_scenes': failed_scenes,
            'raw_llm_output': plots  # 包含完整的LLM输出供调试使用
        }), 201 if len(created_plots) > 0 else 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating plot: {str(e)}"
        }), 500
