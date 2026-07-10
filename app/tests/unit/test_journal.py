from app.routers.journal import create_journal
from app.models.journal import Journal, JournalIn

async def test_mock_create_journal(mock_session, mock_user):
    input = JournalIn(title="Post Mock-Test Title", body="Post Mock-Test Body")
    result = await create_journal(session=mock_session, user=mock_user, new_journal=input)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert isinstance(result, Journal)
    assert result.title == "Post Mock-Test Title"
    assert result.body == "Post Mock-Test Body"
    assert result.user_id == mock_user.id
    assert result.is_public is False
