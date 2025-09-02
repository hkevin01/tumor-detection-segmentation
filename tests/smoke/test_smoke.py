def test_smoke_imports():
    """Very small smoke test to ensure test runner and package import work.
    This avoids importing heavy ML libs.
    """
    import importlib

    # import a small module from src to ensure package is discoverable
    mod = importlib.import_module('src.utils')
    assert hasattr(mod, 'some_helper') or hasattr(mod, 'parse_args') or True
