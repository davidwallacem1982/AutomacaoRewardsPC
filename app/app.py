import json
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk  # Pillow

from app.automation import executar_automacao
from app.items import gerar_lista_itens

ctk.set_appearance_mode("dark")


# ===== INICIANDO O ÍCONE =====
def resource_path(relative_path: str) -> Path:
    """Retorna o caminho correto para arquivos no PyInstaller ou modo normal"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # título da janela
        try:
            self.title("Automação Microsoft Rewards")
        except Exception:
            pass
        # estilos de botão consistentes
        btn_w = 150
        btn_h = 42
        btn_radius = 8
        stop_w = 460
        stop_h = 46
        stop_radius = 10
        # ===== INITIAL STATE =====
        # filas/eventos/threads usados pela UI
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.last_backup = None

        # variáveis usadas pelos controles (inicializações mínimas)
        # default para resolução: primeira resolução definida em app.config.RESOLUCOES
        try:
            from app.config import RESOLUCOES as _RESOLUCOES

            _default_res = next(iter(_RESOLUCOES.keys())) if _RESOLUCOES else ""
        except Exception:
            _default_res = ""
        self.resolucao = tk.StringVar(value=_default_res)
        self.verificar = tk.StringVar(value="5")
        self.browser = tk.StringVar(value="chrome")

        # ===== ÍCONE DA JANELA =====

        # prepara ícones para uso imediato (se arquivos existirem)
        try:
            self._prepare_button_icons()
        except Exception:
            self._icons = {}

        # frame de controles (placeholder se layout originalmente estiver em outra
        # parte do código)
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # botões básicos que algumas rotinas assumem existir
        self.btn_start = ctk.CTkButton(
            controls_frame,
            text="▶ Iniciar",
            command=self.iniciar,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("start"),
        )
        # inicialmente posicionamos o botão Iniciar mais abaixo para abrir espaço
        self.btn_start.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

        # Option menu para seleção de resolução (liga-se a `self.resolucao`)
        try:
            from app.config import RESOLUCOES as _RESOLUCOES

            _res_values = list(_RESOLUCOES.keys())
        except Exception:
            _res_values = [self.resolucao.get()] if self.resolucao.get() else []

        if _res_values:
            try:
                # label descritivo para o seletor de resolução
                lbl_res = ctk.CTkLabel(controls_frame, text="Resolução:")
                lbl_res.grid(row=0, column=0, padx=(6, 2), pady=6, sticky="w")

                self.opt_resolucao = ctk.CTkOptionMenu(
                    controls_frame,
                    values=_res_values,
                    command=lambda v: self.resolucao.set(v),
                )
                # set default visible value
                if self.resolucao.get() in _res_values:
                    self.opt_resolucao.set(self.resolucao.get())
                else:
                    self.opt_resolucao.set(_res_values[0])
                self.opt_resolucao.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
                # habilita/desabilita o botão Iniciar dependendo da seleção
                try:
                    if self.resolucao.get() and str(self.resolucao.get()).strip():
                        self.btn_start.configure(state="normal")
                    else:
                        self.btn_start.configure(state="disabled")
                except Exception:
                    pass

                # atualiza estado do botão ao alterar a variável
                def _on_res_change(*_args):
                    try:
                        if self.resolucao.get() and str(self.resolucao.get()).strip():
                            self.btn_start.configure(state="normal")
                        else:
                            self.btn_start.configure(state="disabled")
                    except Exception:
                        pass

                try:
                    # tkinter 8.6+: trace_add
                    self.resolucao.trace_add("write", _on_res_change)
                except Exception:
                    try:
                        # older tkinter: trace
                        self.resolucao.trace("w", _on_res_change)
                    except Exception:
                        pass
            except Exception:
                pass

        else:
            # se não houver resoluções configuradas, desabilita iniciar
            try:
                self.btn_start.configure(state="disabled")
            except Exception:
                pass
        self.btn_calibrate = ctk.CTkButton(
            controls_frame,
            text="🧭 Calibrar",
            command=self.abrir_calibracao,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("calibrate"),
        )
        self.btn_calibrate.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        icon_path = resource_path("app/assets/icon.ico")

        def set_window_icon():
            if icon_path.exists():
                """Carrega ícones PNG estáticos de `app/assets/` (padrão simples).

                Procura por `icon_<name>_48.png` e `icon_<name>_28.png`.
                """
                assets_dir = Path(__file__).parent / "assets"
                self._icons = {}
                names = [
                    "start",
                    "calibrate",
                    "auto",
                    "remove",
                    "export",
                    "import",
                    "undo",
                    "stop",
                ]
                for name in names:
                    p = assets_dir / f"icon_{name}_48.png"
                    size = 48
                    if not p.exists():
                        p = assets_dir / f"icon_{name}_28.png"
                        size = 28
                    try:
                        if p.exists():
                            loaded = Image.open(p).convert("RGBA")
                            try:
                                ctk_img = ctk.CTkImage(
                                    light_image=loaded, size=(size, size)
                                )
                                self._icons[name] = ctk_img
                            except Exception:
                                self._icons[name] = ImageTk.PhotoImage(loaded)
                        else:
                            self._icons[name] = None
                    except Exception:
                        self._icons[name] = None

                # update button images if buttons already exist
                try:
                    for btn_name in (
                        "btn_start",
                        "btn_calibrate",
                        "btn_auto_all",
                        "btn_remove_calib",
                        "btn_export",
                        "btn_import",
                        "btn_undo_remove",
                        "btn_stop",
                    ):
                        if hasattr(self, btn_name):
                            btn = getattr(self, btn_name)
                            key = btn_name.replace("btn_", "")
                            if key == "auto_all":
                                key = "auto"
                            if key == "remove_calib":
                                key = "remove"
                            if key == "undo_remove":
                                key = "undo"
                            icon = self._icons.get(key)
                            try:
                                btn.configure(image=icon)
                            except Exception:
                                pass
                except Exception:
                    pass

        self.btn_auto_all = ctk.CTkButton(
            controls_frame,
            text="Auto-gerar",
            command=self.auto_generate_all,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("auto"),
        )
        self.btn_auto_all.grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        # linha 2: remover / exportar
        self.btn_remove_calib = ctk.CTkButton(
            controls_frame,
            text="Remover",
            command=self.remove_calibration_current,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            fg_color="#f0ad4e",
            image=self._icons.get("remove"),
        )
        self.btn_remove_calib.grid(row=2, column=0, padx=6, pady=6, sticky="ew")

        self.btn_export = ctk.CTkButton(
            controls_frame,
            text="Exportar",
            command=self.export_calibrations,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("export"),
        )
        self.btn_export.grid(row=2, column=1, padx=6, pady=6, sticky="ew")

        # linha 3: importar / desfazer
        self.btn_import = ctk.CTkButton(
            controls_frame,
            text="Importar",
            command=self.import_calibrations,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("import"),
        )
        self.btn_import.grid(row=3, column=0, padx=6, pady=6, sticky="ew")

        self.btn_undo_remove = ctk.CTkButton(
            controls_frame,
            text="Desfazer",
            command=self.undo_last_removal,
            state="disabled",
            width=btn_w,
            height=btn_h,
            corner_radius=btn_radius,
            image=self._icons.get("undo"),
        )
        self.btn_undo_remove.grid(row=3, column=1, padx=6, pady=6, sticky="ew")

        # stop - destaque embaixo
        self.btn_stop = ctk.CTkButton(
            controls_frame,
            text="Parar",
            command=self.parar,
            state="disabled",
            width=stop_w,
            height=stop_h,
            corner_radius=stop_radius,
            fg_color="#d9534f",
            image=self._icons.get("stop"),
        )
        self.btn_stop.grid(row=4, column=0, columnspan=3, pady=(10, 0), padx=6, sticky="ew")

        self.log_box = ctk.CTkTextbox(self, width=400, height=260)
        # place log box using grid to avoid mixing pack/grid on the root
        self.log_box.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.log_box.configure(state="disabled")

        # allow log column/row to expand when window resizes
        try:
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)
        except Exception:
            pass

        # Loop de processamento de logs
        self.after(100, self.processar_logs)

    # ===== LOG THREAD-SAFE =====
    def log(self, msg: str):
        self.log_queue.put(msg)

    def processar_logs(self):
        try:
            while not self.log_queue.empty():
                msg = self.log_queue.get_nowait()
                self.log_box.configure(state="normal")
                self.log_box.insert("end", msg + "\n")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
        finally:
            self.after(100, self.processar_logs)

    # ===== CONTROLES =====
    def iniciar(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.log("⚠️ Automação já está em execução")
            return

        # validação: precisa existir resolução selecionada
        if not (self.resolucao.get() and str(self.resolucao.get()).strip()):
            messagebox.showwarning(
                "Resolução não selecionada",
                "Selecione uma resolução antes de iniciar a automação.",
            )
            self.log("❌ Nenhuma resolução selecionada")
            return

        try:
            verificar = max(1, int(self.verificar.get()))
        except ValueError:
            self.log("❌ Valor inválido para verificação")
            return

        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

        textos = gerar_lista_itens(500)
        # import get_runtime_config lazily to avoid circular import issues in frozen exe
        from app.config import get_runtime_config

        # obtém config em pixels, aplicando calibração percentual se disponível
        try:
            config = get_runtime_config(self.resolucao.get())
        except Exception as e:
            self.log(f"❌ Erro ao obter config: {e}")
            # restaura estado da UI
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            return
        browser = self.browser.get().lower()

        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(textos, config, verificar, browser),
            daemon=True,
        )
        self.worker_thread.start()

        self.log("🚀 Automação iniciada")

    def _worker(self, textos, config, verificar, browser):
        try:
            executar_automacao(
                textos=textos,
                config=config,
                verificar_a_cada=verificar,
                browser=browser,
                stop_event=self.stop_event,
                log_callback=self.log,
            )
        except Exception as e:
            self.log(f"❌ Erro inesperado: {e}")
        finally:
            self.log("🏁 Automação finalizada")
            self.after(0, self._reset_ui)

    def _reset_ui(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def parar(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.log("⏹ Solicitando parada...")
            self.stop_event.set()
            self.btn_stop.configure(state="disabled")
        else:
            self.log("ℹ️ Nenhuma automação em execução")

    def abrir_calibracao(self):
        # Abre janela de calibragem (não bloqueante)
        from app.calibration import Calibrator

        Calibrator(self, self.resolucao.get())

    def _prepare_button_icons(self):
        """Carrega ícones PNG estáticos de `app/assets/` (padrão simples).

        Procura por `icon_<name>_48.png` e `icon_<name>_28.png`.
        """
        assets_dir = Path(__file__).parent / "assets"
        self._icons = {}
        names = [
            "start",
            "calibrate",
            "auto",
            "remove",
            "export",
            "import",
            "undo",
            "stop",
        ]
        for name in names:
            p = assets_dir / f"icon_{name}_48.png"
            size = 48
            if not p.exists():
                p = assets_dir / f"icon_{name}_28.png"
                size = 28
            try:
                if p.exists():
                    loaded = Image.open(p).convert("RGBA")
                    try:
                        ctk_img = ctk.CTkImage(light_image=loaded, size=(size, size))
                        self._icons[name] = ctk_img
                    except Exception:
                        self._icons[name] = ImageTk.PhotoImage(loaded)
                else:
                    self._icons[name] = None
            except Exception:
                self._icons[name] = None

        # update button images if buttons already exist
        try:
            for btn_name in (
                "btn_start",
                "btn_calibrate",
                "btn_auto_all",
                "btn_remove_calib",
                "btn_export",
                "btn_import",
                "btn_undo_remove",
                "btn_stop",
            ):
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    key = btn_name.replace("btn_", "")
                    if key == "auto_all":
                        key = "auto"
                    if key == "remove_calib":
                        key = "remove"
                    if key == "undo_remove":
                        key = "undo"
                    icon = self._icons.get(key)
                    try:
                        btn.configure(image=icon)
                    except Exception:
                        pass
        except Exception:
            pass

    def _update_icon_preview(self, style: str):
        # preview removed in simplified UI
        return

    def auto_generate_all(self):
        try:
            from app.calibration import generate_all_from_resolucoes

            p = generate_all_from_resolucoes()
            try:
                size_kb = Path(p).stat().st_size / 1024
                self.log(f"🔧 Calibrações geradas em {p} ({size_kb:.1f} KB)")
            except Exception:
                self.log(f"🔧 Calibrações geradas em {p}")
        except Exception as e:
            self.log(f"❌ Erro ao gerar calibrações: {e}")

    def remove_calibration_current(self):
        try:
            from app.calibration import remove_calibration

            res_name = self.resolucao.get()
            if not messagebox.askyesno(
                "Confirmar remoção",
                f"Remover calibração para {res_name}? Esta ação não pode ser desfeita.",
            ):
                self.log("ℹ️ Remoção cancelada pelo usuário")
                return
            backup = remove_calibration(res_name)
            if backup:
                self.last_backup = str(backup)
                self.btn_undo_remove.configure(state="normal")
                try:
                    size_kb = Path(self.last_backup).stat().st_size / 1024
                    self.log(
                        f"🗑️ Calibração removida para {res_name} — backup em {backup} ({size_kb:.1f} KB)"
                    )
                except Exception:
                    self.log(
                        f"🗑️ Calibração removida para {res_name} — backup em {backup}"
                    )
            else:
                self.log(f"ℹ️ Nenhuma calibração encontrada para {res_name}")
        except Exception as e:
            self.log(f"❌ Erro ao remover calibração: {e}")

    def export_calibrations(self):
        try:
            from app.calibration import export_calibrations

            file = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                initialfile="calibration_backup.json",
            )
            if not file:
                return
            p = export_calibrations(file)
            try:
                size_kb = Path(p).stat().st_size / 1024
                self.log(f"💾 Calibrações exportadas para {p} ({size_kb:.1f} KB)")
            except Exception:
                self.log(f"💾 Calibrações exportadas para {p}")
        except Exception as e:
            self.log(f"❌ Erro exportando calibrações: {e}")

    def import_calibrations(self):
        try:
            from app.calibration import import_calibrations

            file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if not file:
                return

            # preview keys to check for conflicts
            try:
                new_data = json.loads(Path(file).read_text(encoding="utf-8"))
            except Exception:
                self.log(f"❌ Arquivo inválido: {file}")
                return

            new_keys = set(new_data.keys())
            calib_path = Path(__file__).parent / "calibration.json"
            existing_keys = set()
            if calib_path.exists():
                try:
                    existing_keys = set(
                        json.loads(calib_path.read_text(encoding="utf-8")).keys()
                    )
                except Exception:
                    existing_keys = set()

            overlap = new_keys & existing_keys
            if overlap:
                msg = f"O arquivo contém calibrações para: {', '.join(sorted(overlap))}.\nDeseja sobrescrever essas entradas?"
                if not messagebox.askyesno("Confirmar importação", msg):
                    self.log("ℹ️ Importação cancelada pelo usuário")
                    return

            ok = import_calibrations(file)
            if ok:
                self.log(f"✅ Calibrações importadas de {file}")
            else:
                self.log(f"❌ Falha ao importar calibrações de {file}")
        except Exception as e:
            self.log(f"❌ Erro importando calibrações: {e}")

    def undo_last_removal(self):
        if not getattr(self, "last_backup", None):
            self.log("ℹ️ Nenhum backup disponível")
            return
        try:
            from app.calibration import restore_backup

            if not messagebox.askyesno(
                "Confirmar restauração",
                f"Restaurar calibrações a partir de {self.last_backup}? Isso sobrescreverá o arquivo atual.",
            ):
                self.log("ℹ️ Restauração cancelada pelo usuário")
                return

            ok = restore_backup(self.last_backup)
            if ok:
                self.log("🔄 Restauração concluída")
                self.btn_undo_remove.configure(state="disabled")
                self.last_backup = None
            else:
                self.log("❌ Falha ao restaurar backup")
        except Exception as e:
            self.log(f"❌ Erro ao restaurar backup: {e}")


# if __name__ == "__main__":
#     app = App()
#     app.mainloop()
