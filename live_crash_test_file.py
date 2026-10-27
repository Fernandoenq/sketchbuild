from core.su_api import SketchUpAPI

print("iniciando...", flush=True)
api = SketchUpAPI()
with api:
    print("SUInitialize ok, versao:", api.get_api_version(), flush=True)
    print("chamando open_model (via arquivo)...", flush=True)
    with api.open_model(r"C:\Users\Fernando\Desktop\CatalogoRevenda\Moto mola.skp") as modelo:
        print("abriu! resumo:", modelo.count_summary(), flush=True)
print("fim", flush=True)
