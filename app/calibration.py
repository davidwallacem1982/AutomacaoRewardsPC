import json
import time
from pathlib import Path

import customtkinter as ctk
import pyautogui as ptg

from app.config import REGION_KEY, REQUIRED_CLICK_KEYS, RESOLUCOES

CALIB_PATH = Path(__file__).parent / "calibration.json"


class Calibrator(ctk.CTkToplevel):
    def __init__(self, master, resolution_name: str):
        super().__init__(master)
        self.title("Calibragem de Coordenadas")
        self.resolution_name = resolution_name
        self.posicoes = {}
        self.region_points = []

        self.label = ctk.CTkLabel(
            self,
            text=(
                "Siga as instruções e clique em 'Capturar' para cada item. "
                "Para evitar mover o mouse ao clicar no botão, posicione o mouse no alvo "
                "e pressione Enter (tecla) para capturar sem usar o mouse)."
            ),
        )
        self.label.pack(pady=8)

        self.listbox = ctk.CTkTextbox(self, width=420, height=200)
        self.listbox.pack(pady=8)
        self.listbox.configure(state="disabled")

        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=6)

        self.btn_capture = ctk.CTkButton(
            self.btn_frame, text="Capturar próximo", command=self.capture_next
        )
        self.btn_capture.grid(row=0, column=0, padx=6)

        self.btn_save = ctk.CTkButton(
            self.btn_frame,
            text="Salvar calibração",
            command=self.save,
            state="disabled",
        )
        self.btn_save.grid(row=0, column=1, padx=6)

        self.btn_cancel = ctk.CTkButton(
            self.btn_frame, text="Cancelar", command=self.destroy
        )
        self.btn_cancel.grid(row=0, column=2, padx=6)

        self.btn_auto = ctk.CTkButton(
            self.btn_frame, text="Auto-gerar", command=self.auto_generate
        )
        self.btn_auto.grid(row=0, column=3, padx=6)

        self._capture_order = REQUIRED_CLICK_KEYS + [REGION_KEY]
        self._current_index = 0
        # tenta registrar um listener global de teclado para a tecla Enter
        # se `pynput` estiver disponível; caso contrário, o usuário pode
        # focar a janela e pressionar Enter para capturar.
        try:
            from pynput import keyboard as _keyboard

            def _on_press(key):
                try:
                    if key == _keyboard.Key.enter:
                        # agendar chamada na thread do Tkinter
                        self.after(0, self.capture_next)
                except Exception:
                    pass

            self._keyboard_listener = _keyboard.Listener(on_press=_on_press)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
            self._hotkey_available = True
        except Exception:
            self._keyboard_listener = None
            self._hotkey_available = False

        self._show_next_instruction()

    def _append_log(self, text: str):
        self.listbox.configure(state="normal")
        self.listbox.insert("end", text + "\n")
        self.listbox.see("end")
        self.listbox.configure(state="disabled")

    def _show_next_instruction(self):
        if self._current_index >= len(self._capture_order):
            self._append_log(
                "Todas as posições capturadas. Clique em 'Salvar calibração'."
            )
            self.btn_capture.configure(state="disabled")
            self.btn_save.configure(state="normal")
            return

        key = self._capture_order[self._current_index]
        if key == REGION_KEY:
            self._append_log(
                "Agora capture a região do PC Search: primeiro posicione o mouse no canto superior esquerdo da região e clique 'Capturar próximo', depois posicione no canto inferior direito e clique novamente."
            )
        else:
            self._append_log(
                f"Posicione o mouse sobre: {key} e clique 'Capturar próximo'."
            )

    def capture_next(self):
        # pega posição atual do mouse
        pos = ptg.position()
        key = self._capture_order[self._current_index]

        if key == REGION_KEY:
            self.region_points.append((pos.x, pos.y))
            self._append_log(f"Ponto da região capturado: {pos}")
            if len(self.region_points) == 2:
                left = min(self.region_points[0][0], self.region_points[1][0])
                top = min(self.region_points[0][1], self.region_points[1][1])
                w = abs(self.region_points[1][0] - self.region_points[0][0])
                h = abs(self.region_points[1][1] - self.region_points[0][1])
                self.posicoes[REGION_KEY] = (left, top, w, h)
                self._current_index += 1
        else:
            self.posicoes[key] = (pos.x, pos.y)
            self._append_log(f"Posição capturada para {key}: {pos}")
            self._current_index += 1

        self._show_next_instruction()

    def save(self):
        # Convert captured absolute positions to percentual baseado na resolução string
        res = self.resolution_name
        try:
            w, h = map(int, res.split("x"))
        except Exception:
            w, h = ptg.size()

        calib = {}
        for k, v in self.posicoes.items():
            if k == REGION_KEY:
                left, top, ww, hh = v
                calib[k] = [left / w, top / h, ww / w, hh / h]
            else:
                x, y = v
                calib[k] = [x / w, y / h]

        data = {}
        if CALIB_PATH.exists():
            try:
                data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        data[self.resolution_name] = calib
        CALIB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._append_log(f"Calibração salva em: {CALIB_PATH}")
        self.btn_save.configure(state="disabled")

    def destroy(self):
        # stop keyboard listener if running
        try:
            if getattr(self, "_keyboard_listener", None):
                try:
                    self._keyboard_listener.stop()
                except Exception:
                    pass
        finally:
            try:
                super().destroy()
            except Exception:
                # fallback: just call base destroy without raising
                ctk.CTkToplevel.destroy(self)

    def auto_generate(self):
        """Gera calibração percentual a partir dos valores em `RESOLUCOES` e salva diretamente."""
        try:
            base = RESOLUCOES.get(self.resolution_name)
            if not base:
                self._append_log(
                    f"Resolução não encontrada em RESOLUCOES: {self.resolution_name}"
                )
                return

            try:
                w, h = map(int, self.resolution_name.split("x"))
            except Exception:
                w, h = ptg.size()

            calib = {}
            for k, v in base.items():
                if k == REGION_KEY:
                    left, top, ww, hh = v
                    calib[k] = [left / w, top / h, ww / w, hh / h]
                else:
                    x, y = v
                    calib[k] = [x / w, y / h]

            data = {}
            if CALIB_PATH.exists():
                try:
                    data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
                except Exception:
                    data = {}

            data[self.resolution_name] = calib
            CALIB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._append_log(f"Calibração automática gerada e salva em: {CALIB_PATH}")
            self.btn_save.configure(state="disabled")
        except Exception as e:
            self._append_log(f"Erro ao gerar calibração automática: {e}")


