from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from agent.llm import global_llm
from sql import *
from . import api_bp
from agent.prompt import PROMPT
from sql.character_db import Character
from sql import db


# 路由函数：解析请求数据并显式传参
@api_bp.route('/character/create', methods=['POST'])
@jwt_required()
def create_character_route():
    # 获取请求数据和当前用户ID
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    # 从请求数据中提取各字段
    storyline_id = data.get('storyline_id')
    character_name = data.get('character_name')
    appearance = data.get('appearance', '')
    personality = data.get('personality', '')
    related = data.get('related', {})

    # 调用核心函数（显式传递各个参数）
    result = Character.create_character_core(
        user_id=current_user_id,
        storyline_id=storyline_id,
        character_name=character_name,
        appearance=appearance,
        personality=personality,
        related=related
    )

    if isinstance(result, Character):
        # 成功返回新创建的角色信息
        return jsonify({
            'msg': 'Character created successfully',
            'character': {
                'character_id': result.character_id,
                'storyline_id': result.storyline_id,
                'character_name': result.character_name,
                'appearance': result.appearance,
                'personality': result.personality,
                'related': result.related
            }
        }), 201
    else:
        # 失败返回错误信息
        message, status_code = result
        return jsonify({'msg': message}), status_code

@api_bp.route('/character/get_characters/<int:storyline_id>', methods=['GET'])
@jwt_required()  # 验证登录状态
def get_characters_by_storyline(storyline_id):
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 1. 验证故事概要是否存在
    storyline = Storyline.query.get(storyline_id)
    if not storyline:
        return jsonify({'msg': 'Storyline not found'}), 404

    # 2. 验证当前用户是否为故事概要所属用户（权限控制）
    # 通过 storyline -> opera -> user 关联链验证所有权
    opera = Opera.query.get(storyline.opera_id)
    if not opera or opera.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You do not own this storyline'}), 403

    # 3. 查询该故事概要下的所有角色（按角色ID升序排列）
    characters = Character.query.filter_by(storyline_id=storyline_id).order_by(Character.character_id.asc()).all()

    # 4. 构造返回数据
    character_list = []
    for char in characters:
        character_list.append({
            'character_id': char.character_id,
            'storyline_id': char.storyline_id,
            'character_name': char.character_name,
            'appearance': char.appearance,
            'personality': char.personality,
            'related': char.related  # JSON格式的关联关系
        })

    return jsonify({
        'msg': 'Characters retrieved successfully',
        'storyline_id': storyline_id,
        'total_characters': len(character_list),
        'characters': character_list
    }), 200


