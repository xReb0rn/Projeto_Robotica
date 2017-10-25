#!/usr/bin/env python3

import ev3dev.ev3 as ev3
from time import sleep

M_ESQUERDO = ev3.LargeMotor('outC')
M_DIREITO = ev3.LargeMotor('outD')
CL = ev3.ColorSensor('in1')
CL.mode = 'COL-COLOR'
PROX1 = ev3.InfraredSensor('in2')  # DIREITA
PROX2 = ev3.InfraredSensor('in3')  # ESQUERDA
PROX1.mode = 'IR-PROX'
PROX2.mode = 'IR-PROX'
GYRO = ev3.GyroSensor('in4')
GYRO.mode = 'TILT-ANG'
log = open("log.txt", "w")

VELOCIDADE_CURVA = 300
VELOCIDADE_ATUAL = 400
KP = 1.5
VERDE = 3
VERMELHO = 5
AZUL = 2
PRETO = 1
lista_valores = [0, 0, 0]  # indice 0 - VERMELHO, indice 1 - VERDE, indice 2 - AZUL
cor_caminho = ["", ""]
cores = ["VERMELHO", "AZUL", "VERDE"]
relacao_cores = {"VERMELHO": "", "VERDE": "", "AZUL": ""}


def corrigir_percurso(valor_distancia1, valor_distancia2):
    # Faz correção do percurso de acordo com os valores de distancia dos sensores
    # e retorna velocidade nova pro motor
    distancia_direita = valor_distancia1
    distancia_esquerda = valor_distancia2
    erro = distancia_direita - distancia_esquerda
    s = KP * erro
    velocidade_nova_dir = VELOCIDADE_ATUAL - s
    velocidade_nova_esq = VELOCIDADE_ATUAL + s

    return velocidade_nova_esq, velocidade_nova_dir


def acelerar(velocidade, tempo=0):
    # Se n receber tempo, roda infinitamente
    if tempo == 0:
        M_ESQUERDO.run_forever(speed_sp=velocidade, stop_action='brake')
        M_DIREITO.run_forever(speed_sp=velocidade, stop_action='brake')
        M_ESQUERDO.wait_while('running')
        M_DIREITO.wait_while('running')
    else:
        M_ESQUERDO.run_timed(time_sp=tempo, speed_sp=velocidade, stop_action='brake')
        M_DIREITO.run_timed(time_sp=tempo, speed_sp=velocidade, stop_action='brake')
        M_ESQUERDO.wait_while('running')
        M_DIREITO.wait_while('running')


def acelerar_ajustando(velocidade_direita, velocidade_esquerda):
    # Acelera infinitamente, mas com velocidade diferente em cada motor
    M_ESQUERDO.run_forever(speed_sp=velocidade_esquerda)
    M_DIREITO.run_forever(speed_sp=velocidade_direita)


def fazer_curva_dir(velocidade):
    # Faz curva pra esquerda no proprio eixo do robo
    M_ESQUERDO.run_forever(speed_sp=velocidade * -1)
    M_DIREITO.run_forever(speed_sp=velocidade)


def fazer_curva_esq(velocidade):
    # Faz curva pra direita no proprio eixo do robo
    M_ESQUERDO.run_forever(speed_sp=velocidade)
    M_DIREITO.run_forever(speed_sp=velocidade * -1)


def cor_preto():
    acelerar(VELOCIDADE_ATUAL, 400)
    ang_atual = GYRO.value()
    while True:
        fazer_curva_dir(VELOCIDADE_CURVA)
        if ang_atual - 175 >= GYRO.value():
            break
    while CL.value() == PRETO:
        # Depois de fazer a curva, enquanto estiver sobre uma cor apenas va em frente
        velocidade_esq, velocidade_dir = corrigir_percurso(PROX1.value(),
                                                           PROX2.value())  # Novos valores de velocidade
        acelerar_ajustando(velocidade_dir, velocidade_esq)


def retornar_cor(cor):
    # Cor anterior = indice 0
    # Cor atual = indice 1

    if cor_caminho[1] != "":
        cor_caminho[0] = cor_caminho[1]
        cor_caminho[1] = cor
    elif cor_caminho[0] == "":
        cor_caminho[1] = cor


def define_direcao(cor):
    if cor == "VERMELHO":
        index = 0
    elif cor == "VERDE":
        index = 1
    else:
        index = 2

    if lista_valores[index] == 1 and "DIREITA" not in relacao_cores.values():
        relacao_cores[cor] = "DIREITA"
    else:
        if lista_valores[index] == 2 or ("ESQUERDA" in relacao_cores.values() and "DIREITA" in relacao_cores.values()):
            relacao_cores[cor] = "MEIO"
        elif lista_valores[index] == 3 or "ESQUERDA" not in relacao_cores.values():
            relacao_cores[cor] = "ESQUERDA"

    ultima_direcao()


def ultima_direcao():
    if "DIREITA" in relacao_cores.values() and "ESQUERDA" in relacao_cores.values():
        ultima_cor("MEIO")
    elif "ESQUERDA" in relacao_cores.values() and "MEIO" in relacao_cores.values():
        ultima_cor("DIREITA")
    elif "DIREITA" in relacao_cores.values() and "MEIO" in relacao_cores.values():
        ultima_cor("ESQUERDA")


