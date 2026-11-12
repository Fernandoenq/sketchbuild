"""B4: gera 16 .skp pelo núcleo + gravador (10 de geometria; 6 de curva, material e hierarquia) e um JSON com o esperado.

Uso (Python 3.12):  py -3.12 -I -c "import sys; sys.path.insert(0, '.'); from tools.gerar_amostras_b4 import main; main()" [PASTA]
Depois, no SketchUp: Window > Ruby Console e
  load 'C:/Users/Fernando/sketchup_companion/ruby_bridge/conferir_gerados.rb'
"""
import json
import os
import sys

from core.skp_topology_writer import _curvas_validas, gravar_cena, gravar_topologia
from core.topology.cena import Cena
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
    # curvas, material e hierarquia (11 a 16): o valor esperado inclui o que o SketchUp deve enxergar além da geometria
    t = Topology(); desenhar(t, "arco", centro=(0, 0, 0), raio=30, ang_ini=0, ang_fim=90, lados=8); out["11_arco_curva"] = t
    t = Topology()
    desenhar(t, "mao_livre", pontos=[(0, 0, 0), (100, 0, 0), (150, 80, 0), (100, 160, 30)], fechar=False)
    out["12_mao_livre_curva"] = t
    t = Topology(); desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    t.materiais = {"Vermelho": {"rgb": (255, 0, 0)}, "Verde": {"rgb": (0, 200, 0)}}
    f = next(iter(t.faces.values())); f.frente, f.verso = "Vermelho", "Verde"
    out["13_material_frente_verso"] = t
    c = Cena(); desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)); c.criar_grupo(faces=list(c.topo.faces), nome="G1")
    out["14_grupo"] = c
    c = Cena()
    desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    k = c.criar_componente(faces=list(c.topo.faces), nome="Peca")
    c.instanciar(k, [0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 300, 0, 0, 1])
    c.instanciar(k, [2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 4, 0, 0, 500, 0, 1])
    out["15_componente_3x"] = c
    c = Cena(); desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    ext = c.criar_grupo(faces=list(c.topo.faces), nome="Externo")
    c.entrar(ext); desenhar(c.topo, "retangulo", p0=(200, 0, 0), p1=(300, 100, 0))
    c.criar_grupo(faces=[max(c.topo.faces)], nome="Interno"); c.sair()
    out["16_grupo_aninhado"] = c
    return out


def _esperado(obj):
    t = obj.defs[0] if isinstance(obj, Cena) else obj
    c = t.counts()
    e = {"faces": c["faces"], "edges": c["edges"], "area_total": round(sum(t.face_area(f) for f in t.faces), 3)}
    if isinstance(obj, Cena):
        e["grupos"] = sum(1 for i in obj.instancias.values() if i.pai == 0 and i.tipo == "grupo")
        e["componentes"] = sum(1 for i in obj.instancias.values() if i.pai == 0 and i.tipo == "componente")
    e["curvas"] = len(_curvas_validas(t))
    usadas = [(f.frente, f.verso) for f in t.faces.values() if f.frente or f.verso]
    if usadas:
        e["cor_frente"] = list(t.materiais[usadas[0][0]]["rgb"]) if usadas[0][0] else None
        e["cor_verso"] = list(t.materiais[usadas[0][1]]["rgb"]) if usadas[0][1] else None
    return e


def main(pasta=None):
    pasta = pasta or (sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados"))
    os.makedirs(pasta, exist_ok=True)
    esperado = {}
    for nome, t in amostras().items():
        destino = os.path.join(pasta, nome + ".skp")
        (gravar_cena if isinstance(t, Cena) else gravar_topologia)(t, destino)
        esperado[nome + ".skp"] = _esperado(t)
    with open(os.path.join(pasta, "esperado.json"), "w", encoding="utf-8") as fh:
        json.dump(esperado, fh, indent=1)
    print("gerados %d arquivos em %s" % (len(esperado), pasta))
