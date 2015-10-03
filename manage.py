from flask.ext.script import Manager
from app import app
from app.scripts.ai_worker import AiWorker

manager = Manager(app)
manager.add_command('ai_worker', AiWorker)

if __name__ == "__main__":
    manager.run()
