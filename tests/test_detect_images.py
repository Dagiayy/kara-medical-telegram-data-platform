import kara_detection.detect_images as detect


class FakeBox:
    def __init__(self, cls_id, conf):
        self.cls = [cls_id]
        self.conf = [conf]


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    names = {0: "person", 1: "bottle"}

    def __call__(self, *_args, **_kwargs):
        return [FakeResult([FakeBox(0, 0.9), FakeBox(1, 0.1)])]


def test_detect_objects_filters_by_confidence(monkeypatch):
    monkeypatch.setattr(detect, "get_model", lambda: FakeModel())

    detections = detect.detect_objects("fake.jpg", confidence_threshold=0.35)

    assert detections == [{"class_name": "person", "confidence_score": 0.9}]


def test_detect_objects_no_threshold_keeps_all(monkeypatch):
    monkeypatch.setattr(detect, "get_model", lambda: FakeModel())

    detections = detect.detect_objects("fake.jpg", confidence_threshold=0.0)

    assert len(detections) == 2
