from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[User]:
        statement = select(User)
        return list(self.session.scalars(statement).all())

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)

    def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password)

        self.session.add(user)
        self.session.flush()

        return user
