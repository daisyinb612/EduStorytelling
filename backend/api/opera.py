from datetime import date  # 用于处理日期
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sql.opera_db import Opera
from sql import db
from . import api_bp
import base64

@api_bp.route('/opera/create', methods=['POST'])
@jwt_required()  # 要求登录状态，确保只有已注册用户能创建剧本
def create_opera():
    # 从token中获取当前登录用户ID（关联到opera的user_id）
    current_user_id = int(get_jwt_identity())
    try:
        current_user_id = int(current_user_id)
    except Exception:
        pass

    # 获取请求数据
    data = request.get_json(silent=True) or {}
    opera_name = data.get('opera_name')
    opera_image_b64 = data.get('opera_image')

    # 基础数据校验
    if not opera_name:
        return jsonify({'msg': 'Opera name is required'}), 400  # 剧本名称为必填项

    # 校验剧本名称长度（模型中定义为String(50)）
    if len(opera_name) > 50:
        return jsonify({'msg': 'Opera name must be less than 50 characters'}), 400

    # 可选：解析 base64 图片
    opera_image_bytes = None
    if isinstance(opera_image_b64, str) and opera_image_b64:
        try:
            # 兼容 dataURL 前缀
            if ',' in opera_image_b64 and opera_image_b64.strip().startswith('data:'):
                opera_image_b64 = opera_image_b64.split(',', 1)[1]
            opera_image_bytes = base64.b64decode(opera_image_b64)
        except Exception:
            # 如果解析失败，置空，不因图片问题阻塞创建
            opera_image_bytes = None

    # 构建新剧本对象
    new_opera = Opera(
        user_id=current_user_id,  # 关联当前登录用户
        opera_name=opera_name,
        create_time=date.today(),  # 默认为当前日期
        opera_image=opera_image_bytes
    )

    # 保存到数据库
    try:
        db.session.add(new_opera)
        db.session.commit()

        # 返回创建成功的剧本信息
        return jsonify({
            'msg': 'Opera created successfully',
            'opera_info': {
                'opera_id': new_opera.opera_id,
                'opera_name': new_opera.opera_name,
                'create_time': new_opera.create_time.isoformat(),  # 转为ISO格式日期字符串
            }
        }), 201  # 201表示资源创建成功
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to create opera', 'error': str(e)}), 500


@api_bp.route('/opera/get_operas', methods=['GET'])
@jwt_required()  # 验证登录状态，确保只能查询自己的剧本
def get_operas():
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())
    try:
        current_user_id = int(current_user_id)
    except Exception:
        pass

    # 查询该用户创建的所有剧本（按创建时间倒序，最新的在前）
    user_operas = Opera.query.filter_by(user_id=current_user_id).order_by(Opera.create_time.desc()).all()

    if not user_operas:
        return jsonify({'msg': 'No operas found for this user'}), 200  # 无剧本时返回空列表而非错误

    # 构造返回的剧本列表
    operas_list = []
    for opera in user_operas:
        operas_list.append({
            'opera_id': opera.opera_id,
            'opera_name': opera.opera_name,
            'create_time': opera.create_time.isoformat(),  # 日期转为字符串便于JSON传输
        })

    return jsonify({
        'total': len(operas_list),  # 剧本总数
        'operas': operas_list
    }), 200


@api_bp.route('/opera/update_name/<int:opera_id>', methods=['PUT'])
@jwt_required()  # 验证登录状态
def update_opera_name(opera_id):
    # 从token中获取当前登录用户ID
    current_user_id = int(get_jwt_identity())

    # 查询剧本是否存在
    opera = Opera.query.get(opera_id)
    if not opera:
        return jsonify({'msg': 'Opera not found'}), 404

    # 验证当前用户是否为剧本的所有者（防止越权修改）
    if opera.user_id != current_user_id:
        return jsonify({'msg': 'Permission denied: You are not the owner of this opera'}), 403

    # 获取请求数据
    data = request.get_json()
    new_opera_name = data.get('opera_name')

    # 校验新剧本名称
    if not new_opera_name:
        return jsonify({'msg': 'New opera name is required'}), 400

    if len(new_opera_name) > 50:
        return jsonify({'msg': 'Opera name must be less than 50 characters'}), 400

    # 检查同一用户下是否有同名剧本
    if Opera.query.filter_by(
            user_id=current_user_id,
            opera_name=new_opera_name
    ).first() and new_opera_name != opera.opera_name:
        return jsonify({'msg': 'You already have an opera with this name'}), 409

    # 更新剧本名称
    try:
        opera.opera_name = new_opera_name
        db.session.commit()

        return jsonify({
            'msg': 'Opera name updated successfully',
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Failed to update opera name', 'error': str(e)}), 500

