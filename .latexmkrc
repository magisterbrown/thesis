$pdf_mode = 5;          # generate PDF via xelatex
$xelatex = 'xelatex -interaction=nonstopmode -synctex=1 %O %S';
$bibtex_use = 2;        # run bibtex/biber as needed
$clean_ext = 'synctex.gz synctex.gz(busy) run.xml tex.bak bbl bcf fdb_latexmk run tdo %R-blx.bib';
@default_files = ('main.tex');
$out_dir = 'build';
