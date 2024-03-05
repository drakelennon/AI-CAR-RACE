import pygame as pp
import os
import random
import math
import sys
import neat
import time
import pickle
from utils import *

pp.init()

MODO = int(input('digite 1 para um carro ou 2 para varios carros por vez: '))

# Constantes
fator_multi_pista = .9
TELA_ALTU = 900 * fator_multi_pista
TELA_LARG = 1500 * fator_multi_pista  # 900 pro antigo
TELA = pp.display.set_mode((TELA_LARG, TELA_ALTU))
pp.display.set_caption("Corrida IA")

# Carrega as imagens e as modifica, se necessario
GRAMA = scale_image(pp.image.load(os.path.join("PythonProjects/NewAI/imgs/other", "grass.jpg")), 2.5)
GRAY = scale_image(pp.image.load(os.path.join("PythonProjects/NewAI/imgs/other", "gray.jpg")), 1.5)
PISTA = scale_image(pp.image.load(os.path.join("PythonProjects/NewAI/imgs/other", "track.png")).convert_alpha(), fator_multi_pista)
BORDA = scale_image(pp.image.load(os.path.join("PythonProjects/NewAI/imgs/other", "border2.png")).convert_alpha(), fator_multi_pista)
CHEGADA = scale_image(pp.image.load(os.path.join("PythonProjects/NewAI/imgs/other", "finish.png")).convert_alpha(), fator_multi_pista)
CHEGADA2 = pp.transform.rotate(CHEGADA, 90)
CHEGADA_POS = (130, 250)
CHEGADA_POS2 = (600, 30)
carro_size = .055  # 20,88 x 45,66

BORDA_MASK = pp.mask.from_surface(BORDA)

CARROS_RAW = [pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "cyanCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "blackCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "purpleCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "redCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "yellowCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "blueCar.png")).convert_alpha(),
              pp.image.load(os.path.join("PythonProjects/NewAI/imgs/cars", "whiteCar.png")).convert_alpha()]

CARROS = []
for i in CARROS_RAW:
    j = scale_image(i, carro_size)
    CARROS.append(j)

# Fonte
FONT = pp.font.SysFont('comicsansms', 20, True, False)

# Variaveis globais
recorde = 0
melhorCarro = 0
carrosBatidos = 0
esqu = 90
dire = 270
ticks = 30
ultimaBatida = (0, 0)


# Classes
class AbstractCar:
    IMG = None
    angulos = (0, 180, 135, 45, 90, 25, 115, 65, 155)
    # angulos = (0, 180, 135, 45, 90) # 0, 180, 135, 45, 90, 25, 115, 65, 155
    inputs = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    line_size = 500  # 150
    anguloInicio = esqu
    corParedes = pp.Color(30, 80, 30, 255)
    corParedes2 = pp.Color(30, 30, 80, 255)

    def __init__(self, max_vel, rotation_vel):
        self.x, self.y = self.START_POS2  # START_POS pro antigo
        self.initial_x, self.initial_y = self.x, self.y

        self.rand = random.randint(0, 6)
        self.randColor1 = random.randint(0, 255)
        self.randColor2 = random.randint(0, 255)
        self.randColor3 = random.randint(0, 255)
        self.carros = CARROS[self.rand]
        self.img = self.carros
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angulo = self.anguloInicio
        self.accel = .1
        self.pontos = 0
        self.sensores = []
        self.vel_vector = pp.math.Vector2(0.8, 0)
        self.rect = self.img.get_rect()
        self.inicioTempo = time.time()
        self.tempoLinha = time.time()
        self.percorreu = 0
        self.horaBatida = 0
        self.distanciaTotal = 0
        self.total = 0
        self.dist_covered = 0
        self.frente = False
        self.freio = False
        self.esquerda = False
        self.direita = False
        self.nada = False
        self.first_check = False

    def rotate(self, left=False, right=False):
        if left:
            self.angulo += self.rotation_vel
            self.vel_vector.rotate_ip(self.rotation_vel)
        elif right:
            self.angulo -= self.rotation_vel
            self.vel_vector.rotate_ip(-self.rotation_vel)

    def move(self):
        old_x, old_y = self.x, self.y

        radians = math.radians(self.angulo)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel

        self.y -= vertical
        self.x -= horizontal

        distance_moved = math.sqrt((old_x - self.x) ** 2 + (old_y - self.y) ** 2)
        self.dist_covered += distance_moved

    def distancia(self):
        distance_x = self.x - self.initial_x
        distance_y = self.y - self.initial_y
        distance = (distance_x ** 2 + distance_y ** 2) ** 0.5
        return distance

    def collidePoi(self, mask, x=0, y=0):
        car_mask = pp.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        poi = mask.overlap(car_mask, offset)
        return poi

    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.center[0])
        y = int(self.rect.center[1])

        try:
            while not TELA.get_at((x, y)) == self.corParedes and length < self.line_size:
                length += 1
                x = int(self.rect.center[0] + math.cos(math.radians(self.angulo + radar_angle)) * length)
                y = int(self.rect.center[1] - math.sin(math.radians(self.angulo + radar_angle)) * length)
        except IndexError:
            pass

        # Desenha sensores
        pp.draw.line(TELA, (self.randColor2, self.randColor3, self.randColor1, 255), self.rect.center, (x, y), 1)
        pp.draw.circle(TELA, (self.randColor2, self.randColor3, self.randColor1, 255), (x, y), 1)

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                             + math.pow(self.rect.center[1] - y, 2)))

        self.sensores.append([radar_angle, dist])

    def data(self):
        inputz = self.inputs
        for i, radar in enumerate(self.sensores):
            inputz[i] = int(radar[1])
        return inputz

    def draw(self, tela):
        blit_rotate_center(tela, self.img, (self.x, self.y), self.angulo)

    def draw_rect(self, tamanho):
        pp.draw.rect(self.img, (0, 0, 0), (self.img.get_rect()), tamanho)


