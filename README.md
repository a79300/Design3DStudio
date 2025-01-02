# Controle de Mobiliário Virtual

## Tema Principal e Motivação

Este projeto visa explorar o uso de tecnologias de modelagem 3D para criar uma experiência interativa onde os usuários podem adicionar, manipular e substituir móveis virtuais em um ambiente tridimensional. Utilizando o **Blender**, uma poderosa ferramenta de criação e animação 3D, o objetivo principal é fornecer uma plataforma intuitiva para o design de interiores, permitindo aos usuários experimentar diferentes disposições de móveis e objetos no espaço virtual.

A motivação do projeto é integrar tecnologias avançadas de modelagem e animação 3D em aplicações práticas como design de interiores, educação e entretenimento. A experiência interativa permite visualizações dinâmicas de estilos de decoração, ajustes de escala e personalização de móveis, proporcionando uma maneira criativa e eficiente de planejar espaços.

## Funcionalidades Principais

- **Adição de Objetos Virtuais**: Os usuários podem adicionar diversos móveis e objetos virtuais ao ambiente 3D, personalizando o espaço conforme suas preferências.
- **Manipulação de Objetos Virtuais**: É possível alterar a posição, rotação e até substituir móveis e objetos dentro do ambiente 3D, permitindo um design dinâmico e interativo.
- **Interação por Gestos**: Utilização de gestos corporais e das mãos para controlar e manipular objetos virtuais, oferecendo uma experiência mais imersiva e intuitiva.
- **Deteção de Objetos Reais**: A possibilidade de importar imagens ou dados de móveis reais para integrá-los ao ambiente 3D virtual, tornando a experiência ainda mais próxima da realidade.

## Público-Alvo

- **Designers de Interiores**: Ferramenta para simulação e visualização de ambientes decorados em 3D, permitindo experimentar diferentes móveis e estilos de decoração.
- **Professores e Alunos**: Aplicação educacional para ensinar conceitos de design, modelagem 3D e visualização espacial de maneira interativa.
- **Entusiastas de Tecnologia**: Incentivo à exploração de novas formas de interação com ambientes 3D, estimulando a criatividade e personalização de espaços virtuais.

## Especificações da Aplicação

### Detecção de Gestos

| Contexto            | Evento                                    | Resposta                 | Algoritmo  | Prioridade |
|---------------------|-------------------------------------------|--------------------------|------------|------------|
| Deteção de Gestos    | Fazer uma pinça com a mão direita         | Agarrar objeto           | MediaPipe  | M1 - MVP   |
| Deteção de Gestos    | Detetar a pose de uma tesoura             | Eliminar Objeto           | MediaPipe  | M1 - MVP   |
| Deteção de Gestos    | Aproximar o polegar e o indicador         | Diminuir o tamanho do Objeto | MediaPipe | M1 - MVP   |
| Deteção de Gestos    | Distanciar o polegar e o indicador        | Aumentar o tamanho do objeto | MediaPipe | M1 - MVP   |

### Movimento Corporal

| Contexto            | Evento                                  | Resposta                        | Algoritmo  | Prioridade |
|---------------------|-----------------------------------------|---------------------------------|------------|------------|
| Movimento Corporal  | Mão, Swipe right                        | Próximo Objeto                  | MediaPipe  | M1 - MVP   |
| Movimento Corporal  | Mão, Swipe Left                         | Objeto Anterior                 | MediaPipe  | M1 - MVP   |
| Movimento Corporal  | Inclinar cabeça direita                 | Rodar Quarto 3D para a direita  | MediaPipe  | M1 - MVP   |
| Movimento Corporal  | Inclinar cabeça esquerda                | Rodar Quarto 3D para a esquerda | MediaPipe  | M1 - MVP   |
| Movimento Corporal  | Levantar braço esquerdo                | Guardar Quarto 3D              | MediaPipe  | M1 - MVP   |

### Reconhecimento de Objetos

| Contexto            | Evento                         | Resposta                                  | Algoritmo  | Prioridade |
|---------------------|--------------------------------|-------------------------------------------|------------|------------|
| Reconhecimento de Objetos | Telemóvel detectado        | O telemóvel é trocado por uma TV virtual  | MediaPipe  | M1 - MVP   |
| Reconhecimento de Objetos | Cadeira detectada          | A cadeira é trocada por uma cadeira virtual | MediaPipe | M1 - MVP   |
| Reconhecimento de Objetos | Garrafa detectada          | A garrafa é trocada por uma garrafa virtual | MediaPipe | M1 - MVP   |
| Reconhecimento de Objetos | Mesa detectada             | A mesa é trocada por uma mesa virtual      | MediaPipe | M1 - MVP   |
| Reconhecimento de Objetos | Vaso detectado             | O vaso é tocado por um vaso virtual        | MediaPipe | M1 - MVP   |

## Algoritmos Necessários

- **MediaPipe**: Utilizado para a detecção e rastreamento de poses corporais, identificação de gestos e reconhecimento de objetos. Permite uma interação mais natural e intuitiva com os elementos virtuais.
- **OpenCV**: Usado para renderização e manipulação dos objetos virtuais no ambiente 3D, possibilitando o controle e a visualização dinâmica dos móveis e objetos adicionados.

## Cronograma de Desenvolvimento

### MVP (Minimum Viable Product)

- **Criação do Ambiente 3D no Blender**: Desenvolvimento de um espaço virtual 3D onde os móveis e objetos podem ser adicionados e manipulados.
- **Deteção de Poses Corporais**: Implementação da deteção e rastreamento de poses corporais para interação com o ambiente 3D.
- **Adição e Controle Básico de Móveis Virtuais**: Funcionalidade que permite ao usuário adicionar móveis ao ambiente 3D e controlá-los de maneira simples (posicionamento, rotação, etc.).
- **Deteção e Interação com Gestos Simples das Mãos**: Implementação de gestos simples, como agarrar com dois dedos, rodar e mover objetos virtuais, permitindo uma interação intuitiva com o ambiente.
