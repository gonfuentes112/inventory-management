from sqlalchemy.orm import Session

from app.repositories.user import UserRepository

from app.models.user import User

from app.schemas.user import UserCreate

from app.core.security import hash_password, create_access_token, verify_password


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)

    def create_user(self, data: UserCreate) -> User:
        if self.repository.get_by_username(data.username) is not None:
            raise ValueError("Username already exists")

        if self.repository.get_by_email(data.email) is not None:
            raise ValueError("Email already exists")

        hashed_password = hash_password(data.password)

        user = self.repository.create(
            username=data.username, email=data.email, hashed_password=hashed_password
        )

        self.session.commit()
        self.session.refresh(user)

        return user

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_users(self) -> list[User]:
        return self.repository.get_all()

    def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> str | None:
        user = self.repository.get_by_username(username)

        if user is None:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return create_access_token(user.id)
