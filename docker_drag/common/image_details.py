

class ImageDetails(object):
    TAG_DEFAULT = "latest"
    REPOSITORY_DEFAULT = "library"

    def __init__(self, image: str, tag: str = None, repository: str = None):
        self.image = image
        self.tag = tag
        self.repository = repository

    @property
    def repository_and_image(self):
        name = self.image
        if self.repository:
            name = self.repository + "/" + name
        return name

    @property
    def full_name(self) -> str:
        name = self.repository_and_image
        if self.tag:
            name = name + ":" + self.tag
        return name

    @staticmethod
    def from_dict(args_dict: dict) -> "ImageDetails":
        image: str = args_dict["image"]
        tag = args_dict.get("tag", ImageDetails.TAG_DEFAULT)
        if image.count(":") == 1:
            image, tag = image.split(":")[1]

        repository = args_dict.get("repository", ImageDetails.REPOSITORY_DEFAULT)
        if "/" in image:
            repository, image = image.split("/")[0]

        return ImageDetails(image, tag, repository)

    def __repr__(self) -> str:
        return self.full_name

    def __eq__(self, other: "ImageDetails") -> bool:
        if self.image != other.image:
            return False
        if self.tag != other.tag:
            return False
        if self.repository != other.repository:
            return False
        return True
