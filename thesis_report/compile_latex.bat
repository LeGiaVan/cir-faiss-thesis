@echo off
echo Compiling LaTeX...
pdflatex -interaction=nonstopmode main.tex
if %errorlevel% neq 0 (
    echo pdflatex failed during the first run.
    pause
    exit /b %errorlevel%
)

echo Running BibTeX...
bibtex main
if %errorlevel% neq 0 (
    echo bibtex failed.
    pause
    exit /b %errorlevel%
)

echo Running pdflatex again (1/2)...
pdflatex -interaction=nonstopmode main.tex

echo Running pdflatex again (2/2)...
pdflatex -interaction=nonstopmode main.tex

echo LaTeX compilation finished. Opening PDF...
start main.pdf