class Car(AbstractCar):
    START_POS = (180, 200)
    START_POS2 = (570, 50)

    def bounce(self):
        self.vel = -self.vel
        self.move()

    def go(self):
        self.rect.x = self.x
        self.rect.y = self.y
        self.pontos += 1
        self.sensores.clear()
        self.data()

        for radar_angle in self.angulos:
            self.radar(radar_angle)
        if self.reduz_vel() is False:
            self.move_fwd()

    def move_fwd(self):
        self.vel = min(self.vel + self.accel, self.max_vel)
        self.move()
        self.nada = False
        self.frente = True
        self.freio = False

    def turn_left(self):
        self.rotate(left=True)
        self.esquerda = True
        self.direita = False
        self.nada = False

    def turn_right(self):
        self.rotate(right=True)
        self.esquerda = False
        self.direita = True
        self.nada = False

    def no_turn(self):
        self.rotate(right=False)
        self.rotate(left=False)
        self.nada = True
        self.esquerda = False
        self.direita = False

    def reduz_vel(self):
        pass
        if time.time() - self.inicioTempo >= 1:
            self.vel = max(self.vel - self.accel / 1, 0)
            self.inicioTempo = time.time()
            self.move()
            self.freio = True
            self.nada = False
            self.frente = False
        else:
            self.move_fwd()

# Função de remoção
def remove_car(index):
    global carrosBatidos
    carros.pop(index)
    ge.pop(index)
    redes.pop(index)
    carrosBatidos += 1


# Função desenha
def draw(tela, images):
    for img, pos in images:
        TELA.blit(img, pos)


