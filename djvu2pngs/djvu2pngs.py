#This file is based on examples provided by python-djvulibre

from __future__ import print_function
from tqdm.notebook import tqdm

import argparse
import os
import sys

import cairo
import djvu.decode
import numpy

cairo_pixel_format = cairo.FORMAT_ARGB32
djvu_pixel_format = djvu.decode.PixelFormatRgbMask(0xFF0000, 0xFF00, 0xFF, bpp=32)
djvu_pixel_format.rows_top_to_bottom = 1
djvu_pixel_format.y_top_to_bottom = 0

class Context(djvu.decode.Context):

    def handle_message(self, message):
        if isinstance(message, djvu.decode.ErrorMessage):
            print(message, file=sys.stderr)
            # Exceptions in handle_message() are ignored, so sys.exit()
            # wouldn't work here.
            os._exit(1)

    def process(self, djvu_path, png_path, mode, pages=[]):
        document = self.new_document(djvu.decode.FileURI(djvu_path))
        for i, page in tqdm(enumerate(document.pages)):
            page.get_info(wait=1)
            if i not in pages and pages != []:
                continue
            page_job = page.decode(wait=True)
            width, height = page_job.size
            rect = (0, 0, width, height)
            bytes_per_line = cairo.ImageSurface.format_stride_for_width(cairo_pixel_format, width)
            assert bytes_per_line % 4 == 0
            color_buffer = numpy.zeros((height, bytes_per_line // 4), dtype=numpy.uint32)
            page_job.render(mode, rect, rect, djvu_pixel_format, row_alignment=bytes_per_line, buffer=color_buffer)
            mask_buffer = numpy.zeros((height, bytes_per_line // 4), dtype=numpy.uint32)
            if mode == djvu.decode.RENDER_FOREGROUND:
                page_job.render(djvu.decode.RENDER_MASK_ONLY, rect, rect, djvu_pixel_format, row_alignment=bytes_per_line, buffer=mask_buffer)
                mask_buffer <<= 24
                color_buffer |= mask_buffer
            color_buffer ^= 0xFF000000
            surface = cairo.ImageSurface.create_for_data(color_buffer, cairo_pixel_format, width, height)
            surface.write_to_png(png_path + str(i) + ".png")

def book2pngs(djvu_path, png_path, pages=[]):
    mode=djvu.decode.RENDER_COLOR
    context = Context()
    context.process(djvu_path, png_path, mode, pages)
