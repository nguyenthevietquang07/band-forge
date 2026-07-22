def test_domain_package_is_importable() -> None:
    import bandforge_domain

    assert bandforge_domain.__name__ == "bandforge_domain"
