import sys
import getopt
import fitz
import os
import time
import json
from pprint import pprint

def main():
    replace_main()
    f2()

def read_fonts(infilename):
    repl_filename = infilename + "-fontnames.json"
    indoc = fitz.open(infilename)  # input PDF
    if os.path.exists(repl_filename):
        new_fontnames, font_subsets, font_buffers = build_repl_table(indoc, repl_filename)

    if new_fontnames == {}:
        sys.exit("\n***** There are no fonts to replace. *****")
    print(
        "Processing PDF '%s' with %i page%s.\n"
        % (indoc.name, indoc.page_count, "s" if indoc.page_count > 1 else "")
    )
    return new_fontnames, font_subsets, font_buffers

def analyze_font_use(infilename, new_fontnames, font_subsets):
    # the following flag prevents images from being extracted:
    extr_flags = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
    indoc = fitz.open(infilename)  # input PDF
    page = indoc[0] # first page. Assume doc has one page!!
    fontrefs = get_page_fontrefs(page, new_fontnames)
    if fontrefs == {}:  # page has no fonts to replace
        print('page has no font refs!')
        return
    blocks_dict = page.get_text("dict", flags=extr_flags)["blocks"]
    block_number = 0
    for block in blocks_dict:
        block_number = block_number + 1
        line_number = 0
        for line in block["lines"]:
            line_number = line_number + 1
            span_number = 0
            for span in line["spans"]:
                span_number = span_number + 1
                font_subsets = do_for_each_span(span, span_number, block_number, line_number, new_fontnames, font_subsets)

def do_for_each_span(span, span_number, block_number, line_number, new_fontnames, font_subsets):
    font_in_this_span = span["font"]
    text_in_this_span = span["text"]
    bbox_of_this_span = span["bbox"]
    originX = int(span["origin"][0])    # int() converts to a number and rounds the decimal part
    originY = int(span["origin"][1])
    new_fontname = get_new_fontname(font_in_this_span, new_fontnames)
    # here we could store the parts of data according to (block, line, span) or according to origin x, y
    # then later we could use this data to replace the text with something else in specified parts
    # (currently only displaying:)
    print('block', block_number, 'line', line_number, 'span', span_number, 'at (', originX, ',', originY, ') : text=', text_in_this_span, 'bbox=', bbox_of_this_span, 'old font=', font_in_this_span, 'should be replaced with', new_fontname)
    if new_fontname is None:  # do not replace this font
        return
    ## build an extended font subset which includes all characters of the original text, with the new font
    # (this is not needed in our code)
    font_subsets = extend_font_subset(span, new_fontname, font_subsets)
    return font_subsets


def extend_font_subset(span, new_fontname, font_subsets):
    # replace non-utf8 by section symbol
    text = span["text"].replace(chr(0xFFFD), chr(0xB6))
    # extend collection of used unicodes
    subset = font_subsets.get(new_fontname, set())
    for c in text:
        subset.add(ord(c))  # add any new unicode values
    font_subsets[new_fontname] = subset  # store back extended set
    return font_subsets


def rebuild_document(infilename, new_fontnames, font_buffers):
    # Phase 2
    print("Phase 2: Rebuild document with new fonts/text")

    extr_flags = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
    indoc = fitz.open(infilename)  # input PDF
    page = indoc[0] # first page. Assume doc has one page!!

    # extract text again
    blocks = page.get_text("dict", flags=extr_flags)["blocks"]

    # clean contents streams of the page and any XObjects.  (why do we need it?)
    page.clean_contents(sanitize=True)
    fontrefs = get_page_fontrefs(page, new_fontnames)
    if fontrefs == {}:  # page has no fonts to replace
        #continue
        print('no font replacements, ignoring...')
    cont_clean(page, fontrefs)  # remove text using fonts to be replaced
    add_text(page, blocks, font_buffers, new_fontnames)


def add_text(page, blocks, font_buffers, new_fontnames):
    textwriters = {}  # contains one text writer per detected text color
    for block in blocks:
        add_text_to_block(page, textwriters, block, font_buffers, new_fontnames)

def add_text_to_block(page, textwriters, block, font_buffers, new_fontnames):
    for line in block["lines"]:
        add_text_to_line(page, textwriters, line, font_buffers, new_fontnames)

