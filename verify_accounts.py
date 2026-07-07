from app import app
from models.user import User

ctx = app.app_context()
ctx.push()
print('Total users:', User.query.count())
for user in User.query.all():
    print(f'- {user.username} ({user.role})')
ctx.pop()
