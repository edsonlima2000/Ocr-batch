"""Agrupa arquivos TXT da pasta de resultados em um único documento."""

from pathlib import Path


def agrupar(pasta: Path, nome_saida: str) -> tuple[Path, int]:
    destino = pasta / nome_saida
    arquivos = sorted(
        (arquivo for arquivo in pasta.rglob("*.txt") if arquivo.resolve() != destino.resolve()),
        key=lambda arquivo: str(arquivo.relative_to(pasta)).casefold(),
    )

    partes: list[str] = []
    for arquivo in arquivos:
        nome = arquivo.relative_to(pasta)
        conteudo = arquivo.read_text(encoding="utf-8-sig", errors="replace").strip()
        partes.append(f"===== {nome} =====\n\n{conteudo}")

    destino.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    return destino, len(arquivos)


if __name__ == "__main__":
    pasta_textos = Path(__file__).resolve().parent / "textos"
    saida, quantidade = agrupar(pasta_textos, "BM-Conhecimento13082026.txt")
    print(f"{quantidade} arquivo(s) agrupado(s) em: {saida}")
