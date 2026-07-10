from unittest.mock import Mock, AsyncMock

from app.models.user import User
from app.utils.utils import hash_password
import pytest

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = Mock()
    return session

@pytest.fixture
def mock_user():
    return User(username="test_user", password_hash=hash_password("123"), id="1")