def ultima_cor(direcao):
    if relacao_cores["VERMELHO"] != "" and relacao_cores["VERDE"] != "" and relacao_cores["AZUL"] == "":
        relacao_cores["AZUL"] = direcao
    elif relacao_cores["VERMELHO"] != "" and relacao_cores["AZUL"] != "" and relacao_cores["VERDE"] == "":
        relacao_cores["VERDE"] = direcao
    elif relacao_cores["VERDE"] != "" and relacao_cores["AZUL"] != "" and relacao_cores["VERMELHO"] == "":
        relacao_cores["VERMELHO"] = direcao


def curva(sentido):
    # Verifica o caminho que deve seguir
    if sentido == "DIREITA":
        direita()
    elif sentido == "ESQUERDA":
        esquerda()
    else:
        return


def esquerda():
    # Faz curva de 90 graus para a esquerda
    acelerar(VELOCIDADE_ATUAL, 500)
    ang_atual = GYRO.value()
    while True:
        fazer_curva_esq(VELOCIDADE_CURVA)
        if ang_atual + 75 <= GYRO.value():
            return


def direita():
    # Faz curva de 90 graus para direita
    acelerar(VELOCIDADE_ATUAL, 500)
    ang_atual = GYRO.value()
    while True:
        fazer_curva_dir(VELOCIDADE_CURVA)
        if ang_atual - 75 >= GYRO.value():
            return


def aprender_caminho():
    if cor_caminho[0] != "" and cor_caminho[1] in cores and cor_caminho[0] != "PRETO" and relacao_cores[cor_caminho[0]] == "":
        return True


def sem_direcao():
    if "DIREITA" not in relacao_cores.values():
        direita()
    elif "ESQUERDA" not in relacao_cores.values():
        esquerda()
    else:
        return


def percurso():
    while True:
        log.write("%s : %s\n%s : %s\n%s : %s\n" % ("VERMELHO", relacao_cores["VERMELHO"], "VERDE",
                                                   relacao_cores["VERDE"], "AZUL", relacao_cores["AZUL"]))
        velocidade_esq, velocidade_dir = corrigir_percurso(PROX1.value(), PROX2.value())  # Novos valores de velocidade
        acelerar_ajustando(velocidade_dir, velocidade_esq)  # Vai mudando a velocidade do robo durante o percurso
        if CL.value() == VERDE:
            acelerar(VELOCIDADE_ATUAL, 300)
            if not CL.value() == VERDE:
                break
            retornar_cor("VERDE")
            if relacao_cores["VERDE"] == "":
                lista_valores[1] += 1
                condicao = aprender_caminho()
                log.write("linha 176\n")
                if condicao:
                    log.write("linha 178\n")
                    define_direcao(cor_caminho[0])
                    if relacao_cores["VERDE"] != "":
                        curva(relacao_cores["VERDE"])
                    else:
                        sem_direcao()
                    break
                sem_direcao()
            else:
                log.write("linha 183\n")
                curva(relacao_cores["VERDE"])
            break
        elif CL.value() == VERMELHO:  # Vermelho
            acelerar(VELOCIDADE_ATUAL, 300)
            if not CL.value() == VERMELHO:
                break
            retornar_cor("VERMELHO")
            if relacao_cores["VERMELHO"] == "":
                lista_valores[0] += 1
                condicao = aprender_caminho()
                if condicao:
                    define_direcao(cor_caminho[0])
                    if relacao_cores["VERMELHO"] != "":
                        curva(relacao_cores["VERMELHO"])
                    else:
                        sem_direcao()
                    break
                sem_direcao()
            else:
                curva(relacao_cores["VERMELHO"])
            break
        elif CL.value() == AZUL:  # Azul
            acelerar(VELOCIDADE_ATUAL, 300)
            if not CL.value() == AZUL:
                break
            retornar_cor("AZUL")
            if relacao_cores["AZUL"] == "":
                lista_valores[2] += 1
                condicao = aprender_caminho()
                if condicao:
                    log.write("linha 211\n")
                    define_direcao(cor_caminho[0])
                    if relacao_cores["AZUL"] != "":
                        curva(relacao_cores["AZUL"])
                    else:
                        sem_direcao()
                    break
                sem_direcao()
            else:
                curva(relacao_cores["AZUL"])
            break
        elif CL.value() == PRETO:
            sleep(0.2)
            if not CL.value() == PRETO:
                break
            retornar_cor("PRETO")
            cor_preto()
    while (CL.value() == VERMELHO) or (CL.value() == VERDE) or (CL.value() == AZUL):
        # Depois de fazer a curva, enquanto estiver sobre uma cor apenas va em frente
        velocidade_esq, velocidade_dir = corrigir_percurso(PROX1.value(), PROX2.value())  # Novos valores de velocidade
        acelerar_ajustando(velocidade_dir, velocidade_esq)


while True:
    percurso()
    log.write("%d - %d - %d\n" % (lista_valores[0], lista_valores[1], lista_valores[2]))
    log.write("%s - %s\n" % (cor_caminho[0], cor_caminho[1]))
    log.write("%s : %s\n%s : %s\n%s : %s\n" % ("VERMELHO", relacao_cores["VERMELHO"], "VERDE",
                                               relacao_cores["VERDE"], "AZUL", relacao_cores["AZUL"]))
