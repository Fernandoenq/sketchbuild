"""B4: gera 10 .skp pelo núcleo + gravador e um JSON com as contagens esperadas.

Uso (Python 3.12):  py -3.12 -I -c "import sys; sys.path.insert(0, '.'); from tools.gerar_amostras_b4 import main; main()" [PASTA]
Depois, no SketchUp: Window > Ruby Console e
  load 'C:/Users/Fernando/sketchup_companion/ruby_bridge/conferir_gerados.rb'
"""
import json
import os
import sys

from core.skp_topology_writer import gravar_topologia
from core.topology import Topology
from core.topology.draw import desenhar
from core.topology.pushpull import empurrar


def _cubo(t, x=0, y=0, l=100, h=50):
    desenhar(t, "retangulo", p0=(x, y, 0), p1=(x + l, y + l, 0))
    empurrar(t, max(t.faces), -h)


def amostras():
    out = {}
    t = Topology(); desenhar(t, "linha", pontos=[(0, 0, 0), (100, 0, 0)]); out["01_linha_solta"] = t
    t = Topology(); desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)); out["02_retangulo"] = t
    t = Topology(); _cubo(t); out["03_cubo"] = t
    t = Topology(); desenhar(t, "circulo", centro=(0, 0, 0), raio=50); out["04_circulo"] = t
    t = Topology(); desenhar(t, "poligono", centro=(0, 0, 0), raio=40, lados=6); out["05_hexagono"] = t
    t = Topology()
    desenhar(t, "retangulo", p0=(0, 0, 0), p1=(200, 200, 0)); desenhar(t, "retangulo", p0=(50, 50, 0), p1=(150, 150, 0))
    out["06_face_com_furo"] = t
    t = Topology(); _cubo(t)
    desenhar(t, "retangulo", p0=(30, 30, 50), p1=(70, 70, 50))
    empurrar(t, min(t.faces, key=lambda i: t.face_area(i)), -50)
    out["07_furo_vazado"] = t
    t = Topology(); _cubo(t); _cubo(t, 300, 0, 80, 120); out["08_dois_cubos"] = t
    t = Topology(); desenhar(t, "circulo", centro=(0, 0, 0), raio=50); empurrar(t, 1, -100); out["09_cilindro"] = t
    t = Topology(); _cubo(t); empurrar(t, next(i for i, f in t.faces.items() if f.normal[2] > 0.9), 40); out["10_cubo_esticado"] = t
    return out


def main(pasta=None):
    pasta = pasta or (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados"))
    os.makedirs(pasta, exist_ok=True)
    esperado = {}
    for nome, t in amostras().items():
        gravar_topologia(t, os.path.join(pasta, nome + ".skp"))
        c = t.counts()
        esperado[nome + ".skp"] = {"faces": c["faces"], "edges": c["edges"],
                                   "area_total": round(sum(t.face_area(f) for f in t.faces), 3)}
    with open(os.path.join(pasta, "esperado.json"), "w", encoding="utf-8") as fh:
        json.dump(esperado, fh, indent=1)
    print("gerados %d arquivos em %s" % (len(esperado), pasta))
