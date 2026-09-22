from app.core.security import hash_password, verify_password


def test_hash_password():
    password = "mypassword123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2")


def test_verify_password():
    password = "mypassword123"

    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False
