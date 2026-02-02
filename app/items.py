# items.py
import random

BASE_ITENS = [
    "sofá",
    "mesa de jantar",
    "cadeira",
    "geladeira",
    "fogão",
    "micro-ondas",
    "liquidificador",
    "ventilador",
    "ar-condicionado",
    "luminária",
    "controle de videogame",
    "console playstation",
    "xbox series x",
    "nintendo switch",
    "teclado gamer",
    "mouse gamer",
    "headset gamer",
    "cadeira gamer",
    "monitor gamer",
    "volante para jogos",
    "cimento",
    "areia",
    "tijolo",
    "bloco de concreto",
    "vergalhão",
    "massa corrida",
    "tinta acrílica",
    "telha cerâmica",
    "cimento cola",
    "rejunte",
    "batom",
    "base facial",
    "pó compacto",
    "rímel",
    "delineador",
    "perfume",
    "hidratante corporal",
    "protetor solar",
    "creme anti-idade",
    "shampoo",
]

EXTRAS = [
    "meia perdida na lavanderia",
    "controle sem pilha",
    "mouse que falha só em reunião",
    "teclado com tecla quebrada",
    "café frio esquecido",
    "copo térmico misterioso",
    "fone emaranhado",
    "carregador que só funciona em certo ângulo",
    "cadeira que range",
    "mesa bamba",
    "panela antiaderente riscada",
    "espelho de banheiro",
    "escova de dente elétrica",
    "toalha molhada na cama",
    "almofada decorativa inútil",
    "tapete escorregadio",
    "espada lendária nível 1",
    "armadura enferrujada",
    "poção de mana vazia",
    "controle clássico retrô",
    "cartucho antigo",
    "tijolo ecológico",
    "furadeira",
    "parafuso philips",
    "trena",
    "nível a laser",
    "batom vermelho vibrante",
    "perfume amadeirado",
    "hidratante facial noturno",
    "máscara capilar",
    "shampoo antiqueda",
    "banana madura demais",
    "geladeira fazendo barulho estranho",
    "micro-ondas com relógio errado",
    "relógio parado certo duas vezes ao dia",
    "cadeira de plástico branca",
    "ventilador que só tem duas velocidades",
]


def gerar_lista_itens(quantidade=500):
    itens = BASE_ITENS.copy()
    contador = 1

    while len(itens) < quantidade:
        item = random.choice(EXTRAS)
        itens.append(f"{item}")
        contador += 1

    random.shuffle(itens)
    return itens
