from flask import request, jsonify
from sql import db
from sql.user_db import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import api_bp  # 从 api/__init__.py 导入蓝图

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    identity = data.get('identity')
    # If user_image is not provided, default to None instead of an empty dict.
    user_image = data.get('user_image', None)

    if not username or not email or not password or not identity:
        return jsonify({'msg': 'Missing required fields'}), 400

    # 检查用户名或邮箱是否已存在
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'msg': 'Username or email already exists'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        identity=identity,
        user_image=user_image
    )
    db.session.add(new_user)
    db.session.commit()

    # 注册成功后生成JWT（sub 需为字符串）
    access_token = create_access_token(identity=str(new_user.user_id))
    return jsonify({'msg': 'Registration successful', 'access_token': access_token}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Missing email or password'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'msg': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.user_id))
    return jsonify({'msg': 'Login successful', 'access_token': access_token}), 200

@api_bp.route('/user/get_info', methods=['GET'])
@jwt_required()  # 要求请求中必须包含有效的access_token
def get_user_info():
    # 从token中获取用户ID（即注册/登录时传入create_access_token的identity）
    current_user_id = int(get_jwt_identity())
    try:
        current_user_id = int(current_user_id)
    except Exception:
        pass

    # 根据用户ID查询数据库中的用户信息
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    # 构造返回的用户信息（注意：不要返回密码等敏感字段）
    user_info = {
        'username': user.username,
        'email': user.email,
        'identity': user.identity,  # 注意字段名大小写（与User模型保持一致）
        'user_image': user.user_image
    }
    return jsonify(user_info), 200


@api_bp.route('/user/update_info', methods=['PUT'])
@jwt_required()  # 验证access_token
def update_user_info():
    # 获取当前登录用户ID
    current_user_id = int(get_jwt_identity())
    try:
        current_user_id = int(current_user_id)
    except Exception:
        pass

    # 查询用户是否存在
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    # 获取请求数据
    data = request.get_json()

    # 提取可更新的字段（根据实际需求调整允许更新的字段）
    new_username = data.get('username')
    new_email = data.get('email')
    new_identity = data.get('identity')
    new_user_image = data.get('user_image')

    # 校验并更新字段（避免空值覆盖现有数据）
    if new_username:
        # 检查新用户名是否已被占用
        if User.query.filter_by(username=new_username).first():
            return jsonify({'msg': 'Username already exists'}), 409
        user.username = new_username

    if new_email:
        # 检查新邮箱是否已被占用
        if User.query.filter_by(email=new_email).first():
            return jsonify({'msg': 'Email already exists'}), 409
        user.email = new_email

    if new_identity:
        user.identity = new_identity  # 保持与模型字段名大小写一致

    if new_user_image is not None:  # 允许清空图片（如果业务允许）
        user.user_image = new_user_image

    # 提交数据库变更
    try:
        db.session.commit()
        return jsonify({
            'msg': 'User info updated successfully',
            'updated_info': {
                'username': user.username,
                'email': user.email,
                'identity': user.identity,
                'user_image': user.user_image
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to update user info', 'error': str(e)}), 500


@api_bp.route('/user/delete', methods=['DELETE'])
@jwt_required()  # 验证登录状态
def delete_user():
    # 获取当前登录用户ID
    current_user_id = int(get_jwt_identity())
    try:
        current_user_id = int(current_user_id)
    except Exception:
        pass

    # 查询用户是否存在
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    # 执行删除操作（可根据业务需求添加额外校验，如验证密码）
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'msg': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to delete user', 'error': str(e)}), 500