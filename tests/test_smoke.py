import synw


def test_version():
    assert isinstance(synw.__version__, str)
    assert synw.__version__.count(".") == 2
