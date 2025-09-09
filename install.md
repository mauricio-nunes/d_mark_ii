# D Mark I — Guia de Instalação do Binário

## Sobre
D Mark I é um CLI em Python para acompanhamento e análise de investimentos em **Ações** e **FIIs**, integrando dados da B3, CVM e APIs externas.

---

## Requisitos

- Linux x64
- Python 3.11+ (apenas para empacotamento)
- PyInstaller (`pip install pyinstaller`)
- Permissão de execução no terminal

---

## Processo de Geração do Binário

1. **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/d_mark_ii.git
    cd d_mark_ii
    ```

2. **Instale o PyInstaller:**

    ```bash
    python3 -m pip install pyinstaller
    ```

3. **Crie o arquivo `.spec` personalizado:**

    Salve como `dmarki_cli.spec` na raiz do projeto:

    ```python
    # dmarki_cli.spec
    import os, pyfiglet, glob
    migrations = [(f, 'app/db/migrations') for f in glob.glob('app/db/migrations/*')]
    a = Analysis(
        ['app/main.py'],
        pathex=['.'],
        binaries=[],
        datas=[
            (os.path.join(os.path.dirname(pyfiglet.__file__), 'fonts'), 'pyfiglet/fonts'),
        ] + migrations,
        hiddenimports=[],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
    )
    pyz = PYZ(a.pure, a.zipped_data, cipher=None)
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='dmarki_cli',
        debug=False,
        strip=False,
        upx=True,
        console=True,
    )
    ```

4. **Gere o binário:**

    ```bash
    pyinstaller dmarki_cli.spec
    ```

5. **O binário estará em `dist/dmarki_cli`:**

    ```bash
    ls dist/dmarki_cli
    ```

---

## Como enviar para o cliente

- Envie **apenas o arquivo** `dist/dmarki_cli` gerado.
- Se o sistema usar arquivos extras (ex: templates, configs), inclua-os juntos ou embuta no binário via `.spec`.

---

## Como rodar no cliente

1. Dê permissão de execução:

    ```bash
    chmod +x dmarki_cli
    ```

2. Execute o CLI:

    ```bash
    ./dmarki_cli
    ```

---

## Dicas

- Teste o binário em ambiente limpo antes de enviar.
- Para atualizar, gere o binário novamente e envie ao cliente.
- Para dúvidas, consulte o README original ou abra uma issue.