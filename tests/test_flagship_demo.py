from examples.flagship_demo import run_demo


def test_flagship_demo_emits_report(tmp_path):
    report_path = tmp_path / "demo_report.json"

    report = run_demo(report_path)

    assert report_path.exists()
    assert report["forensic_chain_intact"] is True
    assert report["precog_prediction"]
    assert report["rag_response"]["recommended_response"]
    assert any(event["type"] == "THREAT_DETECTED" for event in report["events_observed"])
    assert any(event["type"] == "POLYMORPH_MUTATION" for event in report["events_observed"])
