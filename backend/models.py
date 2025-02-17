from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, user_id, email, name, profile_pic=None):
        self.id = user_id
        self.email = email
        self.name = name
        self.profile_pic = profile_pic

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic
        }

    @staticmethod
    def from_dict(data):
        return User(
            user_id=data.get('id'),
            email=data.get('email'),
            name=data.get('name'),
            profile_pic=data.get('profile_pic')
        )

class WorkoutHistory:
    def __init__(self, user_id, workout_plan, created_at=None):
        self.user_id = user_id
        self.workout_plan = workout_plan
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'workout_plan': self.workout_plan,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return WorkoutHistory(
            user_id=data.get('user_id'),
            workout_plan=data.get('workout_plan'),
            created_at=datetime.fromisoformat(data.get('created_at'))
        ) 