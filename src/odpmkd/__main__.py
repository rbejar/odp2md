from .odp_markdown import *
import argparse
import sys


def main(argv=None):
    if argv is None:
        argv = sys.argv

    argument_parser = argparse.ArgumentParser(prog='odp-markdown',
                                              description='OpenDocument Presentation converter',
                                              epilog='It will not output hidden slides.')

    argument_parser.add_argument('-i', '--input', required=True, help='ODP file to parse and extract')
    argument_parser.add_argument('-m', '--markdown', help='generate Markdown files', action='store_true')
    argument_parser.add_argument('-b', '--blocks', help='generate pandoc blocks for video files', action='store_true')
    argument_parser.add_argument('-x', '--extract', help='extract media files', action='store_true')
    argument_parser.add_argument('--mediadir', required=False, default='media',
                                 help='output directory for linked media')

    args = argument_parser.parse_args()

    # print(args)
    # return

    juicer = Parser()
    if 'input' in args:
        juicer.open(args.input, args.mediadir, args.markdown, args.extract)
    else:
        argument_parser.print_help()
        return


if __name__ == '__main__':
    main()
