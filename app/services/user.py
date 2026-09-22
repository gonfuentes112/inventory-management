from sqlalchemy.orm import Session

from app.repositories.user import UserRepository

from app.models.user import User

from app.schemas.user import UserCreate


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)

    def create_user(self, data: UserCreate) -> User:
        user = self.repository.create(username=data.username, email=data.email)

        self.session.commit()
        self.session.refresh(user)

        return user

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_users(self) -> list[User]:
        return self.repository.get_all()
