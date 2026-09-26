import tkinter as tk
from pynput import keyboard, mouse
import pyperclip
import threading
import json
import os
import time

# ============================================================
# CONFIGURAÇÃO
# ============================================================

CONFIG_FILE = "config.json"
WORDS_FILE = "palavras.txt"

config = {
    "x": None,
    "y": None
}

# Carrega configuração salva
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    except Exception:
        pass


# ============================================================
# PALAVRAS
# ============================================================

def carregar_palavras():
    if not os.path.exists(WORDS_FILE):
        return []

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        palavras = [
            linha.strip().lower()
            for linha in f
            if linha.strip()
        ]

    # Remove duplicadas
    return list(dict.fromkeys(palavras))


palavras = carregar_palavras()


# ============================================================
# VARIÁVEIS
# ============================================================

texto = ""

gravando_posicao = False

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()


# ============================================================
# SALVAR CONFIGURAÇÃO
# ============================================================

def salvar_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Erro ao salvar configuração:", e)


# ============================================================
# JANELA
# ============================================================

root = tk.Tk()

root.title("KAKA Autocomplete")

root.geometry("420x500")

root.resizable(False, False)

root.attributes("-topmost", True)


# ============================================================
# TÍTULO
# ============================================================

titulo = tk.Label(
    root,
    text="KAKA AUTOCOMPLETE",
    font=("Arial", 18, "bold")
)

titulo.pack(pady=15)


status = tk.Label(
    root,
    text="Pronto.",
    font=("Arial", 10)
)

status.pack(pady=5)


# ============================================================
# LISTA DE SUGESTÕES
# ============================================================

lista = tk.Listbox(
    root,
    font=("Arial", 16),
    height=15
)

lista.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)


# ============================================================
# GRAVAR POSIÇÃO
# ============================================================

def gravar_posicao():

    global gravando_posicao

    gravando_posicao = True

    status.config(
        text="Clique no campo onde a palavra será colocada..."
    )

    def capturar(x, y, button, pressed):

        global gravando_posicao

        if pressed and gravando_posicao:

            config["x"] = x
            config["y"] = y

            salvar_config()

            gravando_posicao = False

            root.after(
                0,
                lambda: status.config(
                    text=f"Posição salva: {x}, {y}"
                )
            )

            return False

    listener = mouse.Listener(
        on_click=capturar
    )

    listener.start()


# ============================================================
# BOTÃO GRAVAR
# ============================================================

botao_gravar = tk.Button(
    root,
    text="🎯 GRAVAR POSIÇÃO",
    font=("Arial", 12, "bold"),
    command=gravar_posicao
)

botao_gravar.pack(
    fill="x",
    padx=20,
    pady=10
)


# ============================================================
# ATUALIZAR LISTA
# ============================================================

def atualizar_lista():

    lista.delete(
        0,
        tk.END
    )

    if not texto:
        return

    encontrados = []

    prefixo = texto.lower()

    for palavra in palavras:

        if palavra.startswith(prefixo):

            encontrados.append(palavra)

            if len(encontrados) >= 20:
                break

    for palavra in encontrados:

        lista.insert(
            tk.END,
            palavra
        )

    if encontrados:

        lista.selection_set(0)


# ============================================================
# LIMPAR
# ============================================================

def limpar():

    global texto

    texto = ""

    root.after(
        0,
        atualizar_lista
    )


# ============================================================
# ENVIAR PALAVRA
# ============================================================

def enviar_palavra(palavra):

    if config["x"] is None or config["y"] is None:

        root.after(
            0,
            lambda: status.config(
                text="Grave primeiro a posição!"
            )
        )

        return

    try:

        # Copia a palavra inteira
        pyperclip.copy(palavra)

        time.sleep(0.01)

        # Move o mouse para o campo
        mouse_controller.position = (
            config["x"],
            config["y"]
        )

        time.sleep(0.01)

        # Clique no campo
        mouse_controller.click(
            mouse.Button.left
        )

        time.sleep(0.01)

        # CTRL + V
        with keyboard_controller.pressed(
            keyboard.Key.ctrl
        ):
            keyboard_controller.press("v")

        time.sleep(0.01)

        # ENTER
        keyboard_controller.press(
            keyboard.Key.enter
        )

        root.after(
            0,
            lambda: status.config(
                text=f"Enviado: {palavra}"
            )
        )

    except Exception as e:

        print("Erro:", e)


# ============================================================
# SELECIONAR SUGESTÃO
# ============================================================

def selecionar(event=None):

    if lista.size() == 0:
        return

    selecao = lista.curselection()

    if not selecao:
        selecao = (0,)

    palavra = lista.get(
        selecao[0]
    )

    # Envia em outra thread para não travar a interface
    threading.Thread(
        target=enviar_palavra,
        args=(palavra,),
        daemon=True
    ).start()

    limpar()


lista.bind(
    "<ButtonRelease-1>",
    selecionar
)


# ============================================================
# TECLADO GLOBAL
# ============================================================

def tecla_pressionada(key):

    global texto

    try:

        # Letras e números
        if hasattr(key, "char") and key.char:

            caractere = key.char

            if caractere.isalpha() or caractere.isdigit():

                texto += caractere.lower()

                root.after(
                    0,
                    atualizar_lista
                )

                return

        # Backspace
        if key == keyboard.Key.backspace:

            if texto:

                texto = texto[:-1]

                root.after(
                    0,
                    atualizar_lista
                )

            return

        # Espaço
        if key == keyboard.Key.space:

            limpar()

            return

        # ESC
        if key == keyboard.Key.esc:

            limpar()

            return

    except Exception as e:

        print("Erro no teclado:", e)


# ============================================================
# INICIAR MONITORAMENTO GLOBAL
# ============================================================

keyboard_listener = keyboard.Listener(
    on_press=tecla_pressionada
)

keyboard_listener.start()


# ============================================================
# FECHAR
# ============================================================

def fechar():

    try:
        keyboard_listener.stop()
    except:
        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    fechar
)


# ============================================================
# INFORMAÇÕES
# ============================================================

if config["x"] is not None:

    status.config(
        text=f"Posição salva: {config['x']}, {config['y']}"
    )

else:

    status.config(
        text="Clique em GRAVAR POSIÇÃO para começar."
    )


# ============================================================
# INICIAR PROGRAMA
# ============================================================

root.mainloop()