@api_bp.route('/character/update/<int:character_id>', methods=['PUT'])
@jwt_required()  # 验证登录状态
def update_character(character_id):
    # 从token获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 1. 查询角色是否存在
    character = Character.query.get(character_id)
    if not character:
        return jsonify({'msg': 'Character not found'}), 404

    # 2. 验证权限：当前用户必须是角色的所有者
    if character.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this character'}), 403

    # 3. 获取请求数据
    data = request.get_json()

    # 4. 提取可更新的字段（按需更新，未提供的字段保持不变）
    update_fields = {
        'character_name': data.get('character_name'),
        'appearance': data.get('appearance'),
        'personality': data.get('personality'),
        'related': data.get('related')
    }

    # 5. 字段校验
    # 角色名校验（必填且长度限制）
    if update_fields['character_name'] is not None:
        if not update_fields['character_name']:
            return jsonify({'msg': 'Character name cannot be empty'}), 400
        if len(update_fields['character_name']) > 50:
            return jsonify({'msg': 'Character name must be less than 50 characters'}), 400

    # 外貌描述长度校验
    if update_fields['appearance'] is not None and len(update_fields['appearance']) > 200:
        return jsonify({'msg': 'Appearance must be less than 200 characters'}), 400

    # 性格描述长度校验
    if update_fields['personality'] is not None and len(update_fields['personality']) > 200:
        return jsonify({'msg': 'Personality must be less than 200 characters'}), 400

    # 关联关系JSON格式校验
    if update_fields['related'] is not None and not isinstance(update_fields['related'], (dict, list)):
        return jsonify({'msg': 'Related must be a JSON object or array'}), 400

    # 6. 执行更新
    for field, value in update_fields.items():
        if value is not None:
            setattr(character, field, value)

    # 7. 提交到数据库
    try:
        db.session.commit()

        # 8. 构造返回结果
        return jsonify({
            'msg': 'Character updated successfully',
            'updated_character': {
                'character_id': character.character_id,
                'storyline_id': character.storyline_id,
                'character_name': character.character_name,
                'appearance': character.appearance,
                'personality': character.personality,
                'related': character.related
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to update character', 'error': str(e)}), 500


@api_bp.route('/character/generate_characters', methods=['POST'])
@jwt_required()
def generate_characters():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # 验证请求数据
    if not data or "storyline_id" not in data:
        return jsonify({
            'success': False,
            'message': 'Missing required field: storyline_id'
        }), 400

    storyline_id = data["storyline_id"]

    try:
        # 获取故事概要（假设get_storyline_core返回对象或错误元组）
        storyline = Storyline.get_storyline_core(storyline_id, current_user_id)

        # 检查故事概要获取结果
        if not isinstance(storyline, Storyline):
            message, status_code = storyline
            return jsonify({
                'success': False,
                'message': message
            }), status_code

        Character.delete_characters_by_storyline_core(current_user_id, storyline_id)

        # 构建提示词并调用LLM生成角色
        question = f"\n###LOGLINE###: {storyline.storyline_content}"
        characters = global_llm.ask(
            question,
            global_llm.CHARACTERLIST_PROMPT,
            current_user_id,
            storyline.opera_id,
            chat_id=None,
            save_history=True
        )
        characters = global_llm.analyze_answer(characters)

        # 验证LLM返回结果
        if not isinstance(characters, list) or len(characters) == 0:
            return jsonify({
                'success': False,
                'message': 'Failed to generate characters from LLM'
            }), 500

        created_characters = []
        failed_creations = []

        # 批量创建角色
        for idx, character in enumerate(characters):
            try:
                character_name = character.get("name", f"Generated_Character_{idx + 1}")
                appearance = character.get("appearance", "")
                personality = character.get("personality", "")
                related = character.get("related", {})

                # 调用创建角色的核心函数
                result = Character.create_character_core(
                    user_id=current_user_id,
                    storyline_id=storyline_id,
                    character_name=character_name,
                    appearance=appearance,
                    personality=personality,
                    related=related
                )

                if isinstance(result, Character):
                    created_characters.append({
                        'character_id': result.character_id,
                        'character_name': result.character_name
                    })
                else:
                    err_msg, _ = result
                    failed_creations.append({
                        'character_name': character_name,
                        'error': err_msg
                    })

            except Exception as e:
                failed_creations.append({
                    'character_name': character.get("character_name", f"Character_{idx + 1}"),
                    'error': str(e)
                })

        # 构建最终响应
        return jsonify({
            'success': len(created_characters) > 0,
            'message': f"Successfully generated {len(created_characters)} characters. {len(failed_creations)} failed.",
            'created_characters': created_characters,
            'failed_characters': failed_creations
        }), 200 if len(created_characters) > 0 else 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating characters: {str(e)}"
        }), 500


@api_bp.route('/character/delete/<int:character_id>', methods=['DELETE'])
@jwt_required()
def delete_character_route(character_id):
    """
    删除指定角色的接口
    
    参数:
        character_id: 要删除的角色ID（路径参数）
    
    返回:
        成功: 200状态码和删除成功的消息
        失败: 相应的错误状态码和错误消息
    """
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())
    
    # 调用核心删除函数
    result = Character.delete_character_core(
        user_id=current_user_id,
        character_id=character_id
    )
    
    if isinstance(result, Character):
        # 成功删除，返回被删除的角色信息
        return jsonify({
            'msg': 'Character deleted successfully',
            'deleted_character': {
                'character_id': result.character_id,
                'storyline_id': result.storyline_id,
                'character_name': result.character_name,
                'appearance': result.appearance,
                'personality': result.personality,
                'related': result.related
            }
        }), 200
    else:
        # 删除失败，返回错误信息
        message, status_code = result
        return jsonify({'msg': message}), status_code


@api_bp.route('/character/get/<int:character_id>', methods=['GET'])
@jwt_required()
def get_character(character_id):
    """
    根据角色ID获取单个角色的详细信息
    """
    current_user_id = int(get_jwt_identity())

    # 1. 查询角色是否存在
    character = Character.query.get(character_id)
    if not character:
        return jsonify({'msg': 'Character not found'}), 404

    # 2. 验证权限：当前用户必须是角色的所有者
    if character.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this character'}), 403

    # 3. 构造返回数据
    return jsonify({
        'msg': 'Character retrieved successfully',
        'character': {
            'character_id': character.character_id,
            'storyline_id': character.storyline_id,
            'character_name': character.character_name,
            'appearance': character.appearance,
            'personality': character.personality,
            'related': character.related
        }
    }), 200

