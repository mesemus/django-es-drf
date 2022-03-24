from rest_framework.routers import DefaultRouter

from tests.app.api import SchoolAPI, SchoolAPI2

router = DefaultRouter()
router.register("schools", SchoolAPI, "schools")
router.register("schools2", SchoolAPI2, "schools2")

urlpatterns = router.urls
