import tkinter as tk
from pynput import mouse, keyboard
import pyperclip
import threading
import json
import os
import sys
import time


# ============================================================
# ARQUIVOS
# ============================================================

def caminho_recurso(nome):
    """
    Funciona tanto rodando o .py quanto o .exe criado pelo PyInstaller.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base, nome)


def caminho_config():
    """
    Salva a configuração ao lado do EXE.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(
            os.path.dirname(sys.executable),
            "config.json"
        )

    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config.json"
    )


WORDS_FILE = caminho_recurso("palavras.txt")
CONFIG_FILE = caminho_config()


# ============================================================
# CONFIGURAÇÃO
# ============================================================

config = {
    "x": None,
    "y": None
}


if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    except Exception:
        pass


# ============================================================
# CARREGAR PALAVRAS
# ============================================================

def carregar_palavras():

    if not os.path.exists(WORDS_FILE):
        return []

    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:

            palavras = []

            for linha in f:
                palavra = linha.strip()

                if palavra:
                    palavras.append(palavra)

            # Remove duplicadas mantendo a ordem
            palavras = list(dict.fromkeys(palavras))

            return palavras

    except Exception as e:
        print("Erro carregando palavras:", e)
        return []


palavras = carregar_palavras()


# ============================================================
# CONTROLES
# ============================================================

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

gravando_posicao = False


# ============================================================
# JANELA
# ============================================================

root = tk.Tk()

root.title("KAKA AUTOCOMPLETE")
root.geometry("430x560")
root.resizable(False, False)
root.attributes("-topmost", True)


# ============================================================
# TÍTULO
# ============================================================

titulo = tk.Label(
    root,
    text="KAKA AUTOCOMPLETE",
    font=("Arial", 20, "bold")
)

titulo.pack(pady=(15, 5))


# ============================================================
# STATUS
# ============================================================

status = tk.Label(
    root,
    text="Pronto.",
    font=("Arial", 10)
)

status.pack(pady=3)


# ============================================================
# BOTÃO GRAVAR POSIÇÃO
# ============================================================

def gravar_posicao():

    global gravando_posicao

    if gravando_posicao:
        return

    gravando_posicao = True

    status.config(
        text="AGORA CLIQUE NO CAMPO DE ENVIO..."
    )

    def capturar(x, y, button, pressed):

        global gravando_posicao

        if pressed and gravando_posicao:

            config["x"] = x
            config["y"] = y

            try:
                with open(
                    CONFIG_FILE,
                    "w",
                    encoding="utf-8"
                ) as f:

                    json.dump(
                        config,
                        f,
                        indent=4
                    )

            except Exception as e:
                print("Erro salvando posição:", e)

            gravando_posicao = False

            root.after(
                0,
                lambda: status.config(
                    text=f"Posição salva! X={x} Y={y}"
                )
            )

            return False

    listener = mouse.Listener(
        on_click=capturar
    )

    listener.start()


botao_gravar = tk.Button(
    root,
    text="🎯 GRAVAR POSIÇÃO",
    font=("Arial", 13, "bold"),
    command=gravar_posicao,
    height=2
)

botao_gravar.pack(
    fill="x",
    padx=25,
    pady=(8, 12)
)


# ============================================================
# CAMPO DE PALAVRA
# ============================================================

label_palavra = tk.Label(
    root,
    text="Digite a palavra:",
    font=("Arial", 11, "bold"),
    anchor="w"
)

label_palavra.pack(
    fill="x",
    padx=25
)


entrada = tk.Entry(
    root,
    font=("Arial", 18),
    relief="solid",
    bd=1
)

entrada.pack(
    fill="x",
    padx=25,
    pady=(5, 10)
)


# ============================================================
# LISTA DE SUGESTÕES
# ============================================================

lista = tk.Listbox(
    root,
    font=("Arial", 16),
    height=13,
    activestyle="none"
)

lista.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=(0, 10)
)


# ============================================================
# ATUALIZAR SUGESTÕES
# ============================================================

def atualizar_lista(event=None):

    prefixo = entrada.get().strip().lower()

    lista.delete(0, tk.END)

    if not prefixo:
        return

    encontrados = []

    for palavra in palavras:

        if palavra.lower().startswith(prefixo):

            encontrados.append(palavra)

            if len(encontrados) >= 30:
                break

    for palavra in encontrados:
        lista.insert(
            tk.END,
            palavra
        )


