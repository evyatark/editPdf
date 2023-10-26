import sys
import getopt
import fitz

def f2():
    doc = fitz.open("own1.pdf")
    length = len(doc)
    print(doc.get_page_fonts(0))
    page = doc[0]
    text = page.get_text()
    as_dict = page.get_text("dict")
    #print(page.get_textpage().extractWORDS())
    print(page.get_textpage().extractRAWJSON())
    #print(length)
    #print(text)
    #print(as_dict['blocks'][5]['lines'][0]['spans'][1]['text'])
    
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

def main():
    f2()

if __name__== '__main__':
    main()