# Função principal
def eval_genomes(genomes, config):
    global carro, carros, obstaculos, ge, rede, redes, recorde, carrosBatidos, melhorCarro, ticks, clock, linhas, ultimaBatida, MODO, count, checks
    rodando = True
    clock = pp.time.Clock()

    carros = []
    ge = []
    redes = []
    linhas = []
    velocidade = 2
    manobrabilidade = 3.5

    for genome_id, genome in genomes:
        carros.append(Car(velocidade, manobrabilidade))
        ge.append(genome)
        rede = neat.nn.FeedForwardNetwork.create(genome, config)
        redes.append(rede)
        genome.fitness = 0

    def stats():
        text1 = FONT.render(f'Pontuação do Carro Mais Inteligente: {int(recorde/10)}m', True,
                            (255, 255, 255))
        text2 = FONT.render(f'Carros Restantes: {str(len(carros))}', True, (255, 255, 255))
        text3 = FONT.render(f'Geração: {str(p.generation)}', True, (255, 255, 255))
        text4 = FONT.render(f'Já Bateram: {str(carrosBatidos)}', True, (255, 255, 255))
        text5 = FONT.render('O circulo simboliza onde o carro mais inteligente bateu', True, (255, 255, 255))

        TELA.blit(text1, (340, 130))
        TELA.blit(text2, (340, 150))
        TELA.blit(text3, (340, 170))
        TELA.blit(text4, (500, 170))
        TELA.blit(text5, (340, 190))

    count = 49
    while rodando:
        for event in pp.event.get():
            if event.type == pp.QUIT:
                pp.quit()
                sys.exit()

            if event.type == pp.KEYDOWN:
                if event.key == pp.K_1:
                    ticks = 60

                if event.key == pp.K_2:
                    ticks = 120

                if event.key == pp.K_3:
                    ticks = 240

                if event.key == pp.K_4:
                    ticks = 480

                if event.key == pp.K_5:
                    ticks = 960

        images = [(GRAY, (0, 0)), (CHEGADA2, CHEGADA_POS2), (BORDA, (0, 0))]
        draw(TELA, images)
        pp.draw.circle(TELA, (127, 0, 127, 127), ultimaBatida, 20, 4)
        # pp.draw.rect(TELA, (200, 0, 200, 127), ultimaBatida, 4)

        if len(carros) == 0:
            break

        def varios():
            global recorde, ultimaBatida, carro, melhorCarro, dist_covered
            for count, carro in enumerate(carros):

                # ge[count].fitness += 0.1
                ge[count].fitness += carros[count].dist_covered / 30

                if recorde < carros[count].dist_covered:
                    recorde = carros[count].dist_covered
                    if carros[count].collidePoi(BORDA_MASK) is not None:
                        ultimaBatida = carros[count].rect.center
                        # ultimaBatida = (carro.rect.topleft[0], carro.rect.topleft[1], 10, 10)

                if carros[count].collidePoi(BORDA_MASK) is not None:
                    ge[count].fitness -= 10
                    remove_car(count)
                    count -= 1
                    melhorCarro = 0

                if len(redes) != 0:
                    output = redes[count].activate(carros[count].data())

                    actv = 0.9

                    if output[0] > actv:
                        carros[count].turn_right()
                    if output[1] > actv:
                        carros[count].turn_left()
                    if output[0] <= actv and output[1] <= actv:
                        carros[count].no_turn()

                    if output[2] > actv:
                        carros[count].reduz_vel()
                    if output[3] > actv:
                        carros[count].move_fwd()
                    if output[2] <= actv and output[3] <= actv:
                        carros[count].no_turn()

                    carros[count].go()
                    carros[count].draw(TELA)

        def um():
            global recorde, count, ultimaBatida, melhorCarro, dist_covered
            if len(carros) != 0:

                # ge[count].fitness += 0.1
                ge[count].fitness += carros[count].dist_covered / 25

                if recorde < carros[count].dist_covered:
                    recorde = carros[count].dist_covered
                    if carros[count].collidePoi(BORDA_MASK) is not None:
                        ultimaBatida = carros[count].rect.center
                        # ultimaBatida = (carro.rect.topleft[0], carro.rect.topleft[1], 10, 10)

                if carros[count].collidePoi(BORDA_MASK) is not None:
                    ge[count].fitness -= 3
                    remove_car(count)
                    count -= 1
                    melhorCarro = 0

                if len(redes) != 0:
                    output = redes[count].activate(carros[count].data())

                    if output[0] > 0.7:
                        carros[count].turn_right()
                    if output[1] > 0.7:
                        carros[count].turn_left()
                    if output[0] <= 0.7 and output[1] <= 0.7:
                        carros[count].no_turn()

                    if output[2] > 0.7:
                        carros[count].reduz_vel()
                    if output[3] > 0.7:
                        carros[count].move_fwd()
                    if output[2] <= 0.7 and output[3] <= 0.7:
                        carros[count].no_turn()

                    carros[count].go()
                    carros[count].draw(TELA)

        if MODO == 1:
            um()
        elif MODO == 2:
            varios()
        else:
            varios()

        stats()
        clock.tick(ticks)
        pp.display.flip()


# Setup the NEAT Neural Network
def run(config_path):
    global p, winner
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    # p = neat.Checkpointer.restore_checkpoint('checkpoints/neat-checkpoint-999')

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    statistics = neat.StatisticsReporter()
    p.add_reporter(statistics)
    p.add_reporter(neat.Checkpointer(5))

    winner = p.run(eval_genomes, 10000)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)


'''def carrega_ia(config):
    with open("best.pickle", "rb") as f:
        winner = pickle.load(f)
        carrega_ia(winner, config_path)'''

# Start
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'C:/Users/drake/vsCode/PythonProjects/NewAI/config.txt')
    run(config_path)
    # carrega_ia(config_path)
