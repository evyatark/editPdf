import sys
import getopt
import fitz
import os
import time
import json
from pprint import pprint


# This prog uses a different method than the replace01, replace02
# it uses annotation redactions as suggested in: https://stackoverflow.com/a/75387883


def main():
    replace_main()
    

def replace_main():
    print('===')
    infilename = "own1.pdf"
    if len(sys.argv) > 1:
        infilename = sys.argv[1]
    indoc = fitz.open(infilename)  # input PDF
    page = indoc[0]  # page number 0-based
    # suppose you want to replace all occurrences of some text
    disliked = "111111"
    better   = "333333"
    hits = page.search_for(disliked)  # list of rectangles where to replace
    print(len(hits))

    # the following is used to add the Arial font to the PDF document
    page.insert_text((0,0),  # anywhere, but outside all redaction rectangles
        "something",  # some non-empty string
        fontname="arial",  # new, unused reference name
        fontfile="C:/Windows/Fonts/arial.ttf",  # desired font file
        render_mode=3,  # makes the text invisible
    )
    
    for rect in hits:
        print(rect)
        page.add_redact_annot(rect, better, fontname="arial", fontsize=14,
                                align=fitz.TEXT_ALIGN_CENTER)  # more parameters

    # without the following line: the new PDF will display the redacted places in RED boxes!!
    #page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)  # don't touch images
    indoc.save(indoc.name.replace(".pdf", "-new.pdf"), garbage=3, deflate=True)


if __name__== '__main__':
    main()

