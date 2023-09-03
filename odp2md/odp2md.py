#!/usr/bin/env python3

'''

2023-09-02 Modified by Rubén Béjar
    - Added support for bold, italic and underline text styles

odp2md 2021.5.0

ODP2Pandoc is a tiny tool to convert 
OpenDocument formatted presentations (ODP) 
to Pandocs' Markdown.

(c) Copyright 2019-2021 Hartmut Seichter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Usage:

$> python odp2md --input <myslide.odp>

 '''

import os
import zipfile
import argparse
import sys
import re, unicodedata
import textwrap
from enum import Enum
import xml.dom.minidom as dom

class Slide:
    def __init__(self):
        self.title = ''
        self.text = ''
        self.notes = ''
        self.media = []
        self.titleLevel = 2 # by default 2; for the first one this will be 1

    def generateMarkdown(self,blockToHTML=True):
        # fix identation
        self.text = textwrap.dedent(self.text)
        out = ('#' * self.titleLevel) + ' {0}\n\n{1}\n'.format(self.title,self.text)
        for m,v in self.media:

            # maybe let everything else fail?
            isVideo = any(x in v for x in ['.mp4','.mkv'])

            if blockToHTML and isVideo:
                # since LaTeX extensions for video are deprecated 
                out += '`![]({0})`{{=html}}\n'.format(v)
            else:
                out += '![]({0})\n'.format(v)
        return out
    
    # override string representation
    def __str__(self):
        return self.generateMarkdown()

class Scope(Enum):

    NONE = 0
    TITLE = 1
    OUTLINE = 2
    NOTES = 3
    IMAGES = 4


