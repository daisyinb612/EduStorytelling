from flask import Blueprint



# 1. 创建一个名为 'api' 的蓝图
api_bp = Blueprint('api', __name__)

# 2. 从当前包（api/）中导入各个模块，以注册它们的路由
#    这样，当外部导入 api_bp 时，这些路由就已经被加载了
from . import user
from . import opera
from . import storyline
from . import character
from . import character_image
from . import plot
from . import scene
from . import scene_image
from . import dialogue
from . import chat
