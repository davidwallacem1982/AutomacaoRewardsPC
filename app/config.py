# config.py
import json

RESOLUCOES = {
    "1280x1024": {
        "botao_microsoft_rewards": (111, 94),
        "detalhamentos_pontos": (934, 321),
        "abrir_pc_search": (531, 433),
        "barra_pesquisa": (193, 159),
        "aba_pesquisa": (380, 23),
        "aba_principal": (120, 20),
        "pc_search_region": (380, 300, 360, 210),
    },
    "1366x768": {
        "botao_microsoft_rewards": (220, 140),
        "detalhamentos_pontos": (180, 70),
        "abrir_pc_search": (934, 321),
        "barra_pesquisa": (720, 240),
        "aba_pesquisa": (410, 300),
        "aba_principal": (130, 15),
        "pc_search_region": (400, 220, 350, 170),
    },
    "1920x1080": {
        "botao_microsoft_rewards": (266, 156),
        "detalhamentos_pontos": (224, 89),
        "abrir_pc_search": (934, 321),
        "barra_pesquisa": (937, 328),
        "aba_pesquisa": (535, 391),
        "aba_principal": (155, 18),
        "pc_search_region": (480, 260, 420, 200),
    },
}

TEMPOS = {
    "curto": 1,
    "medio": 2,
    "alto": 3,
}

BROWSERS = {"Edge": "edge", "Chrome": "chrome", "Chromium": "chromium"}


# Validador simples para checar formato das resoluções
REQUIRED_CLICK_KEYS = [
    "botao_microsoft_rewards",
    "detalhamentos_pontos",
    "abrir_pc_search",
    "barra_pesquisa",
    "aba_pesquisa",
    "aba_principal",
]
REGION_KEY = "pc_search_region"


def _parse_resolucao_str(name: str):
    try:
        w, h = name.split("x")
        return int(w), int(h)
    except Exception:
        return None


def _apply_calibration_to_pixels(resolution_name: str, calibration: dict):
    """Converte entradas percentuais de calibragem para pixels usando a resolução.

    `calibration` deve ter as mesmas chaves de RESOLUCOES, porém valores em 0..1.
    Retorna dicionário com tuplas de pixels apropriadas.
    """
    base = RESOLUCOES.get(resolution_name)
    if base is None:
        raise KeyError(f"Resolução desconhecida: {resolution_name}")

    parsed = _parse_resolucao_str(resolution_name)
    if not parsed:
        raise ValueError(f"Nome de resolução inválido: {resolution_name}")
    width, height = parsed

    result = base.copy()

    for k, v in (calibration or {}).items():
        if k == REGION_KEY:
            # Expect region as (left_pct, top_pct, w_pct, h_pct)
            if isinstance(v, (list, tuple)) and len(v) == 4:
                left = int(v[0] * width)
                top = int(v[1] * height)
                w_px = int(v[2] * width)
                h_px = int(v[3] * height)
                result[k] = (left, top, w_px, h_px)
        else:
            # click coords expected as (x_pct, y_pct)
            if isinstance(v, (list, tuple)) and len(v) == 2:
                x = int(v[0] * width)
                y = int(v[1] * height)
                result[k] = (x, y)

    return result


def get_runtime_config(resolution_name: str, calibration_path: str = None):
    """Retorna um config pronto (pixels) para uso na automação.

    Se `calibration_path` existir, tenta carregar calibração percentual e aplicá-la.
    """
    from pathlib import Path

    base = RESOLUCOES.get(resolution_name)
    if base is None:
        raise KeyError(f"Resolução desconhecida: {resolution_name}")

    if calibration_path is None:
        calibration_path = Path(__file__).parent / "calibration.json"
    else:
        calibration_path = Path(calibration_path)

    if calibration_path.exists():
        try:
            data = json.loads(calibration_path.read_text(encoding="utf-8"))
            calib_for_res = data.get(resolution_name)
            if calib_for_res:
                return _apply_calibration_to_pixels(resolution_name, calib_for_res)
        except Exception:
            # se falhar ao ler calibração, retorna uma cópia do base sem alteração
            return base.copy()

    # sempre retornamos uma cópia do `base` para evitar que o chamador
    # modifique inadvertidamente o dicionário original em `RESOLUCOES`.
    return base.copy()


def validar_resolucoes(resolucoes):
    """Valida que cada resolução tem as chaves esperadas e formatos corretos.

    Retorna uma lista de strings com mensagens de erro (vazia se tudo OK).
    """
    erros = []
    for name, cfg in resolucoes.items():
        if not isinstance(cfg, dict):
            erros.append(f"{name}: configuração inválida (esperado dict)")
            continue

        for k in REQUIRED_CLICK_KEYS:
            if k not in cfg or not (isinstance(cfg[k], tuple) and len(cfg[k]) == 2):
                erros.append(f"{name}: chave ausente ou inválida '{k}'")

        rk = REGION_KEY
        if rk not in cfg or not (isinstance(cfg[rk], tuple) and len(cfg[rk]) == 4):
            erros.append(
                f"{name}: chave ausente ou inválida '{rk}' (esperado 4 valores)"
            )

    return erros


# Rodar validação em import para falhar rápido se algo estiver errado
_config_erros = validar_resolucoes(RESOLUCOES)
if _config_erros:
    raise RuntimeError(
        "Erros na configuração de RESOLUCOES:\n" + "\n".join(_config_erros)
    )