# Atualiza enquanto digita
entrada.bind(
    "<KeyRelease>",
    atualizar_lista
)


# ============================================================
# ENVIAR PALAVRA
# ============================================================

def enviar_palavra(palavra, retorno_x, retorno_y):

    try:

        # Verifica se existe posição gravada
        if (
            config["x"] is None
            or config["y"] is None
        ):

            root.after(
                0,
                lambda: status.config(
                    text="Primeiro grave a posição!"
                )
            )

            return


        # ----------------------------------------------------
        # COPIAR PALAVRA
        # ----------------------------------------------------

        pyperclip.copy(palavra)

        time.sleep(0.03)


        # ----------------------------------------------------
        # IR PARA O CAMPO GRAVADO
        # ----------------------------------------------------

        mouse_controller.position = (
            config["x"],
            config["y"]
        )

        time.sleep(0.05)


        # ----------------------------------------------------
        # CLICAR NO CAMPO
        # ----------------------------------------------------

        mouse_controller.click(
            mouse.Button.left
        )

        time.sleep(0.05)


        # ----------------------------------------------------
        # COLAR
        # ----------------------------------------------------

        with keyboard_controller.pressed(
            keyboard.Key.ctrl
        ):

            keyboard_controller.press("v")

        time.sleep(0.05)


        # ----------------------------------------------------
        # ENTER
        # ----------------------------------------------------

        keyboard_controller.press(
            keyboard.Key.enter
        )

        time.sleep(0.08)


        # ----------------------------------------------------
        # VOLTAR PARA ONDE CLICOU NA PALAVRA
        # ----------------------------------------------------

        mouse_controller.position = (
            retorno_x,
            retorno_y
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        root.after(
            0,
            lambda: status.config(
                text=f"Enviado: {palavra}"
            )
        )


    except Exception as e:

        print(
            "Erro enviando palavra:",
            e
        )

        root.after(
            0,
            lambda: status.config(
                text="Erro ao enviar palavra."
            )
        )


# ============================================================
# CLICAR NA SUGESTÃO
# ============================================================

def selecionar(event=None):

    selecao = lista.curselection()

    if not selecao:
        return

    palavra = lista.get(
        selecao[0]
    )


    # --------------------------------------------------------
    # PEGA A POSIÇÃO EXATA DO MOUSE
    # --------------------------------------------------------

    posicao_retorno = mouse_controller.position

    retorno_x = posicao_retorno[0]
    retorno_y = posicao_retorno[1]


    # --------------------------------------------------------
    # LIMPA A CAIXA
    # --------------------------------------------------------

    entrada.delete(
        0,
        tk.END
    )

    lista.delete(
        0,
        tk.END
    )


    # --------------------------------------------------------
    # ENVIA EM OUTRA THREAD
    # --------------------------------------------------------

    threading.Thread(
        target=enviar_palavra,
        args=(
            palavra,
            retorno_x,
            retorno_y
        ),
        daemon=True
    ).start()


# Clique na palavra
lista.bind(
    "<ButtonRelease-1>",
    selecionar
)


# ============================================================
# ENTER TAMBÉM ENVIA A PALAVRA SELECIONADA
# ============================================================

def enviar_com_enter(event=None):

    selecao = lista.curselection()

    if selecao:

        selecionar()

        return "break"


lista.bind(
    "<Return>",
    enviar_com_enter
)


# ============================================================
# ESC LIMPA A PESQUISA
# ============================================================

def limpar(event=None):

    entrada.delete(
        0,
        tk.END
    )

    lista.delete(
        0,
        tk.END
    )


entrada.bind(
    "<Escape>",
    limpar
)


# ============================================================
# INFORMAÇÃO DE PALAVRAS
# ============================================================

if len(palavras) > 0:

    status.config(
        text=f"{len(palavras)} palavras carregadas."
    )

else:

    status.config(
        text="Nenhuma palavra carregada!"
    )


# ============================================================
# FECHAR
# ============================================================

def fechar():

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    fechar
)


# ============================================================
# INICIAR
# ============================================================

entrada.focus_set()

root.mainloop()
