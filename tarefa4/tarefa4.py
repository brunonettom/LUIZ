import pygame
import sys
import random
import time
import os
import json
import csv
from datetime import datetime

# ==================== CONFIGURAÇÕES PERSONALIZÁVEIS ====================
# Estas configurações podem ser modificadas pelo avaliador

# Parâmetros do experimento
PARTICIPANTE_ID = "anônimo"  # ID padrão caso não seja fornecido
NUM_TENTATIVAS = 100         # Número total de tentativas (padrão: 100)
NUM_BLOCOS = 5               # Número de blocos para análise (padrão: 5)
DINHEIRO_INICIAL = 2000      # Quantidade inicial de dinheiro ($)

# Configuração dos baralhos
# Formato: (recompensa constante, frequência de perda, valores possíveis de perda)

# Baralho A: Desvantajoso - ganho alto, perdas frequentes
BARALHO_A = {
    'recompensa': 100,         # Ganho constante
    'freq_perda': 0.5,         # 50% de chance de perda
    'valores_perda': [150, 200, 250, 300, 350]  # Valores possíveis de perda
}

# Baralho B: Desvantajoso - ganho alto, perdas infrequentes mas grandes
BARALHO_B = {
    'recompensa': 100,
    'freq_perda': 0.1,
    'valores_perda': [1250]
}

# Baralho C: Vantajoso - ganho menor, perdas frequentes mas pequenas
BARALHO_C = {
    'recompensa': 50,
    'freq_perda': 0.5,
    'valores_perda': [25, 50, 75]
}

# Baralho D: Vantajoso - ganho menor, perdas raras e moderadas
BARALHO_D = {
    'recompensa': 50,
    'freq_perda': 0.1,
    'valores_perda': [250]
}

# Configurações visuais
LARGURA_TELA = 1024
ALTURA_TELA = 768
TELA_CHEIA = False
COR_FUNDO = (240, 240, 240)        # Cinza claro
COR_TEXTO = (10, 10, 10)           # Quase preto
COR_BARALHO = (220, 220, 255)      # Azul muito claro
COR_HOVER = (200, 200, 255)        # Azul claro quando hover
COR_BORDA = (70, 70, 140)          # Azul escuro para borda
COR_GANHO = (40, 150, 40)          # Verde para ganhos
COR_PERDA = (200, 40, 40)          # Vermelho para perdas
COR_BOTAO = (200, 200, 220)        # Cinza claro para botões
COR_BOTAO_HOVER = (180, 180, 200)  # Cinza mais escuro para hover de botões

# Tempos
DURACAO_FEEDBACK = 1.5             # Duração da tela de feedback em segundos

# Configurações de dados
SALVAR_DADOS = True
DIRETORIO_DADOS = "dados_igt"

# ===================== FIM DAS CONFIGURAÇÕES =====================

