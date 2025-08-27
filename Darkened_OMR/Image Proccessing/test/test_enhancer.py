import os
from src.enhancer import darken_corners

def test_output_pdf_created():
    input_pdf = "data/input.pdf"
    output_pdf = "data/output_test.pdf"
    darken_corners(input_pdf, output_pdf)
    assert os.path.exists(output_pdf)
