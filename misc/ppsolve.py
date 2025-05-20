import os
import sys
# needed so that python can find our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  

from chiprag_modules import ( 
    load_pesticide_chapters, 
    load_pesticide_names_from_outline, 
    chunk_report_by_sections
    )


def main():
    test_pagestuff()    
    print("the end")


def test_pagestuff():
    test_pdf = "Pestizide_ohne_Pretext.pdf"
    # MIT PDF-VIEWER ZAHLEN ARBEITEN; NICHT MIT INDIZES
    start = 1
    ende  = 100
    text = load_pesticide_chapters(test_pdf, start, ende)
    with open("Output.txt", 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == "__main__":
    main()


## FRAGEN DIE ES ZU KLÄREN GILT
# Sections
"""
> Seitenzahlen, inklusiv oder exklusiv?
- Start 0, Ende 2 = Start ist exklusiv, beginnt mit der ersten Seite des Dokuments
- Start 1, Ende 2 = Start ist exklusiv, gibt gar nichts aus, PDF-Viewer Seite 1 nicht dabei
- Start 0, Ende 2 = Ende ist inklusiv, PDF-Viewer Seite 2 ist zu sehen, ab danach nichts mehr
- Start 1, Ende 2 = Ende ist, gibt gar nichts aus, PDF-Viewer Seite 1 und 2 beide nicht zu sehen
- Start 0, Ende 1 = Start ist exklusiv (oder eher index) PDF-Viewer Seite 1 ist zu sehen, Ende ist
                    ist inklusiv (oder eher index) PDF-Viewer Seite 1 ist zu sehen
- Start 1, Ende 2 = Start ist leer, Ende ist leer 
- Was ist die letzte Seite? laut PDF Viewer 4, laut Code
> Content
- Was ist wenn die erste Seite direkt mit Tabelle anfängt
- Was ist wenn die erste Seite mit Text vorher anfängt
(Ende nicht wirklich testbar, da nach letzer relevanter Tabelle entweder Extraneous oder Seitenumbruch)
"""
# Überschriften
"""
> Seitenzahlen, inklusiv oder exklusiv?
- Start 0, Ende 2 = Start ist
- Start 1, Ende 2 = Start ist
- Start 0, Ende 2 = Ende ist
- Start 1, Ende 2 = Ende ist
- Start 0, Ende 1 = Start ist , Ende ist
- Start 1, Ende 2 = Start ist , Ende ist
- Was ist die letzte Seite? laut PDF Viewer 4, laut Code
> Content
- Was ist wenn die erste Seite direkt mit Tabelle anfängt
- Was ist wenn die erste Seite mit Text vorher anfängt
(Ende nicht wirklich testbar, da nach letzer relevanter Tabelle entweder Extraneous oder Seitenumbruch)
"""