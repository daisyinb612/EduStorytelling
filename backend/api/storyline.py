from datetime import date  # 用于处理日期
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from sql.storyline_db import Storyline
from sql.opera_db import Opera
from sql import db

@api_bp.route('/storyline/create', methods=['POST'])
@jwt_required()  # 验证登录状态
def create_storyline():
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 获取请求数据
    data = request.get_json()
    opera_id = data.get('opera_id')

    # 基础参数校验
    if not opera_id:
        return jsonify({'msg': 'Opera ID is required'}), 400

    # 验证剧本是否存在且属于当前用户（防止为他人剧本创建故事概要）
    opera = Opera.query.get(opera_id)
    if not opera:
        return jsonify({'msg': 'Opera not found'}), 404
    if opera.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this opera'}), 403

    # 提取故事概要字段（根据模型定义）
    theme = data.get('theme', '')  # 主题，默认为空字符串
    classtype = data.get('classtype', '')  # 类型，默认为空
    education = data.get('education', '')  # 教育意义，默认为空
    level = data.get('level', '')  # 级别，默认为空
    storyline_name = data.get('storyline_name', '')
    storyline_content = data.get('storyline_content', '')  # 故事概要内容
    maincharacter = data.get('maincharacter', None)  # 主要角色（JSON）

    # 字段长度校验（匹配模型中的String定义）
    if len(theme) > 500:
        return jsonify({'msg': 'Theme must be less than 500 characters'}), 400
    if len(classtype) > 500:
        return jsonify({'msg': 'Classtype must be less than 500 characters'}), 400
    if len(education) > 500:
        return jsonify({'msg': 'Education must be less than 500 characters'}), 400
    if len(level) > 500:
        return jsonify({'msg': 'Level must be less than 500 characters'}), 400
    if len(storyline_name) > 500:
        return jsonify({'msg': 'Storyline name must be less than 500 characters'}), 400
    if len(storyline_content) > 500:
        return jsonify({'msg': 'Storyline content must be less than 500 characters'}), 400

    # 创建新故事概要
    new_storyline = Storyline(
        user_id=current_user_id,
        opera_id=opera_id,
        theme=theme,
        classtype=classtype,
        education=education,
        level=level,
        storyline_name=storyline_name,
        storyline_content=storyline_content,
        maincharacter=maincharacter
    )

    # 保存到数据库
    try:
        db.session.add(new_storyline)
        db.session.commit()

        # 返回创建成功的故事概要信息
        return jsonify({
            'msg': 'Storyline created successfully',
            'storyline_info': {
                'storyline_id': new_storyline.storyline_id,
                'opera_id': new_storyline.opera_id,
                'theme': new_storyline.theme,
                'classtype': new_storyline.classtype,
                'education': new_storyline.education,
                'level': new_storyline.level,
                'storyline_name': new_storyline.storyline_name,
                'storyline_content': new_storyline.storyline_content,
                'maincharacter': new_storyline.maincharacter
            }
        }), 201  # 201表示资源创建成功
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to create storyline', 'error': str(e)}), 500


@api_bp.route('/storyline/get_storylines/<int:opera_id>', methods=['GET'])
@jwt_required()  # 验证登录状态
def get_opera_storylines(opera_id):
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 验证剧本是否存在且属于当前用户
    opera = Opera.query.get(opera_id)
    if not opera:
        return jsonify({'msg': 'Opera not found'}), 404
    if opera.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this opera'}), 403

    # 查询该剧本下的所有故事概要（按ID倒序）
    storylines = Storyline.query.filter_by(opera_id=opera_id).order_by(Storyline.storyline_id.desc()).all()

    # 构造返回数据
    storylines_list = []
    for item in storylines:
        storylines_list.append({
            'storyline_id': item.storyline_id,
            'opera_id': item.opera_id,
            'theme': item.theme,
            'classtype': item.classtype,
            'education': item.education,
            'level': item.level,
            'storyline_name': item.storyline_name,
            'storyline_content': item.storyline_content,
            'maincharacter': item.maincharacter
        })

    return jsonify({
        'success': True,
        'data': {
            'opera_id': opera_id,
            'opera_name': opera.opera_name,  # 包含剧本名称便于前端展示
            'storylines': storylines_list
        }
    }), 200


