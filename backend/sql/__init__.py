from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 首先导入基础模型（没有外键依赖的）
from sql.user_db import User

# 然后导入只依赖User的模型
from sql.opera_db import Opera

# 接着导入依赖Opera的模型
from sql.storyline_db import Storyline

# 然后导入依赖Storyline的模型
from sql.character_db import Character
from sql.plot_db import Plot
from sql.scene_db import Scene

# 最后导入依赖多个模型的复杂模型
from sql.character_image_db import CharacterImage
from sql.scene_image_db import SceneImage
from sql.chat_db import Chat
from sql.dialogue_db import Dialogue