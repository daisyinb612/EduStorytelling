from flask import request, jsonify
from . import api_bp
from agent.llm import global_llm
from agent.prompt import PROMPT
from sql import db
from sql.chat_db import Chat
from flask_jwt_extended import jwt_required, get_jwt_identity


@api_bp.route('/chat/create', methods=['POST'])
@jwt_required()
def create_chat_route():
    # 获取请求数据和当前用户ID
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    # 调用核心函数创建聊天记录
    result = Chat.create_chat(current_user_id, data["opera_id"], data["chat_AI"])

    if isinstance(result, Chat):
        # 成功返回新创建的聊天记录信息
        return jsonify({
            'success': True,
            'message': '聊天记录创建成功',
            'data': {
                'chat_id': result.chat_id,
                'chat_time': result.chat_time.isoformat()
            }
        }), 201
    else:
        # 失败返回错误信息
        message, status_code = result
        return jsonify({
            'success': False,
            'message': message
        }), status_code


@api_bp.route('/chat/<int:chat_id>', methods=['GET'])
@jwt_required()
def get_chat(chat_id):  # 重命名路由函数避免冲突
    current_user_id = int(get_jwt_identity())
    result = Chat.get_chat_by_id(chat_id, current_user_id)

    if isinstance(result, Chat):
        # 成功返回聊天记录
        return jsonify({
            'success': True,
            'data': {
                'chat_id': result.chat_id,
                'opera_id': result.opera_id,
                'chat_AI': result.chat_AI,
                'chat_time': result.chat_time.isoformat()
            }
        }), 200
    else:
        # 失败返回错误信息
        message, status_code = result
        return jsonify({
            'success': False,
            'message': message
        }), status_code


# 路由函数：提供API接口用于更新聊天记录
@api_bp.route('/chat/<int:chat_id>', methods=['PUT'])
@jwt_required()
def update_chat_route(chat_id):
    current_user_id = int(get_jwt_identity())
    update_data = request.get_json()

    # 验证更新数据是否存在
    if not update_data:
        return jsonify({
            'success': False,
            'message': '没有提供更新数据'
        }), 400

    result = Chat.update_chat_by_id(chat_id, current_user_id, update_data)

    if isinstance(result, Chat):
        # 成功返回更新后的聊天记录
        return jsonify({
            'success': True,
            'message': '聊天记录更新成功',
            'data': {
                'chat_id': result.chat_id,
                'opera_id': result.opera_id,
                'chat_AI': result.chat_AI,
                'chat_time': result.chat_time.isoformat()
            }
        }), 200
    else:
        # 失败返回错误信息
        message, status_code = result
        return jsonify({
            'success': False,
            'message': message
        }), status_code


@api_bp.route('/chat/get_response', methods=['POST'])
@jwt_required()
def get_response():
    data = request.get_json()
    # 获取当前用户ID
    current_user_id = int(get_jwt_identity())

    # 获取用户输入和历史记录
    user_input = data.get('user_input')
    history = data.get('history', [])
    opera_id = data.get('opera_id')

    if not user_input:
        return jsonify({
            'success': False,
            'message': '缺少用户输入'
        }), 400

    # 获取聊天记录，如果没有chat_id则创建新的chat
    chat_id = data.get('chat_id')
    if not chat_id:
        # 如果没有chat_id，需要opera_id来创建新的chat
        if not opera_id:
            return jsonify({
                'success': False,
                'message': '缺少剧本ID或聊天记录ID'
            }), 400
        
        # 创建新的聊天记录，使用默认的chat_AI为空列表
        chat_result = Chat.create_chat(current_user_id, opera_id, [])
        if not isinstance(chat_result, Chat):
            message, status_code = chat_result
            return jsonify({
                'success': False,
                'message': message
            }), status_code
        
        chat_record = chat_result
        chat_id = chat_record.chat_id
    else:
        chat_record = Chat.get_chat_by_id(chat_id, current_user_id)
        if not isinstance(chat_record, Chat):
            message, status_code = chat_record
            return jsonify({
                'success': False,
                'message': message
            }), status_code

    prompt = PROMPT['chat'] # Assuming 'chat' is a key in PROMPT dict
    response = global_llm.ask(
        question=user_input,
        prompt=prompt,
        user_id=current_user_id,
        opera_id=chat_record.opera_id,
        chat_id=chat_id,
        save_history=True
    )

    return jsonify({
        'response': response,
        'chat_id': chat_id
    }), 200