def add_text_to_line(page, textwriters, line, font_buffers, new_fontnames):
    wmode = line["wmode"]  # writing mode (horizontal, vertical)
    wdir = list(line["dir"])  # writing direction
    markup_dir = 0
    bidi_level = 0  # not used
    if wdir == [0, 1]:
        markup_dir = 4
    for span in line["spans"]:
        new_fontname = get_new_fontname(span["font"], new_fontnames)
        if new_fontname is None:  # do not replace this font
            continue

        font = fitz.Font(fontbuffer=font_buffers[new_fontname])
        text = span["text"].replace(chr(0xFFFD), chr(0xB6))
        # guard against non-utf8 characters
        textb = text.encode("utf8", errors="backslashreplace")
        text = textb.decode("utf8", errors="backslashreplace")
        span["text"] = text # <=== HERE WE CAN CHANGE THE TEXT!!
        print('writing text to PDF: ', text)
        if wdir != [1, 0]:  # special treatment for tilted text
            print('required special treatment for tilted text temporarily ignored!')
            #tilted_span(page, wdir, span, font)
            continue
        color = span["color"]  # make or reuse textwriter for the color
        if color in textwriters.keys():  # already have a textwriter?
            tw = textwriters[color]  # re-use it
        else:  # make new
            tw = fitz.TextWriter(page.rect)  # make text writer
            textwriters[color] = tw  # store it for later use
        try:
            tw.append(
                span["origin"],
                text,
                font=font,
                #fontsize=resize(span, font),  # use adjusted fontsize  - temporarily ignored!
                fontsize = span["size"]  # old fontsize
            )
        except:
            print("page %i exception:" % page.number, text)


def remove_font(fontrefs, lines):
    """This inline function removes references to fonts in a /Contents stream.

    Args:
        fontrefs: a list of bytes objects looking like b"/fontref ".
        lines: a list of the lines of the /Contents.
    Returns:
        (bool, lines), where the bool is True if we have changed any of
        the lines.
    """
    changed = False
    count = len(lines)
    for ref in fontrefs:
        found = False  # switch: processing our font
        for i in range(count):
            if lines[i] == b"ET":  # end text object
                found = False  # no longer in found mode
                continue
            if lines[i].endswith(b" Tf"):  # font invoker command
                if lines[i].startswith(ref):  # our font?
                    found = True  # switch on
                    lines[i] = b""  # remove line
                    changed = True  # tell we have changed
                    continue  # next line
                else:  # else not our font
                    found = False  # switch off
                    continue  # next line
            if found == True and (
                lines[i].endswith(
                    (
                        b"TJ",
                        b"Tj",
                        b"TL",
                        b"Tc",
                        b"Td",
                        b"Tm",
                        b"T*",
                        b"Ts",
                        b"Tw",
                        b"Tz",
                        b"'",
                        b'"',
                    )
                )
            ):  # write command for our font?
                lines[i] = b""  # remove it
                changed = True  # tell we have changed
                continue
    return changed, lines


def cont_clean(page, fontrefs):
    """Remove text written with one of the fonts to replace.

    Args:
        page: the page
        fontrefs: dict of contents stream xrefs. Each xref key has a list of
            ref names looking like b"/refname ".
    """
    doc = page.parent
    for xref in fontrefs.keys():
        xref0 = 0 + xref
        if xref0 == 0:  # the page contents
            xref0 = page.get_contents()[0]  # there is only one /Contents obj now
        cont = doc.xref_stream(xref0)
        cont_lines = cont.splitlines()
        changed, cont_lines = remove_font(fontrefs[xref], cont_lines)
        if changed:
            cont = b"\n".join(cont_lines) + b"\n"
            doc.update_stream(xref0, cont)  # replace command source


def replace_main():
    infilename = "own1.pdf"
    if len(sys.argv) > 1:
        infilename = sys.argv[1]
    # indoc = fitz.open(infilename)  # input PDF

    new_fontnames1, font_subsets1, font_buffers = read_fonts(infilename)
    analyze_font_use(infilename, new_fontnames1, font_subsets1)
    rebuild_document(infilename, new_fontnames1, font_buffers)



