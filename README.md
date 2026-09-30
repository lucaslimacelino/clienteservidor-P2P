# Avaliacao de desempenho: Cliente-Servidor e P2P

Projeto da atividade de avaliacao de desempenho de transferencia de arquivos.

Arquiteturas implementadas:

1. Cliente-servidor sequencial: atende um cliente por vez.
2. Cliente-servidor com uma thread por cliente.
3. Cliente-servidor com pool de threads.
4. P2P simplificado: os peers podem obter blocos do arquivo do seed e de outros peers.

O cliente recebe os dados e os descarta, portanto o arquivo baixado nao e salvo em disco.

## 1. Requisitos

- Windows, Linux ou macOS
- Python 3.11 ou superior
- matplotlib

Nao e necessario Docker, maquina virtual ou WSL.

## 2. Baixar e abrir o projeto

Clone ou baixe este repositorio e entre na pasta pelo terminal.

Windows PowerShell:

```powershell
cd "C:\caminho\para\codigo_e_resultados"
```

## 3. Instalar dependencia

```powershell
python -m pip install -r requirements.txt
```

## 4. Criar os arquivos de teste

```powershell
python make_files.py
```

Serão criados localmente:

```text
arquivos/
├── 5MB.bin
├── 50MB.bin
└── 500MB.bin
```

## 5. Fazer um teste pequeno

Sequencial:

```powershell
python run_exp.py --arch seq --size_mb 5 --n 1 --rate_mb 100 --pool 4 --rep 1
```


Os resultados brutos sao salvos em `resultados/results.jsonl`.

## 6. Executar a bateria completa

```powershell
python run_all.py
```

Configuracao padrao em `run_all.py`:

- arquivos: 5, 50 e 500 MB
- clientes: 1, 2, 4 e 8
- arquiteturas: seq, thread, pool e p2p
- 5 MB: 3 repeticoes
- 50 MB: 3 repeticoes
- 500 MB: 1 repeticao
- limite de envio: 100 MB/s
- pool: 4 threads

Se quiser usar 1, 2, 5, 10 e 20 clientes, altere:

```python
CLIENTS = [1, 2, 4, 8]
```

para:

```python
CLIENTS = [1, 2, 5, 10, 20]
```



## 7. Execucao resumida para outro computador

Depois de clonar o repositorio:

```powershell
python -m pip install -r requirements.txt
python make_files.py
python run_all.py
python gerar_estatisticas.py
```

Os resultados ficam em `resultados/`.

## 8. Observacao sobre a rede

Os testes usam `127.0.0.1`, portanto os clientes e servidores rodam no mesmo computador. Isso permite comparar as arquiteturas sem precisar de varias maquinas.

A taxa de 100 MB/s e uma limitacao artificial para controlar os tempos do experimento. Ela pode ser alterada em `run_all.py`.
