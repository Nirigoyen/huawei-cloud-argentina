import pytest

from user import User, validate_user, create_user, get_user_summary, filter_active_users


@pytest.fixture
def valid_user():
    return User(id=1, name="Alice", email="alice@test.com", age=30, is_active=True)


@pytest.fixture
def inactive_user():
    return User(id=2, name="Bob", email="bob@test.com", age=25, is_active=False)


@pytest.fixture
def users_list(valid_user, inactive_user):
    return [valid_user, inactive_user]


@pytest.mark.parametrize("name,email,age,expected", [
    ("Alice", "alice@test.com", 30, True),
    ("Bob", "bob@test.com", 25, True),
    ("Charlie", "charlie@test.com", 0, True),
    ("Diana", "diana@test.com", 150, True),
    ("A", "a@test.com", 30, False),  # name too short
    ("Alice", "invalid-email", 30, False),  # bad email
    ("Alice", "alice@test.com", -1, False),  # negative age
    ("Alice", "alice@test.com", 151, False),  # age too high
    ("", "alice@test.com", 30, False),  # empty name
    ("Alice", "", 30, False),  # empty email
    ("Alice", "alice@test.com", 30, True),
])
def test_validate_user_parametrized(name, email, age, expected):
    user = User(id=1, name=name, email=email, age=age)
    assert validate_user(user) == expected


def test_validate_user_valid(valid_user):
    assert validate_user(valid_user) is True


def test_validate_user_inactive_is_valid(inactive_user):
    assert validate_user(inactive_user) is True


def test_validate_user_not_user_instance():
    with pytest.raises(TypeError):
        validate_user("not a user")


def test_validate_user_long_name():
    user = User(id=1, name="A" * 101, email="test@test.com", age=30)
    assert validate_user(user) is False


def test_validate_user_name_at_limit():
    user = User(id=1, name="A" * 100, email="test@test.com", age=30)
    assert validate_user(user) is True


def test_create_user_valid():
    user = create_user("Alice", "alice@test.com", 30)
    assert user.name == "Alice"
    assert user.email == "alice@test.com"
    assert user.age == 30
    assert user.is_active is True


def test_create_user_invalid_raises():
    with pytest.raises(ValueError):
        create_user("A", "bad-email", 30)


def test_create_user_generates_id():
    user = create_user("Alice", "alice@test.com", 30)
    assert isinstance(user.id, int)
    assert user.id >= 0


def test_get_user_summary_active(valid_user):
    summary = get_user_summary(valid_user)
    assert "Alice" in summary
    assert "Active" in summary
    assert "Adult" in summary


def test_get_user_summary_inactive(inactive_user):
    summary = get_user_summary(inactive_user)
    assert "Bob" in summary
    assert "Inactive" in summary


def test_get_user_summary_minor():
    user = User(id=1, name="Kid", email="kid@test.com", age=10)
    summary = get_user_summary(user)
    assert "Minor" in summary


def test_get_user_summary_senior():
    user = User(id=1, name="Grandpa", email="gp@test.com", age=70)
    summary = get_user_summary(user)
    assert "Senior" in summary


def test_get_user_summary_invalid_user():
    user = User(id=1, name="", email="bad", age=30)
    with pytest.raises(ValueError):
        get_user_summary(user)


def test_filter_active_users(users_list):
    active = filter_active_users(users_list)
    assert len(active) == 1
    assert active[0].name == "Alice"


def test_filter_active_users_empty():
    assert filter_active_users([]) == []


def test_filter_active_users_all_inactive():
    users = [User(id=1, name="Bob", email="bob@test.com", age=30, is_active=False)]
    assert filter_active_users(users) == []


def test_filter_active_users_not_list():
    with pytest.raises(TypeError):
        filter_active_users("not a list")


def test_filter_active_users_skips_invalid():
    users = [
        User(id=1, name="Alice", email="alice@test.com", age=30, is_active=True),
        User(id=2, name="", email="bad", age=30, is_active=True),  # invalid
    ]
    result = filter_active_users(users)
    assert len(result) == 1
