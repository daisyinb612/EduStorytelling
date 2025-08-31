import os
import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from sql import *
import json
from api import api_bp  # 导入我们创建的蓝图
from datetime import timedelta

# 加载环境变量
load_dotenv(override=True)

app = Flask(__name__)

# 配置日志
if not app.debug:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# 配置CORS - 生产环境应限制允许的域名
from flask_cors import CORS
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',')
if allowed_origins and allowed_origins[0]:
    CORS(app, origins=allowed_origins)
else:
    # 仅在没有配置时使用宽松模式，生产环境强烈建议配置ALLOWED_ORIGINS
    app.logger.warning("ALLOWED_ORIGINS not configured, allowing all origins")
    CORS(app)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}
# 延长访问令牌有效期（默认 7 天）
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# 打印当前数据库 URI，便于确认是否指向正确的数据库
app.logger.info('DB URI: %s', app.config['SQLALCHEMY_DATABASE_URI'])

# 注册蓝图，并统一添加 /api 前缀
app.register_blueprint(api_bp, url_prefix='/api')

# 初始化扩展
db.init_app(app)
jwt = JWTManager(app)

# 可选：数据库初始化函数，生产环境建议单独执行
def init_db():
    with app.app_context():
        DB_RESET = os.environ.get('DB_RESET', '0') == '1'
        if DB_RESET:
            app.logger.warning('DB_RESET=1 detected: dropping all tables...')
            db.drop_all()
        db.create_all()
        app.logger.info('Database schema ensured.')

if __name__ == '__main__':
    # 生产环境不应在这里初始化数据库，而是单独执行
    # init_db()
    
    # 生产环境建议通过环境变量控制参数
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # 允许外部访问
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)