class IowaGamblingTask:
    def __init__(self, participante_id=None, embaralhar_baralhos=False):
        """
        Inicializa o experimento Iowa Gambling Task

        Args:
            participante_id: ID do participante
            embaralhar_baralhos: Se True, embaralha a posição dos baralhos
        """
        # Inicialização do Pygame
        pygame.init()
        pygame.font.init()
        
        # Configuração da tela
        if TELA_CHEIA:
            self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.largura, self.altura = self.tela.get_size()
        else:
            self.largura, self.altura = LARGURA_TELA, ALTURA_TELA
            self.tela = pygame.display.set_mode((self.largura, self.altura))
        
        pygame.display.set_caption("Iowa Gambling Task (IGT)")
        
        # Configuração das fontes
        self.fonte_titulo = pygame.font.SysFont('Arial', 36, bold=True)
        self.fonte_instrucao = pygame.font.SysFont('Arial', 22)
        self.fonte_destaque = pygame.font.SysFont('Arial', 26, bold=True)
        self.fonte_baralho = pygame.font.SysFont('Arial', 60, bold=True)
        self.fonte_feedback = pygame.font.SysFont('Arial', 28, bold=True)
        self.fonte_botao = pygame.font.SysFont('Arial', 20)
        
        # Variáveis do experimento
        self.participante_id = participante_id if participante_id else PARTICIPANTE_ID
        self.dinheiro = DINHEIRO_INICIAL
        self.tentativa_atual = 0
        self.dados = []
        self.tempo_inicio = 0
        self.tempo_reacao = 0
        
        # Configuração dos baralhos
        self.posicoes_baralhos = ['A', 'B', 'C', 'D']
        if embaralhar_baralhos:
            random.shuffle(self.posicoes_baralhos)
            
        # Configuração das propriedades dos baralhos
        self.baralhos = {
            'A': BARALHO_A,
            'B': BARALHO_B,
            'C': BARALHO_C,
            'D': BARALHO_D
        }
        
        # Criar os retângulos dos baralhos
        self.retangulos_baralhos = self._criar_retangulos_baralhos()
        
        # Gerar resultados dos baralhos para todas as tentativas
        self.resultados_baralhos = self._gerar_resultados_baralhos()
        
        # Variáveis de controle de estado
        self.estado = "instrucoes"  # Estados: instrucoes, principal, feedback, resultados
        self.feedback_dados = None
        self.tempo_inicio_feedback = 0
        self.executando = True
        self.relogio = pygame.time.Clock()
        self.escolha_atual = None
        self.botao_continuar = None
        
    def _criar_retangulos_baralhos(self):
        """Cria retângulos para os baralhos na interface"""
        retangulos = {}
        largura_baralho = 160
        altura_baralho = 240
        margem = 40
        largura_total = (largura_baralho * 4) + (margem * 3)
        inicio_x = (self.largura - largura_total) // 2
        y = (self.altura - altura_baralho) // 2
        
        for i, baralho in enumerate(self.posicoes_baralhos):
            x = inicio_x + i * (largura_baralho + margem)
            retangulos[baralho] = pygame.Rect(x, y, largura_baralho, altura_baralho)
        
        return retangulos
    
    def _gerar_resultados_baralhos(self):
        """Gera os resultados dos baralhos para todas as tentativas"""
        resultados = {}
        for baralho, propriedades in self.baralhos.items():
            resultados[baralho] = []
            for _ in range(NUM_TENTATIVAS):
                # Recompensa constante
                recompensa = propriedades['recompensa']
                
                # Determina se há perda baseado na frequência de perda
                perda = 0
                if random.random() < propriedades['freq_perda']:
                    perda = random.choice(propriedades['valores_perda'])
                
                # Resultado líquido
                liquido = recompensa - perda
                resultados[baralho].append((recompensa, perda, liquido))
        
        return resultados
    
    def _desenhar_texto(self, texto, fonte, cor, x, y, alinhamento="centro"):
        """
        Desenha texto na tela
        
        Args:
            texto: O texto a ser desenhado
            fonte: A fonte pygame a ser usada
            cor: A cor do texto em RGB
            x, y: Coordenadas para posicionar o texto
            alinhamento: "esquerda", "centro" ou "direita"
        """
        superficie_texto = fonte.render(texto, True, cor)
        retangulo_texto = superficie_texto.get_rect()
        
        if alinhamento == "esquerda":
            retangulo_texto.topleft = (x, y)
        elif alinhamento == "centro":
            retangulo_texto.center = (x, y)
        elif alinhamento == "direita":
            retangulo_texto.topright = (x, y)
        
        self.tela.blit(superficie_texto, retangulo_texto)
        return retangulo_texto
    
    def _desenhar_tela_instrucoes(self):
        """Desenha a tela de instruções"""
        self.tela.fill(COR_FUNDO)
        
        # Título
        self._desenhar_texto("IOWA GAMBLING TASK", self.fonte_titulo, COR_TEXTO,
                            self.largura//2, 80, "centro")
        
        # Instruções
        instrucoes = [
            "Você participará de um experimento sobre tomada de decisões.",
            "Na próxima tela, você verá quatro baralhos: A, B, C e D.",
            "Em cada tentativa, você escolherá uma carta de qualquer um dos baralhos.",
            "Cada escolha resultará em um ganho de dinheiro.",
            "Às vezes, também haverá uma perda de dinheiro.",
            "Alguns baralhos são melhores que outros a longo prazo.",
            "Seu objetivo é maximizar seus ganhos e terminar com a maior",
            "quantidade de dinheiro possível.",
            "Você começa com $" + str(DINHEIRO_INICIAL) + ".",
            "",
            "Boa sorte!"
        ]
        
        y = 150
        for linha in instrucoes:
            self._desenhar_texto(linha, self.fonte_instrucao, COR_TEXTO,
                                self.largura//2, y, "centro")
            y += 40
        
        # Botão para continuar
        botao_largura, botao_altura = 200, 60
        botao_x = (self.largura - botao_largura) // 2
        botao_y = self.altura - 120
        self.botao_continuar = pygame.Rect(botao_x, botao_y, botao_largura, botao_altura)
        
        mouse_pos = pygame.mouse.get_pos()
        if self.botao_continuar.collidepoint(mouse_pos):
            pygame.draw.rect(self.tela, COR_BOTAO_HOVER, self.botao_continuar, 0, 10)
        else:
            pygame.draw.rect(self.tela, COR_BOTAO, self.botao_continuar, 0, 10)
        
        pygame.draw.rect(self.tela, COR_BORDA, self.botao_continuar, 2, 10)
        self._desenhar_texto("Começar", self.fonte_botao, COR_TEXTO,
                            self.botao_continuar.centerx, self.botao_continuar.centery, "centro")
        
        pygame.display.flip()
    
    def _desenhar_tela_principal(self):
        """Desenha a tela principal com os baralhos"""
        self.tela.fill(COR_FUNDO)
        
        # Informações sobre o dinheiro e tentativa
        self._desenhar_texto(f"Dinheiro: ${self.dinheiro}", self.fonte_destaque, COR_TEXTO,
                            20, 20, "esquerda")
        self._desenhar_texto(f"Tentativa: {self.tentativa_atual + 1}/{NUM_TENTATIVAS}", 
                            self.fonte_instrucao, COR_TEXTO,
                            self.largura - 20, 20, "direita")
        
        # Desenhar os baralhos
        mouse_pos = pygame.mouse.get_pos()
        for baralho, retangulo in self.retangulos_baralhos.items():
            # Verifica se o mouse está sobre o baralho
            if retangulo.collidepoint(mouse_pos):
                pygame.draw.rect(self.tela, COR_HOVER, retangulo, 0, 10)
            else:
                pygame.draw.rect(self.tela, COR_BARALHO, retangulo, 0, 10)
            
            # Desenha a borda
            pygame.draw.rect(self.tela, COR_BORDA, retangulo, 3, 10)
            
            # Desenha a letra do baralho
            self._desenhar_texto(baralho, self.fonte_baralho, COR_TEXTO,
                                retangulo.centerx, retangulo.centery, "centro")
            
            # Desenha o verso da carta
            linhas = 7
            espaco = 25
            for i in range(linhas):
                x1 = retangulo.left + 20
                y1 = retangulo.top + 40 + i * espaco
                x2 = retangulo.right - 20
                y2 = y1
                pygame.draw.line(self.tela, COR_BORDA, (x1, y1), (x2, y2), 2)
        
        # Instrução
        self._desenhar_texto("Selecione um baralho clicando nele", self.fonte_instrucao, COR_TEXTO,
                            self.largura//2, self.altura - 50, "centro")
        
        pygame.display.flip()
        
        # Se for a primeira tentativa, inicia o contador de tempo
        if self.tentativa_atual == 0 and self.tempo_inicio == 0:
            self.tempo_inicio = time.time()
    
    def _desenhar_feedback(self):
        """Desenha a tela de feedback após uma escolha"""
        if self.feedback_dados:
            baralho, recompensa, perda, liquido = self.feedback_dados
            
            # Cria uma sobreposição semitransparente
            sobreposicao = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            sobreposicao.fill((0, 0, 0, 150))  # Preto semitransparente
            self.tela.blit(sobreposicao, (0, 0))
            
            # Painel de feedback
            painel_largura, painel_altura = 500, 300
            painel_x = (self.largura - painel_largura) // 2
            painel_y = (self.altura - painel_altura) // 2
            painel = pygame.Rect(painel_x, painel_y, painel_largura, painel_altura)
            
            # Desenha o painel com cantos arredondados
            pygame.draw.rect(self.tela, COR_FUNDO, painel, 0, 15)
            pygame.draw.rect(self.tela, COR_BORDA, painel, 3, 15)
            
            # Título do feedback
            y = painel_y + 40
            self._desenhar_texto(f"Baralho {baralho}", self.fonte_destaque, COR_TEXTO,
                                self.largura//2, y, "centro")
            
            # Resultados
            y += 60
            self._desenhar_texto(f"Ganho: +${recompensa}", self.fonte_feedback, COR_GANHO,
                                self.largura//2, y, "centro")
            
            y += 50
            if perda > 0:
                self._desenhar_texto(f"Perda: -${perda}", self.fonte_feedback, COR_PERDA,
                                    self.largura//2, y, "centro")
            else:
                self._desenhar_texto("Sem perdas", self.fonte_feedback, COR_TEXTO,
                                    self.largura//2, y, "centro")
            
            # Resultado líquido
            y += 50
            cor_resultado = COR_GANHO if liquido >= 0 else COR_PERDA
            prefixo = "+" if liquido >= 0 else ""
            self._desenhar_texto(f"Resultado: {prefixo}${liquido}", self.fonte_feedback, cor_resultado,
                                self.largura//2, y, "centro")
            
            # Atualização total
            y += 50
            self._desenhar_texto(f"Total: ${self.dinheiro}", self.fonte_feedback, COR_TEXTO,
                                self.largura//2, y, "centro")
            
            pygame.display.flip()
            
            # Verifica se o tempo de exibição do feedback acabou
            tempo_atual = time.time()
            if tempo_atual - self.tempo_inicio_feedback >= DURACAO_FEEDBACK:
                self.estado = "principal"
                self.feedback_dados = None
    
    def _desenhar_resultados(self):
        """Desenha a tela de resultados finais"""
        self.tela.fill(COR_FUNDO)
        
        # Calcula os resultados
        resultados = self._calcular_resultados()
        
        # Título
        self._desenhar_texto("RESULTADOS", self.fonte_titulo, COR_TEXTO,
                            self.largura//2, 60, "centro")
        
        # Dinheiro final
        y = 130
        self._desenhar_texto(f"Dinheiro Final: ${self.dinheiro}", self.fonte_destaque, COR_TEXTO,
                            self.largura//2, y, "centro")
        
        # Escolhas por baralho
        y += 70
        self._desenhar_texto("Escolhas por Baralho:", self.fonte_instrucao, COR_TEXTO,
                            self.largura//2, y, "centro")
        
        y += 40
        for baralho in ['A', 'B', 'C', 'D']:
            contagem = resultados['escolhas_baralho'].get(baralho, 0)
            tipo = "(desvantajoso)" if baralho in ['A', 'B'] else "(vantajoso)"
            self._desenhar_texto(f"Baralho {baralho} {tipo}: {contagem} escolhas", 
                                self.fonte_instrucao, COR_TEXTO,
                                self.largura//2, y, "centro")
            y += 30
        
        # Pontuação líquida
        y += 20
        self._desenhar_texto(f"Pontuação Líquida: {resultados['pontuacao_liquida']}", 
                            self.fonte_destaque, COR_TEXTO,
                            self.largura//2, y, "centro")
        
        # Pontuações por bloco
        y += 50
        self._desenhar_texto("Pontuações por Bloco:", self.fonte_instrucao, COR_TEXTO,
                            self.largura//2, y, "centro")
        
        y += 30
        for i, pontuacao in enumerate(resultados['pontuacoes_bloco']):
            self._desenhar_texto(f"Bloco {i+1}: {pontuacao}", self.fonte_instrucao, COR_TEXTO,
                                self.largura//2, y, "centro")
            y += 30
        
        # Botão para finalizar
        botao_largura, botao_altura = 200, 60
        botao_x = (self.largura - botao_largura) // 2
        botao_y = self.altura - 100
        self.botao_continuar = pygame.Rect(botao_x, botao_y, botao_largura, botao_altura)
        
        mouse_pos = pygame.mouse.get_pos()
        if self.botao_continuar.collidepoint(mouse_pos):
            pygame.draw.rect(self.tela, COR_BOTAO_HOVER, self.botao_continuar, 0, 10)
        else:
            pygame.draw.rect(self.tela, COR_BOTAO, self.botao_continuar, 0, 10)
        
        pygame.draw.rect(self.tela, COR_BORDA, self.botao_continuar, 2, 10)
        self._desenhar_texto("Finalizar", self.fonte_botao, COR_TEXTO,
                            self.botao_continuar.centerx, self.botao_continuar.centery, "centro")
        
        pygame.display.flip()
    
    def _calcular_resultados(self):
        """
        Calcula os resultados do experimento
        
        Returns:
            dict: Dicionário com os resultados
        """
        resultados = {
            'escolhas_baralho': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
            'pontuacao_liquida': 0,
            'pontuacoes_bloco': [0] * NUM_BLOCOS
        }
        
        # Conta escolhas por baralho
        for dado in self.dados:
            baralho = dado['baralho']
            resultados['escolhas_baralho'][baralho] = resultados['escolhas_baralho'].get(baralho, 0) + 1
        
        # Calcula pontuação líquida (vantajosos - desvantajosos)
        vantajosos = resultados['escolhas_baralho'].get('C', 0) + resultados['escolhas_baralho'].get('D', 0)
        desvantajosos = resultados['escolhas_baralho'].get('A', 0) + resultados['escolhas_baralho'].get('B', 0)
        resultados['pontuacao_liquida'] = vantajosos - desvantajosos
        
        # Calcula pontuações por bloco
        tentativas_por_bloco = NUM_TENTATIVAS // NUM_BLOCOS
        for i, dado in enumerate(self.dados):
            if i < NUM_TENTATIVAS:  # Garante que não ultrapasse o número de tentativas
                bloco = i // tentativas_por_bloco
                if bloco < NUM_BLOCOS:  # Garante que não ultrapasse o número de blocos
                    baralho = dado['baralho']
                    if baralho in ['C', 'D']:  # Vantajoso
                        resultados['pontuacoes_bloco'][bloco] += 1
                    elif baralho in ['A', 'B']:  # Desvantajoso
                        resultados['pontuacoes_bloco'][bloco] -= 1
        
        return resultados
    
    def _salvar_dados(self):
        """Salva os dados do experimento em arquivos CSV e JSON"""
        if not SALVAR_DADOS:
            return
        
        # Cria diretório de dados se não existir
        if not os.path.exists(DIRETORIO_DADOS):
            os.makedirs(DIRETORIO_DADOS)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = f"{DIRETORIO_DADOS}/igt_{self.participante_id}_{timestamp}"
        
        # Salva dados brutos em CSV
        with open(f"{basename}_dados.csv", 'w', newline='', encoding='utf-8') as csvfile:
            campos = ['tentativa', 'baralho', 'recompensa', 'perda', 'liquido', 
                      'dinheiro_total', 'tempo_reacao']
            writer = csv.DictWriter(csvfile, fieldnames=campos)
            
            writer.writeheader()
            for dado in self.dados:
                writer.writerow({
                    'tentativa': dado['tentativa'],
                    'baralho': dado['baralho'],
                    'recompensa': dado['recompensa'],
                    'perda': dado['perda'],
                    'liquido': dado['liquido'],
                    'dinheiro_total': dado['dinheiro_total'],
                    'tempo_reacao': dado['tempo_reacao']
                })
        
        # Salva resultados em JSON
        resultados = self._calcular_resultados()
        resultados['participante_id'] = self.participante_id
        resultados['dinheiro_final'] = self.dinheiro
        resultados['posicoes_baralhos'] = self.posicoes_baralhos
        resultados['configuracoes'] = {
            'NUM_TENTATIVAS': NUM_TENTATIVAS,
            'NUM_BLOCOS': NUM_BLOCOS,
            'DINHEIRO_INICIAL': DINHEIRO_INICIAL,
            'BARALHO_A': BARALHO_A,
            'BARALHO_B': BARALHO_B,
            'BARALHO_C': BARALHO_C,
            'BARALHO_D': BARALHO_D
        }
        
        with open(f"{basename}_resultados.json", 'w', encoding='utf-8') as jsonfile:
            json.dump(resultados, jsonfile, indent=4, ensure_ascii=False)
        
        print(f"Dados salvos em {basename}_dados.csv")
        print(f"Resultados salvos em {basename}_resultados.json")
    
    def _processar_eventos_instrucoes(self):
        """Processa eventos na tela de instruções"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.executando = False
                elif evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN:
                    self.estado = "principal"
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.botao_continuar and self.botao_continuar.collidepoint(evento.pos):
                    self.estado = "principal"
    
    def _processar_eventos_principal(self):
        """Processa eventos na tela principal"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.executando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for baralho, retangulo in self.retangulos_baralhos.items():
                    if retangulo.collidepoint(mouse_pos):
                        self._processar_escolha(baralho)
                        break
    
    def _processar_eventos_resultados(self):
        """Processa eventos na tela de resultados"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.executando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_SPACE:
                    self.executando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if self.botao_continuar and self.botao_continuar.collidepoint(evento.pos):
                    self.executando = False
    
    def _processar_escolha(self, baralho):
        """
        Processa a escolha de um baralho
        
        Args:
            baralho: O baralho escolhido ('A', 'B', 'C' ou 'D')
        """
        # Calcula o tempo de reação
        tempo_atual = time.time()
        self.tempo_reacao = tempo_atual - self.tempo_inicio
        self.tempo_inicio = tempo_atual  # Reseta para a próxima tentativa
        
        # Obtém o resultado para esta tentativa
        recompensa, perda, liquido = self.resultados_baralhos[baralho][self.tentativa_atual]
        
        # Atualiza o dinheiro
        self.dinheiro += liquido
        
        # Registra os dados
        dados_tentativa = {
            'tentativa': self.tentativa_atual + 1,
            'baralho': baralho,
            'recompensa': recompensa,
            'perda': perda,
            'liquido': liquido,
            'dinheiro_total': self.dinheiro,
            'tempo_reacao': round(self.tempo_reacao, 3)
        }
        self.dados.append(dados_tentativa)
        
        # Configura o feedback
        self.feedback_dados = (baralho, recompensa, perda, liquido)
        self.tempo_inicio_feedback = time.time()
        self.estado = "feedback"
        
        # Avança para a próxima tentativa
        self.tentativa_atual += 1
        
        # Verifica se o experimento terminou
        if self.tentativa_atual >= NUM_TENTATIVAS:
            self.estado = "resultados"
    
    def executar(self):
        """Executa o loop principal do experimento"""
        while self.executando:
            if self.estado == "instrucoes":
                self._desenhar_tela_instrucoes()
                self._processar_eventos_instrucoes()
            elif self.estado == "principal":
                self._desenhar_tela_principal()
                self._processar_eventos_principal()
            elif self.estado == "feedback":
                self._desenhar_feedback()
                # Eventos não são processados durante o feedback (timeout automático)
            elif self.estado == "resultados":
                self._desenhar_resultados()
                self._processar_eventos_resultados()
            
            self.relogio.tick(60)  # Limita a 60 FPS
        
        # Salva os dados antes de sair
        if len(self.dados) > 0:
            self._salvar_dados()
        
        pygame.quit()
        return len(self.dados) == NUM_TENTATIVAS  # Retorna True se concluiu todas as tentativas


def obter_info_participante():
    """Obtém informações do participante via linha de comando"""
    print("\n=== Iowa Gambling Task (IGT) ===\n")
    
    # Obtém ID do participante
    if len(sys.argv) > 1:
        participante_id = sys.argv[1]
    else:
        participante_id = input("ID do Participante: ")
        if not participante_id:
            participante_id = "anônimo"
    
    # Pergunta se deve embaralhar os baralhos
    embaralhar = input("Embaralhar posições dos baralhos? (s/n): ").lower().startswith('s')
    
    return participante_id, embaralhar


if __name__ == "__main__":
    participante_id, embaralhar_baralhos = obter_info_participante()
    
    experimento = IowaGamblingTask(participante_id, embaralhar_baralhos)
    concluido = experimento.executar()
    
    if concluido:
        print("\nExperimento concluído com sucesso!")
    else:
        print("\nExperimento interrompido antes do término.")