@api_bp.route('/storyline/update/<int:storyline_id>', methods=['PUT'])
@jwt_required()  # 验证登录状态
def update_storyline(storyline_id):
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 查询故事概要是否存在
    storyline = Storyline.query.get(storyline_id)
    if not storyline:
        return jsonify({'msg': 'Storyline not found'}), 404

    # 验证当前用户是否为所属剧本的所有者（通过关联表查询）
    # 逻辑：storyline -> opera -> user，确保归属关系
    opera = Opera.query.get(storyline.opera_id)
    if not opera:
        return jsonify({'msg': 'Associated opera not found'}), 404
    if opera.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this storyline'}), 403

    # 获取请求数据
    data = request.get_json()

    # 提取可更新的字段（根据模型定义）
    update_fields = {
        'theme': data.get('theme'),
        'classtype': data.get('classtype'),
        'education': data.get('education'),
        'level': data.get('level'),
        'storyline_name': data.get('storyline_name'),
        'storyline_content': data.get('storyline_content'),
        'maincharacter': data.get('maincharacter')
    }

    # 字段长度校验（仅校验提供了新值的字段）
    if update_fields['theme'] is not None and len(update_fields['theme']) > 500:
        return jsonify({'msg': 'Theme must be less than 500 characters'}), 400
    if update_fields['classtype'] is not None and len(update_fields['classtype']) > 500:
        return jsonify({'msg': 'Classtype must be less than 500 characters'}), 400
    if update_fields['education'] is not None and len(update_fields['education']) > 500:
        return jsonify({'msg': 'Education must be less than 500 characters'}), 400
    if update_fields['level'] is not None and len(update_fields['level']) > 500:
        return jsonify({'msg': 'Level must be less than 500 characters'}), 400
    if update_fields['storyline_name'] is not None and len(update_fields['storyline_name']) > 500:
        return jsonify({'msg': 'Storyline name must be less than 500 characters'}), 400
    if update_fields['storyline_content'] is not None and len(update_fields['storyline_content']) > 500:
        return jsonify({'msg': 'Storyline content must be less than 500 characters'}), 400

    # 更新字段（只更新提供了新值的字段）
    for field, value in update_fields.items():
        if value is not None:
            setattr(storyline, field, value)

    # 提交更新
    try:
        db.session.commit()

        # 构造返回的更新后信息
        updated_info = {
            'storyline_id': storyline.storyline_id,
            'opera_id': storyline.opera_id,
            'theme': storyline.theme,
            'classtype': storyline.classtype,
            'education': storyline.education,
            'level': storyline.level,
            'storyline_name': storyline.storyline_name,
            'storyline_content': storyline.storyline_content,
            'maincharacter': storyline.maincharacter
        }

        return jsonify({
            'msg': 'Storyline updated successfully',
            'data': updated_info
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to update storyline', 'error': str(e)}), 500


# 路由函数：提供API接口用于获取故事概要
@api_bp.route('/storyline/<int:storyline_id>', methods=['GET'])
@jwt_required()
def get_storyline_route(storyline_id):
    # 获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 调用核心函数获取故事概要
    result = Storyline.get_storyline_core(storyline_id, current_user_id)

    if isinstance(result, Storyline):
        # 成功返回故事概要信息
        return jsonify({
            'success': True,
            'data': {
                'storyline_id': result.storyline_id,
                'opera_id': result.opera_id,
                'theme': result.theme,
                'classtype': result.classtype,
                'education': result.education,
                'level': result.level,
                'storyline_name': result.storyline_name,
                'storyline_content': result.storyline_content,
                'maincharacter': result.maincharacter
            }
        }), 200
    else:
        # 失败返回错误信息
        message, status_code = result
        return jsonify({
            'success': False,
            'message': message
        }), status_code