def build_repl_table(doc, fname):
    """Populate font replacement information.

    Read the JSON font relacement file and store its information in
    dictionaries 'font_subsets', 'font_buffers' and 'new_fontnames'.
    """
    font_subsets = {}
    font_buffers = {}
    new_fontnames = {}

    fd = open(fname)
    fontdicts = json.load(fd)
    fd.close()

    for fontdict in fontdicts:
        oldfont = fontdict["oldfont"]
        newfont = fontdict["newfont"].strip()

        if newfont == "keep":  # ignore if not replaced
            continue
        if "." in newfont or "/" in newfont or "\\" in newfont:
            try:
                font = fitz.Font(fontfile=newfont)
            except:
                sys.exit("Could not create font '%s'." % newfont)
            fontbuffer = font.buffer
            new_fontname = font.name
            font_subsets[new_fontname] = set()
            font_buffers[new_fontname] = fontbuffer
            for item in oldfont:
                new_fontnames[item] = new_fontname
            del font
            continue

        try:
            font = fitz.Font(newfont)
        except:
            sys.exit("Could not create font '%s'." % newfont)
        fontbuffer = font.buffer
        new_fontname = font.name
        font_subsets[new_fontname] = set()
        font_buffers[new_fontname] = fontbuffer
        for item in oldfont:
            new_fontnames[item] = new_fontname
        del font
        continue
    
    return new_fontnames, font_subsets, font_buffers


def get_page_fontrefs(page, new_fontnames):
    fontlist = page.get_fonts(full=True)
    # Ref names for each font to replace.
    # Each contents stream has a separate entry here: keyed by xref,
    # 0 = page /Contents, otherwise xref of XObject
    fontrefs = {}
    for f in fontlist:
        fontname = f[3]
        cont_xref = f[-1]  # xref of XObject, 0 if page /Contents
        idx = fontname.find("+") + 1
        fontname = fontname[idx:]  # remove font subset indicator
        if fontname in new_fontnames.keys():  # we replace this font!
            refname = f[4]
            refname = b"/" + refname.encode() + b" "
            refs = fontrefs.get(cont_xref, [])
            refs.append(refname)
            fontrefs[cont_xref] = refs
    return fontrefs  # return list of font reference names


def get_new_fontname(old_fontname, new_fontnames):
    """Determine new fontname for a given old one.

    Return None if not found. The complex logic part is required because font
    name length is restricted to 32 bytes (by MuPDF).
    So we check instead, whether a dict key "almost" matches.
    """
    new_fontname = new_fontnames.get(old_fontname, None)
    if new_fontname:  # the simple case.
        return new_fontname
    fontlist = [  # build list of "almost matching" keys
        new_fontnames[n]
        for n in new_fontnames.keys()
        if n.startswith(old_fontname) or old_fontname.startswith(n)
    ]
    if fontlist == []:
        return None
    # the list MUST contain exactly one item!
    if len(fontlist) > 1:  # this should not happen!
        error_exit(old_fontname, "new fontname")
    return fontlist[0]


def error_exit(searchname, name):
    print("Error occurred for '%s' ==> '%s'" % (searchname, name))
    # display_tables()
    sys.exit()


def f2():
    doc = fitz.open("own1.pdf")
    length = len(doc)
    #print(doc.get_page_fonts(0))
    page = doc[0]
    text = page.get_text()
    as_dict = page.get_text("dict")
    #print(page.get_textpage().extractWORDS())
    #print(page.get_textpage().extractRAWJSON())
    #print(length)
    #print(text)
    print(as_dict['blocks'][5]['lines'][0]['spans'][1]['text'])
    
    # {
    #     'spans': [
    #         {
    #             'size': 9.977970123291016, 
    #             'flags': 20, 
    #             'font': 
    #             'Arial-BoldMT', 
    #             'color': 4144959, 
    #             'ascender': 0.9052734375, 
    #             'descender': -0.2119140625, 
    #             'text': ':קנב:ףינס:ןובשח', 
    #             'origin': (555.2589721679688, 109.68902587890625), 
    #             'bbox': (394.1659851074219, 100.65623474121094, 573.8947143554688, 111.80349731445312)
    #         }, 
    #         {
    #             'size': 9.977970123291016, 
    #             'flags': 4, 
    #             'font': 'ArialMT', 
    #             'color': 4144959, 
    #             'ascender': 0.9052734375, 
    #             'descender': -0.2119140625, 
    #             'text': 'רתיבא יפכפכו רמת ןמדלוג', 
    #             'origin': (537.2589721679688, 109.68902587890625), 
    #             'bbox': (224.3132781982422, 100.65623474121094, 548.35595703125, 111.80349731445312)
    #         }
    #     ], 
    #     'wmode': 0, 
    #     'dir': (1.0, 0.0), 
    #     'bbox': (224.3132781982422, 100.65623474121094, 573.8947143554688, 111.80349731445312)
    # }


def f1():
    args, opts = getopt.getopt(sys.argv, "?h")
    #print(args)
    print(opts)


if __name__== '__main__':
    main()

