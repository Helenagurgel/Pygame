# Head Soccer DesSoft

## Integrantes

- Felipe Lima
- Helena Gurgel
- Rodrigo do Valle

## Descrição do jogo

Head Soccer DesSoft é um jogo de futebol cabeça a cabeça para dois jogadores (ou um jogador contra a CPU) desenvolvido em Python com a biblioteca pygame-ce. Cada partida dura 60 segundos, e vence quem marcar mais gols dentro do tempo. A câmera é fixa, o campo ocupa a tela inteira e as traves ficam em cada extremidade do cenário.

O jogo conta com um sistema de personagens com atributos distintos: velocidade e altura de pulo variam de herói para herói, obrigando cada jogador a adaptar sua estratégia à escolha do oponente. O fluxo de jogo passa por três telas de seleção — personagem, estádio e dificuldade (modo 1P) — antes de iniciar a partida, tornando cada confronto único.

Power-ups surgem aleatoriamente no campo durante a partida e mudam o equilíbrio do jogo de forma temporária: a bola pode pegar fogo, um jogador pode dobrar de tamanho, o adversário pode ser congelado ou a gravidade da cena inteira pode cair drasticamente. Esses elementos garantem que mesmo partidas equilibradas terminem com reviravoltas emocionantes.

Os estádios vão além do visual: cada cenário altera os modificadores físicos da partida. Na Lua a gravidade é 40 % da normal, tornando os chutes mais longos e os saltos astronômicos; na Pista Gelada o atrito é reduzido, fazendo a bola deslizar de forma diferente e dificultando as paradas bruscas. Escolher o estádio certo para o seu personagem é parte da estratégia.

O projeto foi desenvolvido como trabalho da disciplina Desenvolvimento de Software (DesSoft) do Insper, com foco em boas práticas de engenharia de software: separação de responsabilidades em cenas, entidades e utilitários, ausência de números mágicos no código e uso de Inteligência Artificial Generativa como ferramenta de apoio ao desenvolvimento.

## Como rodar

```bash
git clone https://github.com/Helenagurgel/Pygame.git
cd Pygame/projeto
python -m venv .venv && source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  no Windows
pip install -r requirements.txt
python main.py
```

## Controles

| Ação       | Jogador 1 (P1) | Jogador 2 (P2) |
|------------|:--------------:|:--------------:|
| Mover esquerda | `A` | `←` |
| Mover direita  | `D` | `→` |
| Pular          | `W` | `↑` |
| Chutar         | `ESPAÇO` | `ENTER` |

## Mecânica de chute

O chute utiliza **força fixa** de módulo 18 px/frame (constante `KICK_FORCE`), mas com **direção variável** determinada pelo vetor que vai do centro do jogador até o centro da bola no momento do input. O jogador precisa estar a no máximo 70 px da bola (`KICK_RANGE`) para o chute ser registrado; fora desse alcance, o comando é ignorado. Esse modelo garante que a habilidade do jogador esteja em se posicionar corretamente antes de chutar, e não em calibrar a força do golpe.

## Personagens

| Personagem | Velocidade | Pulo | Descrição |
|------------|:----------:|:----:|-----------|
| **Veloz** | ×1.3 | ×1.0 | Rápido, mas pulo médio |
| **Saltador** | ×1.0 | ×1.4 | Pulo alto, velocidade média |
| **Equilibrado** | ×1.1 | ×1.1 | Atributos balanceados |
| **Tanque** | ×0.9 | ×0.9 | Lento, mas poderoso |

## Estádios

| Estádio | Gravidade | Atrito | Descrição |
|---------|:---------:|:------:|-----------|
| **Estádio Clássico** | ×1.0 | ×1.0 | Campo padrão de futebol |
| **Lua** | ×0.4 | ×1.0 | Gravidade reduzida — bola flutua mais |
| **Pista Gelada** | ×1.0 | ×0.7 | Atrito baixo — escorregadio |

## Power-ups

| Power-up | Duração | Efeito |
|----------|:-------:|--------|
| **FireBall** | 5 s | A bola pega fogo; chutes ficam 1,5× mais fortes |
| **GiantPlayer** | 6 s | O jogador que coletou dobra de tamanho |
| **Freeze** | 2 s | Congela o adversário — apenas o input é bloqueado |
| **LowGravity** | 4 s | Reduz a gravidade de toda a cena para 30 % do valor atual |

## Capturas de tela

> Adicione ao menos 3 imagens na pasta `docs/screenshots/` e referencie abaixo.

| Menu principal | Gameplay | Gol |
|:-:|:-:|:-:|
| ![Menu](docs/screenshots/menu.png) | ![Gameplay](docs/screenshots/gameplay.png) | ![Gol](docs/screenshots/goal.png) |

## Vídeo de demonstração

> [Assista ao vídeo de demonstração no YouTube](https://youtu.be/PLACEHOLDER)
> *(substitua o link pelo URL real após publicar)*

## Uso de Inteligência Artificial Generativa

<!-- Descreva aqui como a IA generativa foi utilizada no desenvolvimento deste projeto. -->
