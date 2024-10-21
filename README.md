So yes, a converter from DDF to KiCad PCB format it is.

I had a bunch of all old UltiBoard design files which I wanted to make easliy accessible for myself.
I had found the Eagle import ulp script which only really works for a fully licensed Eagle version.
This converter is losely based on that script but also largely on the format information that included
in the original UltiBoard manuals.

Since I never really got attached to Eagle but do all my pcb design work in KiCad these days the target
was set.

Right now only 4 layer boards are generated. I plan to make this configurable using the command line.

I have added kind of a bit of handling for Pad Stacks. KiCad's support is relatively new and not
fully grown yet. So if you have a trough hole pad with a smaller top layer pad than the bottom one,
the converter will add an additional SMD pad on the bottom layer to care for that.
This should pass the DRC.

The code surely could be a bit neater. 
This was a good endeavour to dive a bit more into Python coding.

There are some small preparations for some better data structures.

Text sizes and placement could be better.

This was only tested with version 4.80 files. Thats all I have.


usage: ulti2kicad.py \[-h\] \[-f FONT\] \[-ts\] infile outfile

Convert PCB board files in UltiBoard 4.x format to KiCad pcb format.

positional arguments:
  infile                input file
  outfile               output file

options:
  -h, --help            show this help message and exit
  -f FONT, --font FONT  use a different font, mono spaced fonts work best
  -ts, --textsilk       put freestanding silk text unto the front silk layer instead of the reference layer