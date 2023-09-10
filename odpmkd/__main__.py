from .odpmkd import *


def main():
    argument_parser = argparse.ArgumentParser(prog='odpmkd',
                                              description='OpenDocument Presentation converter',
                                              epilog='It will not output hidden slides.')

    argument_parser.add_argument('-i', '--input', required=True, help='ODP file to parse and extract')
    argument_parser.add_argument('-m', '--markdown', help='generate Markdown files', action='store_true')
    argument_parser.add_argument('-b', '--blocks', help='generate pandoc blocks for video files', action='store_true')
    argument_parser.add_argument('-x', '--extract', help='extract media files', action='store_true')
    argument_parser.add_argument('--mediadir', required=False, default='media',
                                 help='output directory for linked media')

    args = argument_parser.parse_args()

    odp_parser = OdpParser()
    if 'input' in args:
        odp_parser.open(args.input, args.mediadir, args.markdown, args.extract)
    else:
        argument_parser.print_help()


if __name__ == '__main__':
    main()
