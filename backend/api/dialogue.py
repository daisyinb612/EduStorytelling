from datetime import date  # 用于处理日期
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sql.opera_db import Opera
from sql.dialogue_db import Dialogue
from sql.storyline_db import Storyline
from sql.plot_db import Plot
from sql import db
from . import api_bp
import base64


@api_bp.route('/dialogue/generate_from_plot', methods=['POST'])
@jwt_required()
def generate_dialogue_from_plot_route():
    """
    根据情节ID生成对话的接口
    
    请求参数:
        plot_id: 情节ID（必填）
    
    返回:
        成功: 201状态码和新创建的对话信息
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    
    # 从请求数据中提取plot_id
    plot_id = data.get('plot_id')
    
    # 验证必填参数
    if not plot_id:
        return jsonify({'msg': 'Missing required field: plot_id'}), 400
    
    try:
        # 调用核心函数生成对话
        result = Dialogue.generate_dialogue_from_plot_core(
            user_id=current_user_id,
            plot_id=plot_id
        )
        
        if isinstance(result, Dialogue):
            # 成功创建，返回对话信息
            return jsonify({
                'msg': 'Dialogue generated successfully',
                'dialogue': {
                    'dialogue_id': result.dialogue_id,
                    'storyline_id': result.storyline_id,
                    'plot_id': result.plot_id,
                    'dialogue_count': len(result.dialogue_content) if result.dialogue_content else 0,
                    'dialogue_content': result.dialogue_content
                }
            }), 201
        else:
            # 生成失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/dialogue/get/<int:dialogue_id>', methods=['GET'])
@jwt_required()
def get_dialogue_route(dialogue_id):
    """
    获取指定对话的接口
    
    参数:
        dialogue_id: 对话ID（路径参数）
    
    返回:
        成功: 200状态码和对话信息
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    
    try:
        # 调用核心函数获取对话
        result = Dialogue.get_dialogue_by_id_core(current_user_id, dialogue_id)

        if isinstance(result, tuple):
            # 获取失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
        
        dialogue = result
        
        # 获取关联的情节和故事概要信息
        plot = Plot.query.get(dialogue.plot_id)
        storyline = Storyline.query.get(dialogue.storyline_id)
        
        return jsonify({
            'msg': 'Dialogue retrieved successfully',
            'data': {
                'dialogue_id': dialogue.dialogue_id,
                'plot_id': dialogue.plot_id,
                'plot_name': plot.plot_name if plot else None,
                'storyline_id': dialogue.storyline_id,
                'dialogue_content': dialogue.dialogue_content,
                'storyline_theme': storyline.theme if storyline else None,
                'storyline_name': storyline.storyline_name if storyline else None,
            }
        }), 200
        
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/dialogue/update/<int:dialogue_id>', methods=['PUT'])
@jwt_required()
def update_dialogue_route(dialogue_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    dialogue_content = data.get('dialogue_content')

    result = Dialogue.update_dialogue_core(current_user_id, dialogue_id, dialogue_content)

    if isinstance(result, tuple):
        msg, status_code = result
        return jsonify({'msg': msg}), status_code

    dialogue = result
    plot = Plot.query.get(dialogue.plot_id)
    storyline = Storyline.query.get(plot.storyline_id) if plot else None

    return jsonify({
        'msg': 'Dialogue updated successfully',
        'data': {
            'dialogue_id': dialogue.dialogue_id,
            'plot_id': dialogue.plot_id,
            'storyline_id': dialogue.storyline_id,
            'dialogue_content': dialogue.dialogue_content,
            'storyline_theme': storyline.theme if storyline else None,
            'storyline_name': storyline.storyline_name if storyline else None,
            'updated_at': dialogue.updated_at.isoformat()
        }
    }), 200


@api_bp.route('/dialogue/get_by_plot/<int:plot_id>', methods=['GET'])
@jwt_required()
def get_dialogue_by_plot_route(plot_id):
    current_user_id = int(get_jwt_identity())
    try:
        # 调用核心函数获取对话
        result = Dialogue.get_dialogue_by_plot_id_core(current_user_id, plot_id)

        if isinstance(result, tuple):
            msg, status_code = result
            return jsonify({'msg': msg}), status_code

        dialogue = result
        storyline = Storyline.query.get(dialogue.storyline_id)
        plot = Plot.query.get(dialogue.plot_id)

        return jsonify({
            'msg': 'Dialogue found',
            'data': {
                'dialogue_id': dialogue.dialogue_id,
                'plot_id': dialogue.plot_id,
                'plot_name': plot.plot_name if plot else None,
                'storyline_id': dialogue.storyline_id,
                'dialogue_content': dialogue.dialogue_content,
                'storyline_theme': storyline.theme if storyline else None,
                'storyline_name': storyline.storyline_name if storyline else None
            }
        }), 200

    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/dialogue/get_previous/<int:dialogue_id>', methods=['GET'])
@jwt_required()
def get_previous_dialogue_route(dialogue_id):
    current_user_id = int(get_jwt_identity())
    result = Dialogue.get_previous_dialogue_core(current_user_id, dialogue_id)

    if isinstance(result, tuple):
        msg, status_code = result
        return jsonify({'msg': msg}), status_code

    if result:
        storyline = Storyline.query.get(result.storyline_id)
        return jsonify({
            'msg': 'Previous dialogue found',
            'data': {
                'dialogue_id': result.dialogue_id,
                'plot_id': result.plot_id,
                'storyline_id': result.storyline_id,
                'dialogue_content': result.dialogue_content,
                'storyline_theme': storyline.theme if storyline else None,
                'storyline_name': storyline.storyline_name if storyline else None
            }
        }), 200
    else:
        return jsonify({'msg': 'No previous dialogue found'}), 404


@api_bp.route('/dialogue/delete/<int:dialogue_id>', methods=['DELETE'])
@jwt_required()
def delete_dialogue_route(dialogue_id):
    """
    删除指定对话的接口
    
    参数:
        dialogue_id: 要删除的对话ID（路径参数）
    
    返回:
        成功: 200状态码和删除成功的消息
        失败: 相应的错误状态码和错误消息
    """
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())
    
    try:
        # 调用核心删除函数
        result = Dialogue.delete_dialogue_core(
            user_id=current_user_id,
            dialogue_id=dialogue_id
        )
        
        if isinstance(result, Dialogue):
            # 成功删除，获取关联信息
            plot = Plot.query.get(result.plot_id)
            storyline = Storyline.query.get(result.storyline_id)
            
            return jsonify({
                'msg': 'Dialogue deleted successfully',
                'deleted_dialogue': {
                    'dialogue_id': result.dialogue_id,
                    'storyline_id': result.storyline_id,
                    'plot_id': result.plot_id,
                    'plot_name': plot.plot_name if plot else None,
                    'storyline_theme': storyline.theme if storyline else None,
                    'dialogue_count': len(result.dialogue_content) if result.dialogue_content else 0,
                    'had_content': result.dialogue_content is not None
                }
            }), 200
        else:
            # 删除失败，返回错误信息
            message, status_code = result
            return jsonify({'msg': message}), status_code
            
    except Exception as e:
        return jsonify({'msg': f'Server error: {str(e)}'}), 500


