# Recuperação de Imagens por Similaridade

Sistema de **recuperação de imagens baseada em conteúdo** (*Content-Based Image Retrieval — CBIR*). A partir de uma imagem de consulta, o programa busca as `N` imagens mais semelhantes em uma pasta de imagens, usando histogramas normalizados como descritores e distância euclidiana como métrica de comparação.

Além da recuperação, o projeto avalia os descritores por meio de classificação por votação entre as classes das imagens recuperadas e calcula a taxa de acerto sobre toda a base.

## Funcionalidades

- Recebe uma imagem de referência, uma pasta com a base e o valor de `N`.
- Extrai histogramas normalizados, interpretados como funções de densidade de probabilidade (PDFs).
- Calcula a distância euclidiana entre o descritor da consulta e os descritores das imagens da base.
- Ordena as imagens por similaridade, da menor para a maior distância.
- Desconsidera a própria imagem de consulta quando ela está presente na base.
- Exibe os nomes, as classes e as distâncias das imagens recuperadas.
- Prediz a classe da consulta por votação majoritária entre as imagens retornadas.
- Calcula a taxa de acerto ao usar cada imagem da base como consulta.
- Compara diferentes estratégias de representação por histogramas.

## Descritores implementados

O programa executa a recuperação e a avaliação para cada um dos seguintes descritores:

| Descritor | Descrição | Dimensão |
|---|---|---:|
| Histograma 3D RGB | Histograma conjunto dos canais RGB, com 8 níveis por canal | 512 bins |
| Histograma em tons de cinza | Histograma de intensidades em escala de cinza | 256 bins |
| Histograma RGB médio | Histograma da média dos canais R, G e B por pixel | 256 bins |
| Histograma HSV quantizado | Histograma conjunto HSV com 16 níveis de H, 3 de S e 3 de V | 144 bins |
| Histograma local 2×2 | Concatenação de histogramas HSV quantizados em 4 regiões | 576 bins |
| Histograma local 4×4 | Concatenação de histogramas HSV quantizados em 16 regiões | 2304 bins |
| Histograma local 8×8 | Concatenação de histogramas HSV quantizados em 64 regiões | 9216 bins |

Os histogramas globais são normalizados para que sua soma seja igual a 1. Nos descritores locais, cada região possui um histograma HSV normalizado individualmente antes da concatenação.

## Requisitos

- Python 3.10 ou superior
- NumPy
- Pillow

Instale as dependências com:

```bash
pip install numpy pillow
```

## Estrutura esperada da base

A base deve ser uma pasta que contenha arquivos de imagem. Para que a avaliação por classe funcione corretamente, os nomes dos arquivos devem seguir preferencialmente o padrão:

```text
c<classe>_<identificador>.<extensão>
```

Exemplos:

```text
c1_001.jpg
c1_002.jpg
c2_001.jpg
c3_015.png
```

Nesse formato, a classe é extraída do trecho numérico logo após a letra `c`. Por exemplo, `c12_045.jpg` pertence à classe `12`.

Caso o arquivo não siga esse padrão, o nome do arquivo sem extensão será utilizado como classe.

## Como executar

Salve o arquivo principal como `trab1.py` e execute no terminal:

```bash
python trab1.py
```

Em seguida, informe:

1. O caminho da pasta com a base de imagens.
2. O caminho da imagem de referência.
3. A quantidade `N` de imagens mais similares a recuperar.

Exemplo:

```text
Digite o caminho para a pasta: ./base_imagens
Digite o caminho para a imagem de referência: ./base_imagens/c1_001.jpg
Digite o número de imagens a serem recuperadas: 5
```

O programa executará todos os descritores, exibindo para cada um deles as imagens recuperadas, a classe estimada para a consulta e a avaliação global da base.

## Método utilizado

### 1. Extração dos descritores

Para a imagem de consulta e para cada imagem da base, o programa calcula um vetor de características baseado em histograma. Os histogramas são normalizados para reduzir a influência das dimensões da imagem:

\[
p(i) = \frac{h(i)}{\sum_j h(j)}
\]

Em que `h(i)` é a contagem do bin `i` e `p(i)` é sua probabilidade normalizada.

### 2. Cálculo da distância

A similaridade é obtida pela distância euclidiana entre o vetor da consulta `q` e o vetor de uma imagem da base `x`:

\[
d(q, x) = \sqrt{\sum_{i=1}^{m}(q_i - x_i)^2}
\]

Quanto menor for a distância, maior é a semelhança entre as imagens segundo o descritor selecionado.

### 3. Recuperação das imagens

As distâncias são ordenadas em ordem crescente. As `N` imagens com menor distância são retornadas como as mais semelhantes à imagem de consulta.

### 4. Classificação por votação

A classe de cada imagem recuperada é identificada pelo nome do arquivo. A classe mais frequente entre as `N` imagens recuperadas é definida como a classe predita da imagem de consulta.

Em caso de empate na quantidade de votos, o critério de desempate é a menor soma das distâncias das imagens pertencentes a cada classe empatada.

### 5. Taxa de acerto

A avaliação percorre todas as imagens da base. Cada imagem é usada como consulta, recupera as `N` imagens mais similares e tem sua classe estimada por votação.

\[
\text{Taxa de acerto} = \frac{\text{número de classificações corretas}}{\text{número total de consultas}}
\]

## Exemplo de saída

```text
======================================================================
Histograma HSV quantizado
======================================================================

Imagens recuperadas:
01. c1_023.jpg | classe: 1 | distância: 0.08421736
02. c1_018.jpg | classe: 1 | distância: 0.09155342
03. c2_006.jpg | classe: 2 | distância: 0.11682901

Resultado:
Classe real: 1
Classe estimada: 1
Acertou: Sim

Avaliação da base:
Acertos: 82
Consultas: 100
Taxa de acerto: 82.00%
```

Os números acima são apenas ilustrativos e variam de acordo com a base, a imagem de consulta e o valor de `N`.

## Arquivos

```text
.
├── trab1.py        # Implementação do sistema de recuperação e avaliação
└── README.md       # Documentação do projeto
```

## Autoria

Trabalho desenvolvido para a atividade de Recuperação de Imagens por Similaridade.
