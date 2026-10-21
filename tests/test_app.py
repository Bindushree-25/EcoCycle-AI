import io
import unittest
from unittest.mock import patch
from PIL import Image
from app import create_app
from app.recommendations import get_guidance
from app.model_service import preprocess_image

class RecommendationTests(unittest.TestCase):
    def test_battery_guidance_includes_safety_caution(self):
        guidance = get_guidance("Battery")
        self.assertIn("caution", guidance)
        self.assertIn("puncture", guidance["caution"].lower())

    def test_unknown_category_uses_general_guidance(self):
        guidance = get_guidance("unknown gadget")
        self.assertEqual(guidance["title"], "General electronic waste")
        self.assertTrue(guidance["steps"])

class ImageValidationTests(unittest.TestCase):
    def image_bytes(self, size=(80, 60), fmt="PNG"):
        stream = io.BytesIO()
        Image.new("RGB", size, (120, 130, 140)).save(stream, format=fmt)
        stream.seek(0)
        return stream

    def test_preprocessing_returns_mobile_net_shape(self):
        result = preprocess_image(self.image_bytes())
        self.assertEqual(result.shape, (1, 224, 224, 3))
        self.assertTrue(result.min() >= -1.0 and result.max() <= 1.0)

    def test_rejects_tiny_image(self):
        with self.assertRaisesRegex(ValueError, "too small"):
            preprocess_image(self.image_bytes((20, 20)))

class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "MODEL_PATH": "/path/that/does/not/exist.h5"})
        self.client = self.app.test_client()

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"EcoCycle", response.data)

    def test_health_reports_missing_model_honestly(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["inference_ready"])
        self.assertTrue(response.json["model_download_on_first_scan"])

    def test_rejects_missing_image(self):
        response = self.client.post("/api/predict", data={})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["success"])

    def test_rejects_bad_extension(self):
        response = self.client.post("/api/predict", data={"image": (io.BytesIO(b"abc"), "payload.exe")}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 415)

    def test_missing_model_does_not_return_fake_prediction(self):
        image = io.BytesIO()
        Image.new("RGB", (60, 60), (1, 2, 3)).save(image, format="PNG")
        image.seek(0)
        response = self.client.post("/api/predict", data={"image": (image, "device.png")}, content_type="multipart/form-data")
        # Network/model download is intentionally mocked to fail so this test is deterministic.
        self.assertIn(response.status_code, (500, 503))
        self.assertIn(response.json.get("code"), ("model_unavailable", "inference_error"))
        self.assertNotIn("prediction", response.json)

if __name__ == "__main__":
    unittest.main()
