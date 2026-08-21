import numpy as np
from PIL import Image
from pathlib import Path
import re
from collections import Counter

def _hsv_histograma_regiao(regiao):
    array = np.asarray(regiao.convert("HSV"))
    h, s, v = array[:, :, 0], array[:, :, 1], array[:, :, 2]
    h_quant = h // 16
    s_quant = np.where(s > 170, 2, np.where(s > 84, 1, 0))
    v_quant = np.where(v > 170, 2, np.where(v > 84, 1, 0))
    indices = (h_quant.ravel() * 9) + (s_quant.ravel() * 3) + v_quant.ravel()

    hist = np.bincount(indices, minlength=144).astype(np.float32)
    hist = hist / np.sum(hist)
        
    return hist

def histograma_local(imagem, linhas, colunas):
    """Concatena histogramas HSV quantizados de cada região da grade."""
    imagem = imagem.convert("RGB")
    largura, altura = imagem.size
    histogramas = []

    for linha in range(linhas):
        y_inicio = linha * altura // linhas
        y_fim = (linha + 1) * altura // linhas
        for coluna in range(colunas):
            x_inicio = coluna * largura // colunas
            x_fim = (coluna + 1) * largura // colunas
            regiao = imagem.crop((x_inicio, y_inicio, x_fim, y_fim))
            histogramas.append(_hsv_histograma_regiao(regiao))

    histograma = np.concatenate(histogramas).astype(np.float32)
    return histograma / histograma.sum()

def histograma_local_2x2(imagem):
    return histograma_local(imagem, 2, 2)

def histograma_local_4x4(imagem):
    return histograma_local(imagem, 4, 4)

def histograma_local_8x8(imagem):
    return histograma_local(imagem, 8, 8)

def histograma_cinza(imagem):
    imagem_cinza = imagem.convert('L')
    hist = np.asarray(imagem_cinza.histogram(), dtype=np.float32)

    return hist / hist.sum()

