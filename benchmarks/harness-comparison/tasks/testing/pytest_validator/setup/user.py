from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class User:
    id: int
    name: str
    email: str
    age: int
    is_active: bool = True


def validate_user(user: User) -> bool:
    if not isinstance(user, User):
        raise TypeError("Expected User instance")

    if not user.name or not isinstance(user.name, str):
        return False

    if len(user.name) < 2 or len(user.name) > 100:
        return False

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", user.email):
        return False

    if not isinstance(user.age, int) or user.age < 0 or user.age > 150:
        return False

    if not isinstance(user.is_active, bool):
        return False

    return True


def create_user(name: str, email: str, age: int) -> User:
    user_id = abs(hash(name + email)) % 1000000
    user = User(id=user_id, name=name, email=email, age=age)
    if not validate_user(user):
        raise ValueError(f"Invalid user data: name={name}, email={email}, age={age}")
    return user


def get_user_summary(user: User) -> str:
    if not validate_user(user):
        raise ValueError("Cannot summarize invalid user")

    status = "Active" if user.is_active else "Inactive"
    age_group = "Minor" if user.age < 18 else "Adult" if user.age < 65 else "Senior"
    return f"User {user.name} (ID: {user.id}): {user.email}, Age: {user.age} ({age_group}), Status: {status}"


def filter_active_users(users: list[User]) -> list[User]:
    if not isinstance(users, list):
        raise TypeError("Expected list of users")
    return [u for u in users if u.is_active and validate_user(u)]
