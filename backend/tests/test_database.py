from app.database import engine, async_session_factory, get_session


def test_engine_is_async():
    assert "asyncpg" in str(engine.url)


def test_session_factory_callable():
    s = async_session_factory()
    assert s is not None


def test_get_session_is_async_generator():
    import inspect
    assert inspect.isasyncgenfunction(get_session)
