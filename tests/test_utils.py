from api.parser.utils import sanitize

def test_sanitize():
    assert sanitize("hello world") == "hello world"
    assert sanitize("   hello    world ") == "hello world"
    assert sanitize("  \thello\nworld ") == "hello world"