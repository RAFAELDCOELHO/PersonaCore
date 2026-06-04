"""Install-parity smoke test (ENV-01): the package imports only after install."""


def test_import_personacore():
    import personacore

    assert personacore is not None


def test_version_is_nonempty_string():
    import personacore

    assert isinstance(personacore.__version__, str)
    assert personacore.__version__ != ""