@api_bp.route('/chat/get_storyline_help', methods=['POST'])
@jwt_required()
def get_storyline_help():
    """
    获取故事概要帮助的接口
    
    请求参数:
        opera_id: 剧本ID（必填）
        storyline: 故事概要内容（可选）
        user_input: 用户问题（必填）
        chat_id: 聊天记录ID（可选，用于继续对话）
    
    返回:
        成功: 200状态码和AI回答
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    # 验证请求数据
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # 从请求数据中提取各字段
    opera_id = data.get("opera_id")
    storyline = data.get("storyline", "")
    user_input = data.get("user_input")
    chat_id = data.get("chat_id")  # 可选的聊天记录ID
    
    # 验证必填参数
    if not opera_id:
        return jsonify({"error": "Missing required field: opera_id"}), 400
    if not user_input:
        return jsonify({"error": "Missing required field: user_input"}), 400
    
    try:
        # 验证剧本是否存在并检查权限
        from sql import Opera
        opera = Opera.query.get(opera_id)
        if not opera:
            return jsonify({"error": "Opera not found"}), 404
        
        if opera.user_id != current_user_id:
            return jsonify({"error": "Permission denied: You do not own this opera"}), 403
        
        # 如果没有提供storyline，尝试从数据库获取
        if not storyline:
            from sql import Storyline
            storyline_obj = Storyline.query.filter_by(opera_id=opera_id).first()
            if storyline_obj:
                storyline = storyline_obj.storyline or ""
        
        # 构建问题内容
        if storyline:
            question = f"###LOGLINE###: {storyline}\n###MYQUESTION###: {user_input}"
        else:
            question = f"###MYQUESTION###: {user_input}"
        
        # 使用故事概要帮助提示词
        storyline_help_prompt = global_llm.storyline_help
        
        # 如果没有提供chat_id，创建新的聊天记录
        if not chat_id:
            chat_result = Chat.create_chat(current_user_id, opera_id, [])
            if not isinstance(chat_result, Chat):
                message, status_code = chat_result
                return jsonify({
                    "success": False,
                    "error": message
                }), status_code
            chat_id = chat_result.chat_id
        
        # 调用LLM获取回答
        answer = global_llm.ask(
            question=question,
            prompt=storyline_help_prompt,
            user_id=current_user_id,
            opera_id=opera_id,
            chat_id=chat_id,
            save_history=True
        )
        
        return jsonify({
            "success": True,
            "answer": answer,
            "storyline": storyline,
            "user_input": user_input,
            "chat_id": chat_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bp.route('/chat/get_role_help', methods=['POST'])
@jwt_required()
def get_role_help():
    """
    获取角色创作帮助的接口
    
    请求参数:
        opera_id: 剧本ID（必填）
        storyline: 故事概要内容（可选）
        character_list: 角色列表（可选）
        user_input: 用户问题（必填）
        chat_id: 聊天记录ID（可选）
    
    返回:
        成功: 200状态码和AI回答
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    # 验证请求数据
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # 从请求数据中提取各字段
    opera_id = data.get("opera_id")
    storyline = data.get("storyline", "")
    character_list = data.get("character_list", [])
    user_input = data.get("user_input")
    chat_id = data.get("chat_id")
    
    # 验证必填参数
    if not opera_id:
        return jsonify({"error": "Missing required field: opera_id"}), 400
    if not user_input:
        return jsonify({"error": "Missing required field: user_input"}), 400
    
    try:
        # 验证剧本是否存在并检查权限
        from sql import Opera
        opera = Opera.query.get(opera_id)
        if not opera:
            return jsonify({"error": "Opera not found"}), 404
        
        if opera.user_id != current_user_id:
            return jsonify({"error": "Permission denied: You do not own this opera"}), 403
        
        # 如果没有提供storyline或character_list，尝试从数据库获取
        if not storyline or not character_list:
            from sql import Storyline, Character
            storyline_obj = Storyline.query.filter_by(opera_id=opera_id).first()
            if storyline_obj:
                if not storyline:
                    storyline = storyline_obj.storyline or ""
                
                if not character_list:
                    characters = Character.query.filter_by(storyline_id=storyline_obj.storyline_id).all()
                    character_list = [
                        {
                            "name": char.character_name,
                            "personality": char.personality or "",
                            "appearance": char.appearance or ""
                        }
                        for char in characters
                    ]
        
        # 构建问题内容
        question_parts = []
        if storyline:
            question_parts.append(f"###LOGLINE###: {storyline}")
        if character_list:
            import json
            question_parts.append(f"###CHARACTERLIST###: {json.dumps(character_list, ensure_ascii=False, indent=2)}")
        question_parts.append(f"###MYQUESTION###: {user_input}")
        
        question = "\n".join(question_parts)
        
        # 使用角色帮助提示词
        role_help_prompt = global_llm.role_help
        
        # 如果没有提供chat_id，创建新的聊天记录
        if not chat_id:
            chat_result = Chat.create_chat(current_user_id, opera_id, [])
            if not isinstance(chat_result, Chat):
                message, status_code = chat_result
                return jsonify({
                    "success": False,
                    "error": message
                }), status_code
            chat_id = chat_result.chat_id
        
        # 调用LLM获取回答
        answer = global_llm.ask(
            question=question,
            prompt=role_help_prompt,
            user_id=current_user_id,
            opera_id=opera_id,
            chat_id=chat_id,
            save_history=True
        )
        
        return jsonify({
            "success": True,
            "answer": answer,
            "storyline": storyline,
            "character_list": character_list,
            "user_input": user_input,
            "chat_id": chat_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bp.route('/chat/get_plot_help', methods=['POST'])
@jwt_required()
def get_plot_help():
    """
    获取情节创作帮助的接口
    
    请求参数:
        opera_id: 剧本ID（必填）
        storyline: 故事概要内容（可选）
        character_list: 角色列表（可选）
        user_input: 用户问题（必填）
        chat_id: 聊天记录ID（可选）
    
    返回:
        成功: 200状态码和AI回答
        失败: 相应的错误状态码和错误消息
    """
    # 获取请求数据和当前用户ID
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    # 验证请求数据
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # 从请求数据中提取各字段
    opera_id = data.get("opera_id")
    storyline = data.get("storyline", "")
    character_list = data.get("character_list", [])
    user_input = data.get("user_input")
    chat_id = data.get("chat_id")
    
    # 验证必填参数
    if not opera_id:
        return jsonify({"error": "Missing required field: opera_id"}), 400
    if not user_input:
        return jsonify({"error": "Missing required field: user_input"}), 400
    
    try:
        # 验证剧本是否存在并检查权限
        from sql import Opera
        opera = Opera.query.get(opera_id)
        if not opera:
            return jsonify({"error": "Opera not found"}), 404
        
        if opera.user_id != current_user_id:
            return jsonify({"error": "Permission denied: You do not own this opera"}), 403
        
        # 如果没有提供storyline或character_list，尝试从数据库获取
        if not storyline or not character_list:
            from sql import Storyline, Character
            storyline_obj = Storyline.query.filter_by(opera_id=opera_id).first()
            if storyline_obj:
                if not storyline:
                    storyline = storyline_obj.storyline or ""
                
                if not character_list:
                    characters = Character.query.filter_by(storyline_id=storyline_obj.storyline_id).all()
                    character_list = [
                        {
                            "name": char.character_name,
                            "personality": char.personality or "",
                            "appearance": char.appearance or ""
                        }
                        for char in characters
                    ]
        
        # 构建问题内容
        question_parts = []
        if storyline:
            question_parts.append(f"###LOGLINE###: {storyline}")
        if character_list:
            import json
            question_parts.append(f"###CHARACTERLIST###: {json.dumps(character_list, ensure_ascii=False, indent=2)}")
        question_parts.append(f"###MYQUESTION###: {user_input}")
        
        question = "\n".join(question_parts)
        
        # 使用情节帮助提示词
        plot_help_prompt = global_llm.plot_help
        
        # 如果没有提供chat_id，创建新的聊天记录
        if not chat_id:
            chat_result = Chat.create_chat(current_user_id, opera_id, [])
            if not isinstance(chat_result, Chat):
                message, status_code = chat_result
                return jsonify({
                    "success": False,
                    "error": message
                }), status_code
            chat_id = chat_result.chat_id
        
        # 调用LLM获取回答
        answer = global_llm.ask(
            question=question,
            prompt=plot_help_prompt,
            user_id=current_user_id,
            opera_id=opera_id,
            chat_id=chat_id,
            save_history=True
        )
        
        return jsonify({
            "success": True,
            "answer": answer,
            "storyline": storyline,
            "character_list": character_list,
            "user_input": user_input,
            "chat_id": chat_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500