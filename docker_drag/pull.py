import gzip
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
from io import BytesIO
from typing import Union

import requests
import urllib3

from docker_drag.common.image_details import ImageDetails

urllib3.disable_warnings()


class Puller(object):
    def __init__(self, image_details: ImageDetails):
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

    def _get_layers_structure(self, request_header: dict):
        url = 'https://registry-1.docker.io/v2/{}/manifests/{}'.format(
            self.image_details.repository_and_image,
            self.image_details.tag)

        # Get image layer digests
        resp = requests.get(url, headers=request_header, verify=False)
        return resp.json()

    def _downloadimage_files(self, headers, layers_structure):
        imgdir = tempfile.mkdtemp()

        layers = layers_structure['layers']
        config = layers_structure['config']['digest']
        confresp = requests.get('https://registry-1.docker.io/v2/{}/blobs/{}'.format(
            self.image_details.repository_and_image, config),
            headers=headers,
            verify=False)
        file = open('{}/{}.json'.format(imgdir, config[7:]), 'wb')
        file.write(confresp.content)
        file.close()

        content = [{
            'Config': config[7:] + '.json',
            'RepoTags': [self.image_details.full_name],
            'Layers': []
        }]

        empty_json = '{"created":"1970-01-01T00:00:00Z","container_config":{"Hostname":"","Domainname":"","User":"","AttachStdin":false, \
        "AttachStdout":false,"AttachStderr":false,"Tty":false,"OpenStdin":false, "StdinOnce":false,"Env":null,"Cmd":null,"Image":"", \
        "Volumes":null,"WorkingDir":"","Entrypoint":null,"OnBuild":null,"Labels":null}}'

        # Build layer folders
        parentid = ''
        for layer in layers:
            ublob = layer['digest']
            # FIXME: Creating fake layer ID. Don't know how Docker generates it
            fake_layerid_raw = parentid + '\n' + ublob + '\n'
            fake_layerid = hashlib.sha256(fake_layerid_raw.encode('utf-8')).hexdigest()
            layerdir = imgdir + '/' + fake_layerid
            os.mkdir(layerdir)

            # Creating VERSION file
            file = open(layerdir + '/VERSION', 'w')
            file.write('1.0')
            file.close()

            # Creating layer.tar file
            print(ublob[7:19] + ': Downloading...', )
            sys.stdout.flush()
            bresp = requests.get(
                'https://registry-1.docker.io/v2/{}/blobs/{}'.format(self.image_details.repository_and_image, ublob),
                headers=headers,
                verify=False)
            print("\r{}: Pull complete [{}]".format(ublob[7:19], bresp.headers['Content-Length']))
            content[0]['Layers'].append(fake_layerid + '/layer.tar')
            file = open(layerdir + '/layer.tar', "wb")
            mybuff = BytesIO(bresp.content)
            unzLayer = gzip.GzipFile(fileobj=mybuff)
            file.write(unzLayer.read())
            unzLayer.close()
            file.close()

            # Creating json file
            file = open(layerdir + '/json', 'w')
            # last layer = config manifest - history - rootfs
            if layers[-1]['digest'] == layer['digest']:
                # FIXME: json.loads() automatically converts to unicode, thus decoding values whereas Docker doesn't
                json_obj = json.loads(confresp.content)
                del json_obj['history']
                del json_obj['rootfs']
            else:  # other layers json are empty
                json_obj = json.loads(empty_json)
            json_obj['id'] = fake_layerid
            if parentid:
                json_obj['parent'] = parentid
            parentid = json_obj['id']
            file.write(json.dumps(json_obj))
            file.close()

        file = open(imgdir + '/manifest.json', 'w')
        file.write(json.dumps(content))
        file.close()

        content = {self.image_details.repository_and_image: {self.image_details.tag: fake_layerid}}
        file = open(imgdir + '/repositories', 'w')
        file.write(json.dumps(content))
        file.close()

        # Create image tar and clean tmp folder
        docker_tar = self.image_details.repository + '_' + self.image_details.image + '.tar'
        tar = tarfile.open(docker_tar, "w")
        tar.add(imgdir, arcname=os.path.sep)
        tar.close()
        shutil.rmtree(imgdir)
        print('Docker image pulled: ' + docker_tar)

    def run(self):
        headers = self._get_auth_headers()
        layers_structure = self._get_layers_structure(headers)
        self._downloadimage_files(headers, layers_structure)


def pull(image_details: Union[str, dict, ImageDetails]):
    if type(image_details) == str:
        image_details = ImageDetails.from_dict({"image": image_details})
    elif type(image_details) == dict:
        image_details = ImageDetails.from_dict(image_details)

    puller = Puller(image_details)
    puller.run()


if __name__ == '__main__':
    pull("hello-world")
