import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
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
