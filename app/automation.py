import os
import random
import re
import time

import pyautogui as ptg
import pygetwindow as gw
import pyperclip
import pytesseract

# ==============================
# CONFIGURAÇÃO DO TESSERACT
# ==============================
TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ==============================
# UTILIDADES
# ==============================
def log_safe(log_callback, mensagem):
    if log_callback:
        log_callback(mensagem)
    else:
        print(mensagem)


def sleep_seguro(segundos, stop_event, step=0.2):
    elapsed = 0
    while elapsed < segundos:
        if stop_event.is_set():
            return False
        time.sleep(step)
        elapsed += step
    return True


# ==============================
# CONTROLE DE JANELAS
# ==============================
def maximizar_se_precisar(titulo_contem=None, stop_event=None):
    if stop_event and stop_event.is_set():
        return

    time.sleep(1)

    for janela in gw.getAllWindows():
        if titulo_contem and titulo_contem.lower() not in janela.title.lower():
            continue

        if janela.isMaximized:
            return

        janela.activate()
        time.sleep(0.2)
        ptg.hotkey("win", "up")
        return


# ==============================
# FINALIZAÇÃO
# ==============================
def fechar_browser(log_callback=None):
    log_safe(log_callback, "❌ Fechando navegador")
    ptg.hotkey("ctrl", "w")
    time.sleep(0.5)
    ptg.hotkey("ctrl", "w")


# ==============================
# NAVEGAÇÃO
# ==============================
def abrir_edge_detalhamentos_pontos(
    config, browser_path, stop_event=None, log_callback=None
):
    log_safe(log_callback, "🌐 Abrindo navegador")

    ptg.press("winleft")
    if not sleep_seguro(1, stop_event):
        return

    ptg.write(browser_path)
    ptg.press("enter")

    if not sleep_seguro(2, stop_event):
        return

    maximizar_se_precisar(browser_path, stop_event)

    for passo, nome in [
        ("botao_microsoft_rewards", "Botão Rewards"),
        ("detalhamentos_pontos", "Detalhamento de pontos"),
        ("abrir_pc_search", "Abrir PC Search"),
        ("barra_pesquisa", "Barra de pesquisa"),
    ]:
        if stop_event.is_set():
            return

        if passo not in config:
            log_safe(log_callback, f"⚠️ Coordenada ausente: {passo}")
            return

        log_safe(log_callback, f"🖱️ Clicando em {nome}")

        # fazer essa logica de outra forma
        # if passo == "abrir_pc_search":
        #     pc_search_completo(config["pc_search_region"], log_callback)
        #     stop_event
        ptg.click(*config[passo])

        if not sleep_seguro(2, stop_event):
            return


# ==============================
# OCR
# ==============================
def pc_search_completo(region, log_callback=None):
    log_safe(log_callback, "📸 Capturando área do PC Search")

    screenshot = ptg.screenshot(region=region)

    try:
        texto = pytesseract.image_to_string(
            screenshot,
            lang="eng",
            config="--psm 6 -c tessedit_char_whitelist=0123456789/",
        )
    except Exception as e:
        log_safe(log_callback, f"❌ Erro no OCR: {e}")
        return False

    texto_limpo = texto.strip().replace("\n", " ")
    log_safe(log_callback, f"🔍 OCR detectado: {texto_limpo}")

    match = re.search(r"(\d+)\s*/\s*(\d+)", texto_limpo)
    if not match:
        return False

    atual = int(match.group(1))
    maximo = int(match.group(2))

    log_safe(log_callback, f"📊 Progresso: {atual}/{maximo}")

    # Fazer de outra forma
    # if maximo != 90:
    #     log_safe(
    #         log_callback,
    #         f"⚠️ Valor máximo inesperado detectado: {maximo}, necessário atualização do sistema, entre en contado com o suporte.",
    #     )
    #     fechar_browser(log_callback)

    if atual == 90:
        return True
    return False


# ==============================
# FLUXO PRINCIPAL
# ==============================
def digitar_textos(textos, config, verificar_a_cada, stop_event, log_callback=None):
    total = len(textos)

    for index, texto in enumerate(textos, start=1):
        if stop_event.is_set():
            log_safe(log_callback, "🛑 Automação interrompida pelo usuário")
            return

        log_safe(log_callback, f"⌨️ Digitando ({index}/{total}): {texto}")

        ptg.click(*config["barra_pesquisa"])
        if not sleep_seguro(1.5, stop_event):
            return

        ptg.hotkey("ctrl", "a")
        ptg.press("backspace")

        pyperclip.copy(texto)
        ptg.hotkey("ctrl", "v")
        time.sleep(0.3)
        ptg.press("enter")

        if not sleep_seguro(random.uniform(2, 3), stop_event):
            return

        if index % verificar_a_cada == 0:
            log_safe(log_callback, "🧠 Verificando status do PC Search")

            ptg.click(*config["aba_principal"])
            if not sleep_seguro(2, stop_event):
                return

            if pc_search_completo(config["pc_search_region"], log_callback):
                sleep_seguro(1, stop_event)
                if pc_search_completo(config["pc_search_region"], log_callback):
                    log_safe(
                        log_callback,
                        "✅ PC Search atingiu 90/90. Encerrando automação!",
                    )
                    return

            log_safe(log_callback, "⏳ PC Search ainda não completou")
            ptg.click(*config["aba_pesquisa"])

            if not sleep_seguro(1, stop_event):
                return


# ==============================
# ORQUESTRAÇÃO
# ==============================
def executar_automacao(
    textos, config, verificar_a_cada, browser, stop_event, log_callback=None
):
    try:
        abrir_edge_detalhamentos_pontos(
            config=config,
            browser_path=browser,
            stop_event=stop_event,
            log_callback=log_callback,
        )

        if stop_event.is_set():
            return

        digitar_textos(
            textos=textos,
            config=config,
            verificar_a_cada=verificar_a_cada,
            stop_event=stop_event,
            log_callback=log_callback,
        )

    finally:
        fechar_browser(log_callback)
