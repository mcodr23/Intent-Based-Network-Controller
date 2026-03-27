from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models import Role, User


DEFAULT_ROLES = [
    ("Admin", "Full platform access"),
    ("Network Engineer", "Can discover, define policy, deploy and remediate"),
    ("Viewer", "Read-only access to dashboards and APIs"),
]


def ensure_roles(db: Session) -> None:
    for role_name, role_desc in DEFAULT_ROLES:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            db.add(Role(name=role_name, description=role_desc))
    db.commit()


def ensure_default_admin(db: Session) -> None:
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        return

    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return

    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        role_id=admin_role.id,
        is_active=True,
    )
    db.add(admin)
    db.commit()


def create_user(db: Session, username: str, email: str, password: str, role_name: str = "Viewer") -> User:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = db.query(Role).filter(Role.name == "Viewer").first()
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