class Parser:

    def __init__(self):
        self.slides = []
        self.currentSlide = None
        self.currentText = ''
        self.currentDepth = 0
        self.currentScope = Scope.NONE
        self.mediaDirectory = 'media'
        self.hiddenPageStyles = set()
        self.debug = False

    def getTextFromNode(self,node):
        if node.nodeType == node.TEXT_NODE and len(str(node.data)) > 0:
            return node.data
        return None

    def hasAttributeWithValue(self,node,name,value):
        if node.attributes == None:
            return False
        for attribute_name,attribute_value in node.attributes.items():
            if attribute_name == name and attribute_value == value:
                return True
        return False

    def debugNode(self,node):
        if self.debug:
            print(node.nodeName, node.nodeType, node.attributes[
                'presentation:class'].value if node.attributes is not None and 'presentation:class' in node.attributes else '')

    def slugify(self,value, allow_unicode=False):
        '''
        Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
        Remove characters that aren't alphanumerics, underscores, or hyphens.
        Convert to lowercase. Also strip leading and trailing whitespace.
        '''
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
        return re.sub(r'[-\s]+', '-', value)

    def handleImage(self, node):
        self.debugNode(node)

        for k, v in node.attributes.items():
            if k == 'xlink:href':
                # get the extension
                name, ext = os.path.splitext(v)
                ext = ext.lower()
                # now we create a new slug name for conversion
                slug = self.slugify(self.currentSlide.title)
                if len(slug) < 1:
                    slug = 'slide-' + str(len(self.slides)) + '-image'
                slug += '-' + str(len(self.currentSlide.media))
                slug = (slug[:128]) if len(slug) > 128 else slug  # truncate
                self.currentSlide.media.append((v, os.path.join(self.mediaDirectory, slug + ext)))


    def handleTextNode(self, node):
        for n in node.childNodes:
            if n.nodeName == 'text:span':
                t = self.getTextFromNode(n.childNodes[0])
                if self.hasAttributeWithValue(n, 'text:style-name', 'T1'):
                    t = '*' + t + '*'
                elif self.hasAttributeWithValue(n, 'text:style-name', 'T2'):
                    t = '**' + t + '**'
                elif self.hasAttributeWithValue(n, 'text:style-name', 'T3'):
                    t = '<u>' + t + '</u>'
                else:   # ignore other styles
                    pass
            else:
                t = self.getTextFromNode(n)

            if t is not None:
                if self.currentSlide.text[:-1] != ' ':
                    self.currentSlide.text += ' '
                self.currentSlide.text += t

    def handleListNode(self, node):
        def _handleListNodeRec(node, depth):
            for n in node.childNodes:
                if n.nodeName == 'text:list':
                    self.currentSlide.text += ('    ' * depth)
                    _handleListNodeRec(n, depth + 1)
                elif n.nodeName == 'text:list-item':
                    self.currentSlide.text += '\n' + ('    ' * depth) + '- ' # space after hyphen is required
                    _handleListNodeRec(n, depth)
                elif n.nodeName == 'text:p':
                    self.handleTextNode(n)
                elif n.nodeName == 'text:list-header':
                    _handleListNodeRec(n, depth)
        _handleListNodeRec(node, -1)

    def handleTextBox(self, node):
        for n in node.childNodes:
            self.handleTextNode(n)

    def handleTitle(self, node):
        def _handleTitleRec(node):
            if node.nodeName == 'text:span':
                t = self.getTextFromNode(node.childNodes[0])
                if self.hasAttributeWithValue(node, 'text:style-name', 'T1'):
                    t = '*' + t + '*'
                elif self.hasAttributeWithValue(node, 'text:style-name', 'T2'):
                    t = '**' + t + '**'
                elif self.hasAttributeWithValue(node, 'text:style-name', 'T3'):
                    t = '<u>' + t + '</u>'
                else:  # ignore other styles
                    pass
                self.currentSlide.title += t
            else:
                t = self.getTextFromNode(node)
                if t is None:
                    for n in node.childNodes:
                        _handleTitleRec(n)
                else:
                    self.currentSlide.title += t

        _handleTitleRec(node)

    def handleOutline(self, node):
        self.debugNode(node)

        for n in node.childNodes:
            self.debugNode(n)
            self.handleListNode(n)

    def handleSlide(self, page):
        self.currentSlide.name = page.attributes['draw:name']
        for item in page.childNodes:
            self.debugNode(item)
            if self.hasAttributeWithValue(item, 'presentation:class', 'title'):
                self.handleTitle(item)
            elif self.hasAttributeWithValue(item, 'presentation:class', 'outline'):
                self.currentDepth = 0
                self.handleOutline(item)
            elif item.nodeName == 'draw:frame':
                for n in item.childNodes:
                    if n.nodeName in ['draw:image', 'draw:plugin']:
                        self.handleImage(n)
                    elif n.nodeName == 'draw:text-box':
                        self.handleTextBox(n)
            elif item.nodeName == 'draw:custom-shape':
                if item.childNodes[0].nodeName == 'text:list':
                    self.handleListNode(item)
                elif item.childNodes[0].nodeName == 'draw:text-box':
                    self.handleTextBox(item)
                else:
                    self.handleTextNode(item)
        # If a slide does not have a title, but it has a text and it does not have media, then we use
        # that as the title. If it had media, the text is probably some kind of caption/explanation.
        # TODO: this seems as a reasonable default, but it probably should be a command-line switch
        if (self.currentSlide.title is None or self.currentSlide.title == "") and \
                self.currentSlide.text is not None and self.currentSlide.text != "" and \
                len(self.currentSlide.media) == 0:
            self.currentSlide.title = self.currentSlide.text
            self.currentSlide.text = ""

    def handleDocument(self,dom):
        # We need the styles to find out if some slides are not visible (we might not want to export them)
        styles = dom.getElementsByTagName('style:style')
        for s in styles:
            style_name = s.attributes['style:name'].value
            for ss in s.childNodes:
                if self.hasAttributeWithValue(ss, 'presentation:visibility', 'hidden'):
                    self.hiddenPageStyles.add(style_name)
        # Pages
        pages = dom.getElementsByTagName('draw:page')
        # iterate pages
        for page in pages:
            self.debugNode(page)
            # we skip hidden pages (TODO: command-line switch for this?)
            if not page.attributes['draw:style-name'].value in self.hiddenPageStyles:
                self.currentSlide = Slide()
                self.handleSlide(page)
                self.slides.append(self.currentSlide)

    def createATitleSlide(self, fname):
        slide_0 = Slide()
        slide_0.title = fname
        slide_0.titleLevel = 1
        self.slides.append(slide_0)


    def open(self,fname,mediaDir='media',markdown = False,mediaExtraction = False):
        
        self.mediaDirectory = mediaDir

        # We create a "title slide" with the name of the file.
        # This allows for having a level 1 title in the document, which is useful for having a TOC in mkdocs
        self.createATitleSlide(os.path.basename(fname))

        # open odp file
        with zipfile.ZipFile(fname) as odp:
            info = odp.infolist()
            for i in info:
                if (i.filename == 'content.xml'):
                    with odp.open('content.xml') as index:
                        doc = dom.parseString(index.read())
                        self.handleDocument(doc)

        
            # output markdown
            if markdown == True:
                for slide in self.slides:
                        print(slide)

            # generate files
            if mediaExtraction == True:           
                for slide in self.slides:
                    for m,v in slide.media:
                        try:
                            odp.extract(m,'.')
                            if not os.path.exists(self.mediaDirectory):
                                os.makedirs(self.mediaDirectory)
                            os.rename(os.path.join('.',m),v)
                        except KeyError:
                            print('error finding media file ',m)
                        



def main(argv=None):

    if argv is None:
        argv = sys.argv

    argument_parser = argparse.ArgumentParser(description='OpenDocument Presentation converter',
                                              epilog='It will not output hidden slides.')
    
    argument_parser.add_argument('-i','--input', required=True,help='ODP file to parse and extract')
    argument_parser.add_argument('-m','--markdown', help='generate Markdown files', action='store_true')
    argument_parser.add_argument('-b','--blocks', help='generate pandoc blocks for video files', action='store_true')
    argument_parser.add_argument('-x','--extract', help='extract media files', action='store_true')
    argument_parser.add_argument('--mediadir', required=False,default='media',help='output directory for linked media')
    
    args = argument_parser.parse_args()

    # print(args)
    # return

    juicer = Parser()
    if 'input' in args:
        juicer.open(args.input,args.mediadir,args.markdown,args.extract)
    else:
        argument_parser.print_help()
        return

if __name__ == '__main__':
    sys.exit(main(sys.argv))