def histograma_3d(imagem):
    "usa uma redução de cores para criar um histograma 3D com 512 bins"
    imagem_rgb = imagem.convert('RGB')
    imagem_reduzida = imagem_rgb.point(lambda p: p // 32)
    largura, altura = imagem_reduzida.size
    cores_contadas = imagem_reduzida.getcolors(maxcolors=largura * altura)
    
    hist = np.zeros(512, dtype=float)

    if cores_contadas:
        contagens, cores = zip(*cores_contadas)
        r, g, b = np.array(cores).T
        indices_1d = (r * 64) + (g * 8) + b
        
        hist[indices_1d] = contagens
            
    return hist / np.sum(hist)

def histograma_rgb_media(imagem):
    imagem_rgb = imagem.convert('RGB')
    imagem_array = np.array(imagem_rgb)
    
    r = imagem_array[:, :, 0].astype(np.uint16)
    g = imagem_array[:, :, 1].astype(np.uint16)
    b = imagem_array[:, :, 2].astype(np.uint16)

    rgb_media = (r + g + b) // 3
    
    hist = np.bincount(rgb_media.ravel(), minlength=256).astype(np.float32)
            
    return hist / np.sum(hist)

def histograma_hsv_quantizado(imagem):
    imagem_hsv = imagem.convert('HSV')
    
    imagem_array = np.array(imagem_hsv)
    
    h = imagem_array[:, :, 0]
    s = imagem_array[:, :, 1]
    v = imagem_array[:, :, 2]

    h_quant = h // 16
    
    s_quant = np.zeros_like(s) 
    s_quant[s > 84] = 1        
    s_quant[s > 170] = 2       
    
    v_quant = np.zeros_like(v)
    v_quant[v > 84] = 1
    v_quant[v > 170] = 2
    
    h_flat = h_quant.ravel()
    s_flat = s_quant.ravel()
    v_flat = v_quant.ravel()
    
    indices_1d = (h_flat * 9) + (s_flat * 3) + v_flat

    hist = np.bincount(indices_1d, minlength=144).astype(np.float32)
    hist = hist / np.sum(hist)
    
    return hist

def classe_imagem(path: str | Path) -> str:
    match = re.match(r"c(\d+)_", Path(path).name, flags=re.IGNORECASE)
    return match.group(1) if match else Path(path).stem

def histogramas_da_pasta(pasta: str | Path, funcao_histograma):
    pasta = Path(pasta)
    histogramas = []
    caminhos = []

    caminhos_ordenados = sorted(
        arquivo
        for arquivo in pasta.iterdir()
        if arquivo.is_file()
    )

    for arquivo in caminhos_ordenados:
        try:
            imagem = Image.open(arquivo)
            hist = funcao_histograma(imagem)
            histogramas.append(hist)
            caminhos.append(arquivo)
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

    return np.array(histogramas), caminhos

def matriz_distancias(histogramas):
    X = np.asarray(histogramas, dtype=np.float32)
    sq = np.sum(X**2, axis=1)
    d2 = sq[:, None] + sq[None, :] - 2 * (X @ X.T)
    return np.sqrt(np.maximum(d2, 0))  # clip por causa de erro de arredondamento

def recuperar_top_n(distancias, indice_referencia, caminhos, n):
    caminhos = list(caminhos)
    indices_validos = np.arange(len(caminhos))
    indices_validos = indices_validos[indices_validos != indice_referencia]

    distancia_ref = distancias[indice_referencia, indices_validos]
    ordem = np.argsort(distancia_ref)[:n]
    indices_top = indices_validos[ordem]

    resultados = []
    for idx in indices_top:
        caminho = Path(caminhos[idx])
        resultados.append({
            "caminho": caminho,
            "nome": caminho.name,
            "classe": classe_imagem(caminho),
            "distancia": float(distancias[indice_referencia, idx]),
        })

    return resultados

def classe_predita(resultados):
    if not resultados:
        return None

    votos = Counter(resultado["classe"] for resultado in resultados)
    maior_numero_de_votos = max(votos.values())
    classes_empatadas = {
        classe for classe, quantidade in votos.items()
        if quantidade == maior_numero_de_votos
    }

    # Desempate determinístico: classe com menor distância acumulada.
    return min(
        classes_empatadas,
        key=lambda classe: sum(
            resultado["distancia"]
            for resultado in resultados
            if resultado["classe"] == classe
        )
    )

def avaliar_taxa_acerto(n, distancias, caminhos_processados):
    acertos = 0
    detalhes = []

    for indice, caminho_consulta in enumerate(caminhos_processados):
        resultados = recuperar_top_n(
            distancias=distancias,
            indice_referencia=indice,
            caminhos=caminhos_processados,
            n=n,
        )

        classe_real = classe_imagem(caminho_consulta)
        classe_estimada = classe_predita(resultados)
        acertou = classe_estimada == classe_real
        acertos += int(acertou)

        detalhes.append({
            "consulta": caminho_consulta,
            "classe_real": classe_real,
            "classe_predita": classe_estimada,
            "acertou": acertou,
            "resultados": resultados,
        })

    taxa = acertos / len(caminhos_processados)

    return {
        "acertos": acertos,
        "total_consultas": len(caminhos_processados),
        "taxa_acerto": taxa,
        "detalhes": detalhes,
    }


def imprimir_resultados(resultados):
    print("\nImagens recuperadas:")
    if not resultados:
        print("Nenhuma imagem disponível para recuperação.")
        return

    for posicao, resultado in enumerate(resultados, start=1):
        print(
            f"{posicao:02d}. {resultado['nome']} | "
            f"classe: {resultado['classe']} | "
            f"distância: {resultado['distancia']:.8f}"
        )

def imprimir_avaliacao(avaliacao):
    print("\nAvaliação da base:")
    print(f"Acertos: {avaliacao['acertos']}")
    print(f"Consultas: {avaliacao['total_consultas']}")
    print(f"Taxa de acerto: {avaliacao['taxa_acerto']:.2%}")

def main():
    caminho_dir = Path(input("Digite o caminho para a pasta: "))
    caminho_referencia = Path(input("Digite o caminho para a imagem de referência: "))
    n = int(input("Digite o número de imagens a serem recuperadas: "))

    descritores = {
        "Histograma 3D RGB": histograma_3d,
        "Histograma em tons de cinza": histograma_cinza,
        "Histograma RGB médio": histograma_rgb_media,
        "Histograma HSV quantizado": histograma_hsv_quantizado,
        "Histograma local 2x2": histograma_local_2x2,
        "Histograma local 4x4": histograma_local_4x4,
        "Histograma local 8x8": histograma_local_8x8,
    }

    for nome_descritor, funcao in descritores.items():
        print(f"\n{'=' * 70}\n{nome_descritor}\n{'=' * 70}")

        histogramas, caminhos = histogramas_da_pasta(caminho_dir, funcao)
        distancias = matriz_distancias(histogramas)

        caminhos_resolvidos = [caminho.resolve() for caminho in caminhos]
        idx_ref = caminhos_resolvidos.index(caminho_referencia.resolve())

        resultados = recuperar_top_n(
            distancias=distancias,
            indice_referencia=idx_ref,
            caminhos=caminhos,
            n=n,
        )

        imprimir_resultados(resultados)
        classe_real = classe_imagem(caminho_referencia)
        classe_estimada = classe_predita(resultados)
        acertou = classe_estimada == classe_real
        print("\nResultado:")
        print(f"Classe real: {classe_real}")
        print(f"Classe estimada: {classe_estimada}")
        print(f"Acertou: {'Sim' if acertou else 'Não'}")

        avaliacao = avaliar_taxa_acerto(n, distancias, caminhos)
        imprimir_avaliacao(avaliacao)

if __name__ == "__main__":
    main()