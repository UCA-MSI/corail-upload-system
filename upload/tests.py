import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase
from PIL import Image

from .models import DiveSite, UploadImageModel, UserDiveSite


def _make_test_image() -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("dive.jpg", buffer.read(), content_type="image/jpeg")


class DiveSiteModelTests(TestCase):
    def test_country_defaults_to_indonesia(self) -> None:
        site = DiveSite.objects.create(name="Blue Hole")
        self.assertEqual(site.country, "Indonesia")

    def test_region_is_optional(self) -> None:
        site = DiveSite.objects.create(name="Blue Hole")
        self.assertEqual(site.region, "")


class ProfileDiveSiteCreationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)

    def test_add_dive_site_creates_site_with_country_and_region(self) -> None:
        self.client.post("/profile/", {
            "action": "add_dive_site",
            "new_site_name": "Manta Point",
            "new_site_country": "Indonesia",
            "new_site_region": "Bali / Nusa Penida",
            "depth": "18.5",
        })
        site = DiveSite.objects.get(name="Manta Point")
        self.assertEqual(site.country, "Indonesia")
        self.assertEqual(site.region, "Bali / Nusa Penida")
        self.assertTrue(
            UserDiveSite.objects.filter(user=self.user, dive_site=site).exists()
        )

    def test_add_dive_site_defaults_country_when_blank(self) -> None:
        self.client.post("/profile/", {
            "action": "add_dive_site",
            "new_site_name": "Coral Garden",
            "new_site_region": "Raja Ampat / Misool - Marine Protected Area",
        })
        site = DiveSite.objects.get(name="Coral Garden")
        self.assertEqual(site.country, "Indonesia")


class UploadPageDiveSiteSelectionTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)
        self.site = DiveSite.objects.create(
            name="Manta Point", region="Bali / Nusa Penida"
        )

    def test_upload_page_lists_existing_sites_only(self) -> None:
        response = self.client.get("/upload/")
        self.assertContains(response, "Manta Point")
        self.assertNotContains(response, "new_site_name")

    def test_upload_does_not_create_new_dive_site(self) -> None:
        site_count_before = DiveSite.objects.count()
        self.client.post("/upload/", {
            "new_site_name": "Should Not Be Created",
            "new_site_region": "Nowhere",
        })
        self.assertEqual(DiveSite.objects.count(), site_count_before)
        self.assertFalse(
            DiveSite.objects.filter(name="Should Not Be Created").exists()
        )


class UploadDivingDateValidationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)

    def test_upload_without_diving_date_is_rejected(self) -> None:
        response = self.client.post("/upload/", {"images": [_make_test_image()]})
        self.assertContains(response, "Please enter the diving date")
        self.assertEqual(UploadImageModel.objects.count(), 0)

    def test_upload_with_diving_date_succeeds(self) -> None:
        self.client.post("/upload/", {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
        })
        image = UploadImageModel.objects.get()
        self.assertEqual(str(image.diving_date), "2026-07-30")

    def test_upload_stores_dive_time(self) -> None:
        self.client.post("/upload/", {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
            "dive_time": "morning",
        })
        image = UploadImageModel.objects.get()
        self.assertEqual(image.dive_time, "morning")

    def test_dive_time_is_optional(self) -> None:
        self.client.post("/upload/", {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
        })
        image = UploadImageModel.objects.get()
        self.assertEqual(image.dive_time, "")


class BatchedUploadTests(TestCase):
    BATCH_HEADERS = {"HTTP_X_UPLOAD_BATCH": "1"}
    SESSION_ID = "6f1c2b9e-3d4a-4e5f-8a7b-1c2d3e4f5a6b"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)

    def _post_batch(self, **fields: str) -> HttpResponse:
        data = {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
            "session_id": self.SESSION_ID,
            **fields,
        }
        return self.client.post("/upload/", data, **self.BATCH_HEADERS)

    def test_batches_share_one_session(self) -> None:
        self._post_batch()
        response = self._post_batch(final="1")
        self.assertEqual(response.json(), {"uploaded": 1})
        session_ids = set(UploadImageModel.objects.values_list("session_id", flat=True))
        self.assertEqual({str(s) for s in session_ids}, {self.SESSION_ID})

    def test_final_batch_flashes_total_count(self) -> None:
        self._post_batch()
        self._post_batch(final="1")
        response = self.client.get("/upload/")
        self.assertContains(response, "2 images uploaded successfully!")

    def test_non_final_batch_does_not_flash(self) -> None:
        self._post_batch()
        response = self.client.get("/upload/")
        self.assertNotContains(response, "uploaded successfully")

    def test_invalid_session_id_is_rejected(self) -> None:
        response = self._post_batch(session_id="not-a-uuid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid upload session"})
        self.assertEqual(UploadImageModel.objects.count(), 0)

    def test_missing_diving_date_returns_json_error(self) -> None:
        response = self._post_batch(diving_date="")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Please enter the diving date"})

    def test_batch_without_images_returns_json_error(self) -> None:
        response = self.client.post("/upload/", {
            "diving_date": "2026-07-30", "session_id": self.SESSION_ID,
        }, **self.BATCH_HEADERS)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Please select at least one image"}
        )

    def test_plain_post_without_session_id_still_redirects(self) -> None:
        response = self.client.post("/upload/", {
            "images": [_make_test_image()], "diving_date": "2026-07-30",
        })
        self.assertRedirects(response, "/upload/", fetch_redirect_response=False)
        self.assertEqual(UploadImageModel.objects.count(), 1)
