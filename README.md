# Edit Pdf Project
Purpose: Read and change PDF documents programmatically.

The end result of this project is to generate PDF documents with a fictive content, based on real PDF documents of specified templates.

As a first step, we develop code to read a PDF document and from it create a new PDF document by changing specific words in the original document.

We rely mainly on the [PyMuPdf](https://github.com/pymupdf/PyMuPDF) [library](https://pymupdf.readthedocs.io/en/latest/index.html).

The code uses Python.

## Running the code
You need to create/enter a Python Virtual Environment.

### create:
(on Windows. On Linux it is similar.)

    cd c:/work/editPdf
    python -m venv .venv
    source ./.venv/Scripts/activate

### use an existing virtual env
(on Windows with git bash)

    cd /c/Users/Evyatar/work/editPdf
    source ./.venv/Scripts/activate

### creating a requirements file
     pip freeze > requirements.txt

### using a requirements file
    pip install -r requirements.txt

It looks like this:

    Evyatar@Evyatar MINGW64 ~/work/editPdf (master)
    $ pip install -r requirements.txt
    Collecting fonttools==4.43.1 (from -r requirements.txt (line 1))
    Using cached fonttools-4.43.1-cp311-cp311-win_amd64.whl (2.1 MB)
    Collecting PyMuPDF==1.23.5 (from -r requirements.txt (line 2))
    Using cached PyMuPDF-1.23.5-cp311-none-win_amd64.whl (3.5 MB)
    Collecting PyMuPDFb==1.23.5 (from -r requirements.txt (line 3))
    Using cached PyMuPDFb-1.23.5-py3-none-win_amd64.whl (24.4 MB)
    Installing collected packages: PyMuPDFb, fonttools, PyMuPDF
    Successfully installed PyMuPDF-1.23.5 PyMuPDFb-1.23.5 fonttools-4.43.1

    [notice] A new release of pip is available: 23.1.2 -> 23.3.1
    [notice] To update, run: python.exe -m pip install --upgrade pip
    (.venv)
    Evyatar@Evyatar MINGW64 ~/work/editPdf (master)
    $

After doing that, in the Python code you can use the libraries:
```python
    import sys
    import getopt
    import fitz
```
