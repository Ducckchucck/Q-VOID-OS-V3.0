from modules.registry import MODULE_REGISTRY, list_module_metadata


def test_every_module_declares_truth_metadata():
    metadata = list_module_metadata()

    assert metadata
    assert set(MODULE_REGISTRY)
    for item in metadata:
        assert item["status"] in {"real", "simulated", "experimental"}
        assert item["confidence"] in {"high", "medium", "low"}
        assert item["summary"]
        assert item["production_notes"]
