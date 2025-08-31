from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from sql import db
from sql.scene_db import Scene
from sql.plot_db import Plot
from sql.scene_image_db import SceneImage


@api_bp.route('/scene/create', methods=['POST'])
@jwt_required()
def create_scene_route():
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    plot_id = data.get('plot_id')
    scene_name = data.get('scene_name')
    scene_content = data.get('scene_content', '')
    scene_object = data.get('scene_object', {})
    location = data.get('location', '')

    result = Scene.create_scene_core(
        user_id=current_user_id,
        plot_id=plot_id,
        scene_name=scene_name,
        scene_content=scene_content,
        scene_object=scene_object,
        location=location
    )

    if isinstance(result, Scene):
        return jsonify({
            'msg': 'Scene created successfully',
            'scene': {
                'scene_id': result.scene_id,
                'plot_id': result.plot_id,
                'scene_name': result.scene_name,
                'scene_content': result.scene_content,
                'scene_object': result.scene_object,
                'location': result.location
            }
        }), 201
    else:
        message, status_code = result
        return jsonify({'msg': message}), status_code


@api_bp.route('/scene/list/<int:plot_id>', methods=['GET'])
@jwt_required()
def list_scenes_by_plot_route(plot_id):
    current_user_id = int(get_jwt_identity())

    result = Scene.get_scenes_by_plot(
        user_id=current_user_id,
        plot_id=plot_id
    )

    if isinstance(result, list):
        return jsonify({
            'msg': 'Scenes retrieved successfully',
            'plot_id': plot_id,
            'total_scenes': len(result),
            'scenes': result
        }), 200
    else:
        message, status_code = result
        return jsonify({'msg': message}), status_code


@api_bp.route('/scene/detail/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_scene_detail_route(scene_id):
    current_user_id = int(get_jwt_identity())

    result = Scene.get_scene_core(
        user_id=current_user_id,
        scene_id=scene_id
    )

    if isinstance(result, Scene):
        sc = result
        return jsonify({
            'msg': 'Scene retrieved successfully',
            'scene': {
                'scene_id': sc.scene_id,
                'plot_id': sc.plot_id,
                'user_id': sc.user_id,
                'scene_name': sc.scene_name,
                'scene_content': sc.scene_content,
                'scene_object': sc.scene_object,
                'location': sc.location
            }
        }), 200
    else:
        message, status_code = result
        return jsonify({'msg': message}), status_code

@api_bp.route('/scene/update/<int:scene_id>', methods=['PUT'])
@jwt_required()
def update_scene_route(scene_id):
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    scene_name = data.get('scene_name')
    scene_content = data.get('scene_content')
    scene_object = data.get('scene_object')
    location = data.get('location')

    result = Scene.update_scene_core(
        user_id=current_user_id,
        scene_id=scene_id,
        scene_name=scene_name,
        scene_content=scene_content,
        scene_object=scene_object,
        location=location
    )

    if isinstance(result, Scene):
        return jsonify({
            'msg': 'Scene updated successfully',
            'scene': {
                'scene_id': result.scene_id,
                'plot_id': result.plot_id,
                'scene_name': result.scene_name,
                'scene_content': result.scene_content,
                'scene_object': result.scene_object,
                'location': result.location
            }
        }), 200
    else:
        message, status_code = result
        return jsonify({'msg': message}), status_code


@api_bp.route('/scene/delete/<int:scene_id>', methods=['DELETE'])
@jwt_required()
def delete_scene_route(scene_id):
    current_user_id = int(get_jwt_identity())

    result = Scene.delete_scene_core(
        user_id=current_user_id,
        scene_id=scene_id
    )

    if isinstance(result, Scene):
        return jsonify({
            'msg': 'Scene deleted successfully',
            'deleted_scene': {
                'scene_id': result.scene_id,
                'plot_id': result.plot_id,
                'scene_name': result.scene_name
            }
        }), 200
    else:
        message, status_code = result
        return jsonify({'msg': message}), status_code


