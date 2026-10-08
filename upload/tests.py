import io

from django.contrib.admin.sites import site as admin_site
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase
from PIL import Image

from .models import DiveSite, UploadImageModel, UserDiveSite
from .site_conflicts import find_depth_conflict


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
            "new_site_id": "60.1",
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
            "new_site_id": "61.1",
            "new_site_region": "Raja Ampat / Misool - Marine Protected Area",
        })
        site = DiveSite.objects.get(name="Coral Garden")
        self.assertEqual(site.country, "Indonesia")


class UploadPageDiveSiteSelectionTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)
        self.site = DiveSite.objects.create(
            name="Manta Point", region="Bali / Nusa Penida", site_id="60.1"
        )

    def test_upload_page_lists_existing_sites_only(self) -> None:
        response = self.client.get("/upload/")
        self.assertContains(response, "Manta Point")
        self.assertNotContains(response, "new_site_name")

    def test_upload_page_hides_sites_without_site_id(self) -> None:
        DiveSite.objects.create(name="Legacy Kwawi")
        response = self.client.get("/upload/")
        self.assertNotContains(response, "Legacy Kwawi")
        self.assertContains(response, "Kwawi (13.1)")

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


class ReferenceDiveSiteTests(TestCase):
    def test_all_reference_sites_are_imported(self) -> None:
        self.assertEqual(DiveSite.objects.filter(source_version="0.3.0").count(), 34)

    def test_reference_site_keeps_coraldb_values(self) -> None:
        site = DiveSite.objects.get(site_id="13.2")
        self.assertEqual(site.name, "Kwawi (13.2)")
        self.assertEqual(site.region, "Papua Barat / Manokwari")
        self.assertEqual(site.depth, 10)
        self.assertEqual(str(site.latitude), "-0.8762100000")

    def test_reference_sites_are_read_only_in_admin(self) -> None:
        admin_user = User.objects.create_superuser("admin", password="secret123")
        request = type("Request", (), {"user": admin_user})()
        model_admin = admin_site._registry[DiveSite]
        site = DiveSite.objects.get(site_id="13.1")
        self.assertFalse(model_admin.has_change_permission(request, site))
        self.assertFalse(model_admin.has_delete_permission(request, site))

    def test_user_sites_stay_editable_in_admin(self) -> None:
        admin_user = User.objects.create_superuser("admin", password="secret123")
        request = type("Request", (), {"user": admin_user})()
        model_admin = admin_site._registry[DiveSite]
        site = DiveSite.objects.create(name="Manta Point", site_id="60.1")
        self.assertTrue(model_admin.has_change_permission(request, site))


class DepthConflictTests(TestCase):
    def _conflict(self, site_id: str, category: str, custom: str = "") -> str | None:
        return find_depth_conflict(
            DiveSite.objects.get(site_id=site_id), category, custom
        )

    def test_matching_depth_has_no_conflict(self) -> None:
        self.assertIsNone(self._conflict("13.1", "5m"))
        self.assertIsNone(self._conflict("13.1", "0_5m"))

    def test_blank_depth_has_no_conflict(self) -> None:
        self.assertIsNone(self._conflict("13.1", ""))

    def test_mismatch_suggests_sibling_at_entered_depth(self) -> None:
        conflict = self._conflict("13.1", "10m")
        self.assertIn("Kwawi (13.1) is at 5 m", conflict)
        self.assertIn("Did you mean Kwawi (13.2)?", conflict)

    def test_suggestions_skip_siblings_at_other_depths(self) -> None:
        conflict = self._conflict("1.3", "10m")
        self.assertIn("Did you mean Kalig House Reef (1.2)?", conflict)
        self.assertNotIn("(1.1)", conflict)

    def test_mismatch_without_sibling_invites_new_site_id(self) -> None:
        conflict = self._conflict("2.1", "5m")
        self.assertIn("create a new site id", conflict)

    def test_greater_than_ten_metres_conflicts_with_ten_metre_site(self) -> None:
        self.assertIn("create a new site id", self._conflict("13.2", "gt_10m"))

    def test_custom_depth_within_tolerance_matches(self) -> None:
        self.assertIsNone(self._conflict("13.2", "custom", "10.5"))

    def test_custom_depth_outside_tolerance_conflicts(self) -> None:
        conflict = self._conflict("13.2", "custom", "5")
        self.assertIn("Did you mean Kwawi (13.1)?", conflict)

    def test_unparseable_custom_depth_has_no_conflict(self) -> None:
        self.assertIsNone(self._conflict("13.2", "custom", "abc"))

    def test_site_without_depth_never_conflicts(self) -> None:
        site = DiveSite.objects.create(name="Manta Point", site_id="60.1")
        self.assertIsNone(find_depth_conflict(site, "10m", ""))


class UploadSiteEnforcementTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)
        self.kwawi_5m = DiveSite.objects.get(site_id="13.1")

    def _upload(self, site: DiveSite, depth_category: str, **headers: str):
        return self.client.post("/upload/", {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
            "dive_site_id": site.id,
            "depth_category": depth_category,
        }, **headers)

    def test_upload_with_matching_depth_succeeds(self) -> None:
        self._upload(self.kwawi_5m, "5m")
        self.assertEqual(UploadImageModel.objects.get().dive_site, self.kwawi_5m)

    def test_depth_conflict_blocks_upload(self) -> None:
        response = self._upload(self.kwawi_5m, "10m")
        self.assertContains(response, "Did you mean Kwawi (13.2)?")
        self.assertEqual(UploadImageModel.objects.count(), 0)

    def test_depth_conflict_returns_json_error_for_batches(self) -> None:
        response = self._upload(self.kwawi_5m, "10m", HTTP_X_UPLOAD_BATCH="1")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Did you mean Kwawi (13.2)?", response.json()["error"])

    def test_site_without_site_id_is_rejected(self) -> None:
        legacy = DiveSite.objects.create(name="Legacy Kwawi")
        response = self._upload(legacy, "5m")
        self.assertContains(response, "Please select a registered site id")
        self.assertEqual(UploadImageModel.objects.count(), 0)

    def test_unknown_site_is_rejected(self) -> None:
        response = self.client.post("/upload/", {
            "images": [_make_test_image()],
            "diving_date": "2026-07-30",
            "dive_site_id": "999999",
        })
        self.assertContains(response, "Please select a registered site id")


class ProfileNewSiteIdTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="diver", password="secret123")
        self.client.force_login(self.user)

    def _add_site(self, name: str, site_id: str, depth: str = "") -> None:
        self.client.post("/profile/", {
            "action": "add_dive_site",
            "new_site_name": name,
            "new_site_id": site_id,
            "new_site_region": "Papua Barat / Manokwari",
            "depth": depth,
        })

    def _error_messages(self) -> list[str]:
        response = self.client.get("/profile/")
        return [str(m) for m in response.context["messages"]]

    def test_new_site_stores_site_id_and_depth(self) -> None:
        self._add_site("Kwawi deep", "13.3", "18")
        site = DiveSite.objects.get(site_id="13.3")
        self.assertEqual(site.depth, 18)
        self.assertFalse(site.is_reference)
        self.assertEqual(site.created_by, self.user)

    def test_new_site_requires_valid_site_id(self) -> None:
        self._add_site("Kwawi deep", "deep")
        self.assertFalse(DiveSite.objects.filter(name="Kwawi deep").exists())
        self.assertIn("Please enter a site id like 13.3", self._error_messages()[0])

    def test_existing_site_id_is_rejected_and_left_unchanged(self) -> None:
        self._add_site("Not Kwawi", "13.1", "30")
        site = DiveSite.objects.get(site_id="13.1")
        self.assertEqual(site.name, "Kwawi (13.1)")
        self.assertEqual(site.depth, 5)
        self.assertIn("already registered as Kwawi (13.1)", self._error_messages()[0])

    def test_existing_name_is_rejected(self) -> None:
        self._add_site("Kwawi (13.1)", "13.3")
        self.assertFalse(DiveSite.objects.filter(site_id="13.3").exists())

    def test_profile_prefills_suggested_site_id(self) -> None:
        response = self.client.get("/profile/?new_site_id=13.3&depth=18")
        self.assertContains(response, 'value="13.3"')
        self.assertContains(response, 'value="18"')
