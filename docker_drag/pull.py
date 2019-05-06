from typing import Union

import requests

from docker_drag.common.image_details import ImageDetails


class Puller(object):
    def __init__(self, image_details: Union[str, ImageDetails]):
        if type(image_details) == str:
            self.image_details: ImageDetails = ImageDetails.from_dict({"image": image_details})
        else:
            self.image_details: ImageDetails = image_details

    def _get_auth_headers(self) -> dict:
        """
        Get Docker token and fetch manifest v2.
        :return: The header that should be sent to the repo to authenticate the requests.
        """
        resp = requests.get(
            f'https://auth.docker.io/token?service=registry.docker.io'
            f'&scope=repository:{self.image_details.repository_and_image}:pull',
            verify=False)
        access_token = resp.json()['access_token']
        return {'Authorization': 'Bearer ' + access_token,
                'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}

    def _get_layers(self, request_header: dict):
        url = 'https://registry-1.docker.io/v2/{}/manifests/{}'.format(
            self.image_details.repository_and_image,
            self.image_details.tag)

        # Get image layer digests
        resp = requests.get(url, headers=request_header, verify=False)
        if resp.status_code != 200:
            print('Cannot fetch manifest for {} [HTTP {}]'.format(self.image_details.repository_and_image,
                                                                  resp.status_code))
            exit(1)
        layers = resp.json()['layers']
        return layers
