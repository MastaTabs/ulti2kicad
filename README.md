So yes, a converter from DDF to KiCad PCB format it is.

I had a bunch of all old UltiBoard design files which I wanted to make easliy accessible for myself.
I had found the Eagle import ulp script which only really works for a fully licensed Eagle version.
This converter is losely based on that script but also largely on the format information that included
in the original UltiBoard manuals.

Since I never really got attached to Eagle but do all my pcb design work in KiCad these days the target
was set.

Right now only 4 layer boards are generated. I plan to make this configurable using the command line.

The code surely could be a bit neater. 
This was a good endeavour to dive a bit more into Python coding.

There are some small preparations for some better data structures.

Usage: ulti2kicad.py <infile> <outfile>
