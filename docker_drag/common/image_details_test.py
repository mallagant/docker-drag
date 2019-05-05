from unittest import TestCase

from docker_drag.common.image_details import ImageDetails


class TestFromDict(TestCase):
    def test_returns_simple_image_with_defaults(self):
        image_name = "hello-world"
        details = ImageDetails.from_dict({"image": image_name})

        self.assertEqual(details, ImageDetails(image_name, ImageDetails.TAG_DEFAULT, ImageDetails.REPOSITORY_DEFAULT))

