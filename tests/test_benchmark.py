from evaluation.run_benchmark import classify, metrics_from_counts


def test_classify_counts_category_presence():
    metrics = classify(
        expected={"A", "B"},
        predicted={"B", "C"},
        universe={"A", "B", "C", "D"},
    )

    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert metrics["tn"] == 1


def test_metrics_calculate_precision_recall_and_f1():
    metrics = metrics_from_counts(tp=8, fp=2, fn=4, tn=6)

    assert metrics["precision"] == 0.8
    assert metrics["recall"] == 8 / 12
    assert round(metrics["f1"], 4) == 0.7273
    assert metrics["specificity"] == 0.75


def test_metrics_handle_empty_denominators():
    metrics = metrics_from_counts(tp=0, fp=0, fn=0, tn=5)

    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["specificity"] == 1.0