def generate_all_from_resolucoes(path: str | None = None):
    """Gera calibração percentual para todas as resoluções definidas em RESOLUCOES.

    Retorna o caminho do arquivo salvo.
    """
    backups_dir = Path(__file__).parent / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    p = (
        Path(path)
        if path
        else backups_dir / f"calibration_backup_{int(time.time())}.json"
    )
    data = {}
    for res_name, base in RESOLUCOES.items():
        try:
            w, h = map(int, res_name.split("x"))
        except Exception:
            w, h = ptg.size()

        calib = {}
        for k, v in base.items():
            if k == REGION_KEY:
                left, top, ww, hh = v
                calib[k] = [left / w, top / h, ww / w, hh / h]
            else:
                x, y = v
                calib[k] = [x / w, y / h]

        data[res_name] = calib

    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def remove_calibration(resolution_name: str, path: str | None = None) -> Path | None:
    """Remove calibração para `resolution_name` do arquivo de calibração.

    Antes de remover, cria um backup com `export_calibrations()` e retorna o Path do backup.
    Retorna None se nada foi removido ou em caso de erro.
    """
    p = Path(path) if path else CALIB_PATH
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

    if resolution_name in data:
        # cria backup completo antes de alterar
        try:
            backup = export_calibrations()
        except Exception:
            backup = None

        del data[resolution_name]
        try:
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            return None

        return backup
    return None


def restore_backup(backup_path: str) -> bool:
    """Restaura o arquivo principal de calibração a partir de `backup_path`.

    Retorna True se sucesso.
    """
    bp = Path(backup_path)
    if not bp.exists():
        return False
    try:
        content = bp.read_text(encoding="utf-8")
        # valida JSON
        json.loads(content)
        CALIB_PATH.write_text(content, encoding="utf-8")
    except Exception:
        return False
    return True


def export_calibrations(dest_path: str | None = None) -> Path:
    """Exporta o conteúdo de `calibration.json` para `dest_path` (ou gera um backup).

    Retorna o Path do arquivo salvo.
    """
    backups_dir = Path(__file__).parent / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    p = (
        Path(dest_path)
        if dest_path
        else backups_dir / f"calibration_backup_{int(time.time())}.json"
    )
    data = {}
    if CALIB_PATH.exists():
        try:
            data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def import_calibrations(src_path: str) -> bool:
    """Importa calibrações de `src_path`, mesclando (sobrescreve por chave) no arquivo padrão.

    Retorna True se importação bem-sucedida.
    """
    p = Path(src_path)
    if not p.exists():
        return False
    try:
        new = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False

    existing = {}
    if CALIB_PATH.exists():
        try:
            existing = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    # mescla (novas chaves ou sobrescritas)
    existing.update(new)
    try:
        CALIB_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        return False
    return True


if __name__ == "__main__":
    # debug
    root = ctk.CTk()
    c = Calibrator(root, "1280x1024")
    root.mainloop()
