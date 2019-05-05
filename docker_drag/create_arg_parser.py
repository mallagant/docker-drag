from argparse import ArgumentParser


def create_arg_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("image",
                        type=str,
                        help="the name of the image you would like to get.")

    parser.add_argument("-t", "--tag",
                        type=str,
                        dest="tag",
                        nargs=1,
                        help="the tag of the chosen image.")

    parser.add_argument("-r", "--repository",
                        type=str,
                        dest="repository",
                        nargs=1,
                        help="the repository to pull the image from.")
    return parser


if __name__ == '__main__':
    print(create_arg_parser().parse_args(["-h"]))
