from app.extensions import db

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    supabase_uid = db.Column(db.String(255), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "user_id": self.user_id, "email": self.email, "role": self.role,
            "full_name": self.full_name, "phone": self.phone,
        }