@api_bp.route('/dialogue/generate_from_storyline', methods=['POST'])
@jwt_required()
def generate_dialogues_from_storyline_route():
    """
    接收故事概要ID，并为该故事概要下的所有剧情（Plot）批量生成对话。

    请求参数:
        storyline_id: 故事概要ID（必填）

    返回:
        成功: 200状态码，包含生成结果的摘要信息
        失败: 相应的错误状态码和错误消息
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # 从请求数据中提取storyline_id
    storyline_id = data.get('storyline_id')

    # 验证storyline_id是否存在
    if not storyline_id:
        return jsonify({'msg': 'Missing required field: storyline_id'}), 400

    try:
        # 验证故事概要是否存在及权限
        storyline = Storyline.query.get(storyline_id)
        if not storyline:
            return jsonify({'msg': 'Storyline not found'}), 404

        opera = Opera.query.get(storyline.opera_id)
        if opera.user_id != current_user_id:
            return jsonify({'msg': 'Permission denied: You do not own this storyline'}), 403

        # 获取该故事概要下的所有剧情
        plots = Plot.query.filter_by(storyline_id=storyline_id).order_by(Plot.plot_id.asc()).all()
        if not plots:
            return jsonify({
                'msg': 'No plots found for this storyline',
                'storyline_id': storyline_id,
                'storyline_theme': storyline.theme,
                'storyline_name': storyline.storyline_name
            }), 404

        # 为每个剧情生成对话
        generated_dialogues = []
        for plot in plots:
            # 调用核心函数生成对话
            result = Dialogue.generate_dialogue_from_plot_core(
                user_id=current_user_id,
                plot_id=plot.plot_id,
            )
            if not isinstance(result, tuple):
                generated_dialogues.append({
                    'plot_id': plot.plot_id,
                    'dialogue_id': result.dialogue_id,
                    'dialogue_content': result.dialogue_content
                })

        # 返回生成结果
        return jsonify({
            'msg': 'Dialogues generated successfully from storyline',
            'storyline_id': storyline_id,
            'storyline_theme': storyline.theme,
            'storyline_name': storyline.storyline_name,
            'generated_dialogues_count': len(generated_dialogues),
            'generated_dialogues': generated_dialogues
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Failed to generate dialogues: {str(e)}'}), 500