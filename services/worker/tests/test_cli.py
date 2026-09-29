from worker.main import parse_args


def test_parse_args_ingest() -> None:
    args = parse_args(["--queue", "ingest"])
    assert args.queue == "ingest"


def test_parse_args_analysis() -> None:
    args = parse_args(["--queue", "analysis"])
    assert args.queue == "analysis"
