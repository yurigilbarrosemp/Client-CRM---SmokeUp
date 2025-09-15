import sys
import sqlite3
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QScrollArea,
                             QGroupBox, QDateEdit, QTextEdit, QComboBox, QFrame,
                             QGridLayout, QCheckBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSystemTrayIcon, QMenu, QAction, QDialog,
                             QInputDialog, QListWidget, QListWidgetItem, QSplitter)
from PyQt5.QtCore import Qt, QDate, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QPainter, QPen
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os
import json
from plyer import notification

class DatabaseManager:
    def __init__(self):
        self.db_name = "tabacaria_crm.db"
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabela de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                data_nascimento DATE,
                data_cadastro DATE,
                preferencias TEXT,
                observacoes TEXT,
                fumante_ativo INTEGER DEFAULT 1,
                total_gasto REAL DEFAULT 0
            )
        ''')
        
        # Tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT,
                preco REAL
            )
        ''')
        
        # Tabela de compras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                produto_id INTEGER,
                data_compra DATE,
                quantidade INTEGER,
                valor_total REAL,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        ''')
        
        # Tabela de notificações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                mensagem TEXT,
                data_notificacao DATE,
                tipo TEXT,
                cliente_id INTEGER,
                lida INTEGER DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        # Inserir alguns produtos de exemplo
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            produtos_exemplo = [
                ('Cigarro Marlboro', 'Cigarro', 10.00),
                ('Cigarro Camel', 'Cigarro', 9.50),
                ('Charuto Cubano', 'Charuto', 45.00),
                ('Fumo de Corda', 'Fumo', 8.00),
                ('Cigarro Parliament', 'Cigarro', 11.00),
                ('Narguilé', 'Acessório', 120.00),
                ('Isqueiro Zippo', 'Acessório', 85.00)
            ]
            cursor.executemany('INSERT INTO produtos (nome, categoria, preco) VALUES (?, ?, ?)', produtos_exemplo)
        
        conn.commit()
        conn.close()
    
    def add_cliente(self, cliente_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clientes 
            (nome, telefone, email, data_nascimento, data_cadastro, preferencias, observacoes, fumante_ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', cliente_data)
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def update_cliente(self, cliente_id, cliente_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE clientes 
            SET nome=?, telefone=?, email=?, data_nascimento=?, preferencias=?, observacoes=?, fumante_ativo=?
            WHERE id=?
        ''', (*cliente_data, cliente_id))
        
        conn.commit()
        conn.close()
    
    def get_clientes(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clientes ORDER BY nome')
        clientes = cursor.fetchall()
        
        conn.close()
        return clientes
    
    def get_cliente(self, cliente_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,))
        cliente = cursor.fetchone()
        
        conn.close()
        return cliente
    
    def search_clientes(self, termo):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM clientes 
            WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ?
            ORDER BY nome
        ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%'))
        
        clientes = cursor.fetchall()
        conn.close()
        return clientes
    
    def add_compra(self, compra_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compras 
            (cliente_id, produto_id, data_compra, quantidade, valor_total)
            VALUES (?, ?, ?, ?, ?)
        ''', compra_data)
        
        # Atualizar o total gasto pelo cliente
        cursor.execute('''
            UPDATE clientes 
            SET total_gasto = total_gasto + ?
            WHERE id = ?
        ''', (compra_data[4], compra_data[0]))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_compras_cliente(self, cliente_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.data_compra, p.nome, c.quantidade, c.valor_total 
            FROM compras c
            JOIN produtos p ON c.produto_id = p.id
            WHERE c.cliente_id = ?
            ORDER BY c.data_compra DESC
        ''', (cliente_id,))
        
        compras = cursor.fetchall()
        conn.close()
        return compras
    
    def get_produtos(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM produtos ORDER BY nome')
        produtos = cursor.fetchall()
        
        conn.close()
        return produtos
    
    def add_notificacao(self, notificacao_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notificacoes 
            (titulo, mensagem, data_notificacao, tipo, cliente_id)
            VALUES (?, ?, ?, ?, ?)
        ''', notificacao_data)
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_notificacoes_hoje(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        hoje = date.today().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT * FROM notificacoes 
            WHERE data_notificacao = ? AND lida = 0
            ORDER BY id DESC
        ''', (hoje,))
        
        notificacoes = cursor.fetchall()
        conn.close()
        return notificacoes
    
    def get_aniversariantes_mes(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        mes_atual = date.today().month
        cursor.execute('''
            SELECT id, nome, data_nascimento 
            FROM clientes 
            WHERE CAST(substr(data_nascimento, 6, 2) AS INTEGER) = ?
            ORDER BY CAST(substr(data_nascimento, 9, 2) AS INTEGER)
        ''', (mes_atual,))
        
        aniversariantes = cursor.fetchall()
        conn.close()
        return aniversariantes
    
    def marcar_notificacao_lida(self, notificacao_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notificacoes 
            SET lida = 1 
            WHERE id = ?
        ''', (notificacao_id,))
        
        conn.commit()
        conn.close()

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
            }
        """)

class ClientCard(QFrame):
    def __init__(self, cliente_data, parent=None):
        super().__init__(parent)
        self.cliente_data = cliente_data
        self.parent_ref = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Nome do cliente
        nome_label = QLabel(self.cliente_data[1])
        nome_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(nome_label)
        
        # Informações de contato
        if self.cliente_data[2]:  # Telefone
            telefone_label = QLabel(f"📞 {self.cliente_data[2]}")
            layout.addWidget(telefone_label)
        
        if self.cliente_data[3]:  # Email
            email_label = QLabel(f"✉️ {self.cliente_data[3]}")
            layout.addWidget(email_label)
        
        # Data de nascimento
        if self.cliente_data[4]:
            nascimento_label = QLabel(f"🎂 {self.cliente_data[4]}")
            layout.addWidget(nascimento_label)
        
        # Total gasto
        total_gasto = self.cliente_data[9] or 0
        total_label = QLabel(f"💰 Total gasto: R$ {total_gasto:.2f}")
        total_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        layout.addWidget(total_label)
        
        # Status
        status = "Ativo" if self.cliente_data[8] == 1 else "Inativo"
        status_color = "#27ae60" if self.cliente_data[8] == 1 else "#e74c3c"
        status_label = QLabel(f"Status: {status}")
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        layout.addWidget(status_label)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        btn_editar = QPushButton("Editar")
        btn_editar.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 5px; border-radius: 3px; }")
        btn_editar.clicked.connect(self.editar_cliente)
        btn_layout.addWidget(btn_editar)
        
        btn_compras = QPushButton("Compras")
        btn_compras.setStyleSheet("QPushButton { background-color: #2ecc71; color: white; border: none; padding: 5px; border-radius: 3px; }")
        btn_compras.clicked.connect(self.ver_compras)
        btn_layout.addWidget(btn_compras)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def editar_cliente(self):
        self.parent_ref.abrir_edicao_cliente(self.cliente_data[0])
    
    def ver_compras(self):
        self.parent_ref.ver_compras_cliente(self.cliente_data[0])

class NotificationDialog(QDialog):
    def __init__(self, notificacoes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notificações")
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        for notif in notificacoes:
            item = QListWidgetItem(f"{notif[1]} - {notif[2]}")
            item.setData(Qt.UserRole, notif[0])  # ID da notificação
            self.list_widget.addItem(item)
        
        layout.addWidget(QLabel("Notificações do dia:"))
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.marcar_como_lida)
        btn_layout.addWidget(btn_ok)
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.close)
        btn_layout.addWidget(btn_fechar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def marcar_como_lida(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            notif_id = current_item.data(Qt.UserRole)
            self.parent().db.marcar_notificacao_lida(notif_id)
            self.list_widget.takeItem(self.list_widget.row(current_item))

class BirthdayWidget(QWidget):
    def __init__(self, aniversariantes, parent=None):
        super().__init__(parent)
        self.aniversariantes = aniversariantes
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Aniversariantes do Mês")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(title)
        
        if not self.aniversariantes:
            layout.addWidget(QLabel("Nenhum aniversariante este mês."))
        else:
            for aniv in self.aniversariantes:
                # Calcular idade
                nascimento = datetime.strptime(aniv[2], "%Y-%m-%d").date()
                hoje = date.today()
                idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
                
                # Calcular dias até o aniversário
                next_birthday = date(hoje.year, nascimento.month, nascimento.day)
                if next_birthday < hoje:
                    next_birthday = date(hoje.year + 1, nascimento.month, nascimento.day)
                
                dias_restantes = (next_birthday - hoje).days
                
                frame = QFrame()
                frame.setFrameShape(QFrame.StyledPanel)
                frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 5px; padding: 5px; }")
                frame_layout = QHBoxLayout()
                
                info_label = QLabel(f"{aniv[1]} - {nascimento.day}/{nascimento.month} ({idade} anos)")
                frame_layout.addWidget(info_label)
                
                days_label = QLabel(f"{dias_restantes} dias")
                days_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                frame_layout.addWidget(days_label)
                
                frame.setLayout(frame_layout)
                layout.addWidget(frame)
        
        layout.addStretch()
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
        self.setup_tray_icon()
        self.verificar_notificacoes()
        
        # Configurar timer para verificar notificações periodicamente
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_notificacoes)
        self.timer.start(300000)  # Verificar a cada 5 minutos
        
    def init_ui(self):
        self.setWindowTitle('Tabacaria CRM - Sistema de Fidelização')
        self.setGeometry(100, 100, 1200, 800)
        
        # Configurar layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Criar splitter para divisão de área
        splitter = QSplitter(Qt.Horizontal)
        
        # Área principal com abas
        main_area = QWidget()
        main_area_layout = QVBoxLayout(main_area)
        
        # Criar abas
        self.tabs = QTabWidget()
        main_area_layout.addWidget(self.tabs)
        
        # Adicionar abas
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self.create_cadastro_tab(), "Cadastro")
        self.tabs.addTab(self.create_clientes_tab(), "Clientes")
        self.tabs.addTab(self.create_vendas_tab(), "Vendas")
        self.tabs.addTab(self.create_relatorios_tab(), "Relatórios")
        self.tabs.addTab(self.create_configuracoes_tab(), "Configurações")
        
        # Área lateral para aniversariantes
        side_widget = QWidget()
        side_widget.setMaximumWidth(300)
        side_layout = QVBoxLayout(side_widget)
        
        # Widget de aniversariantes
        aniversariantes = self.db.get_aniversariantes_mes()
        self.birthday_widget = BirthdayWidget(aniversariantes, self)
        side_layout.addWidget(self.birthday_widget)
        
        # Adicionar widgets ao splitter
        splitter.addWidget(main_area)
        splitter.addWidget(side_widget)
        splitter.setSizes([800, 200])
        
        main_layout.addWidget(splitter)
        
        # Aplicar estilo
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background: white;
            }
            QTabBar::tab {
                background: #95a5a6;
                color: white;
                padding: 10px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #34495e;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit, QDateEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = QAction("Abrir", self)
        quit_action = QAction("Sair", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def verificar_notificacoes(self):
        notificacoes = self.db.get_notificacoes_hoje()
        
        # Verificar aniversários para hoje
        hoje = date.today().strftime("%m-%d")
        clientes = self.db.get_clientes()
        
        for cliente in clientes:
            if cliente[4] and cliente[4][5:] == hoje:
                # É aniversário deste cliente
                titulo = "Aniversário do Cliente"
                mensagem = f"Hoje é aniversário de {cliente[1]}. Que tal enviar uma mensagem de parabéns?"
                
                # Verificar se já notificamos hoje
                notificacao_existe = any(n[4] == "aniversario" and n[5] == cliente[0] for n in notificacoes)
                
                if not notificacao_existe:
                    self.db.add_notificacao((
                        titulo, 
                        mensagem, 
                        date.today().strftime("%Y-%m-%d"), 
                        "aniversario", 
                        cliente[0]
                    ))
                    
                    # Mostrar notificação do sistema
                    try:
                        notification.notify(
                            title=titulo,
                            message=mensagem,
                            app_name="Tabacaria CRM",
                            timeout=10
                        )
                    except:
                        pass  # Ignora erros se notificação do sistema não funcionar
        
        # Buscar notificações atualizadas
        notificacoes = self.db.get_notificacoes_hoje()
        
        if notificacoes:
            self.tray_icon.showMessage(
                "Tabacaria CRM - Notificações",
                f"Você tem {len(notificacoes)} notificação(ões) hoje",
                QSystemTrayIcon.Information,
                2000
            )
            
            # Mostrar diálogo de notificações se a janela estiver visível
            if self.isVisible():
                self.mostrar_dialogo_notificacoes(notificacoes)
    
    def mostrar_dialogo_notificacoes(self, notificacoes):
        dialog = NotificationDialog(notificacoes, self)
        dialog.exec_()
    
    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Resumo do negócio
        resumo_group = QGroupBox("Resumo do Negócio")
        resumo_layout = QGridLayout()
        
        # Estatísticas
        clientes = self.db.get_clientes()
        total_clientes = len(clientes)
        clientes_ativos = len([c for c in clientes if c[8] == 1])
        total_vendas = sum(c[9] or 0 for c in clientes)
        
        resumo_layout.addWidget(QLabel("Total de Clientes:"), 0, 0)
        resumo_layout.addWidget(QLabel(f"{total_clientes}"), 0, 1)
        
        resumo_layout.addWidget(QLabel("Clientes Ativos:"), 1, 0)
        resumo_layout.addWidget(QLabel(f"{clientes_ativos}"), 1, 1)
        
        resumo_layout.addWidget(QLabel("Faturamento Total:"), 2, 0)
        resumo_layout.addWidget(QLabel(f"R$ {total_vendas:.2f}"), 2, 1)
        
        resumo_group.setLayout(resumo_layout)
        layout.addWidget(resumo_group)
        
        # Gráfico de clientes por status
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        
        # Dados para o gráfico
        status = ['Ativos', 'Inativos']
        quantidades = [clientes_ativos, total_clientes - clientes_ativos]
        cores = ['#2ecc71', '#e74c3c']
        
        ax = figure.add_subplot(111)
        ax.bar(status, quantidades, color=cores)
        ax.set_title('Clientes por Status')
        ax.set_ylabel('Quantidade')
        
        layout.addWidget(canvas)
        
        return tab
    
    def create_cadastro_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário de cadastro
        form_group = QGroupBox("Cadastro de Cliente")
        form_layout = QFormLayout()
        
        self.nome_input = QLineEdit()
        self.telefone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.data_nascimento_input = QDateEdit()
        self.data_nascimento_input.setCalendarPopup(True)
        self.data_nascimento_input.setDate(QDate(1990, 1, 1))
        
        self.preferencias_input = QTextEdit()
        self.observacoes_input = QTextEdit()
        self.fumante_ativo_check = QCheckBox("Cliente fumante ativo")
        self.fumante_ativo_check.setChecked(True)
        
        form_layout.addRow("Nome completo:", self.nome_input)
        form_layout.addRow("Telefone:", self.telefone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Data de nascimento:", self.data_nascimento_input)
        form_layout.addRow("Preferências:", self.preferencias_input)
        form_layout.addRow("Observações:", self.observacoes_input)
        form_layout.addRow("", self.fumante_ativo_check)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Botão de cadastro
        btn_cadastrar = ModernButton("Cadastrar Cliente")
        btn_cadastrar.clicked.connect(self.cadastrar_cliente)
        layout.addWidget(btn_cadastrar)
        
        return tab
    
    def create_clientes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Barra de pesquisa
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar clientes...")
        self.search_input.textChanged.connect(self.pesquisar_clientes)
        btn_pesquisar = ModernButton("Pesquisar")
        btn_pesquisar.clicked.connect(self.pesquisar_clientes)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_pesquisar)
        layout.addLayout(search_layout)
        
        # Área de scroll para os cards
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.cards_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Carregar clientes inicialmente
        self.carregar_clientes()
        
        return tab
    
    def create_vendas_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário de venda
        form_group = QGroupBox("Registrar Venda")
        form_layout = QFormLayout()
        
        # Cliente
        self.venda_cliente_combo = QComboBox()
        self.carregar_clientes_combo()
        form_layout.addRow("Cliente:", self.venda_cliente_combo)
        
        # Produto
        self.venda_produto_combo = QComboBox()
        self.carregar_produtos_combo()
        form_layout.addRow("Produto:", self.venda_produto_combo)
        
        # Quantidade
        self.venda_quantidade = QLineEdit("1")
        form_layout.addRow("Quantidade:", self.venda_quantidade)
        
        # Data
        self.venda_data = QDateEdit()
        self.venda_data.setCalendarPopup(True)
        self.venda_data.setDate(QDate.currentDate())
        form_layout.addRow("Data da venda:", self.venda_data)
        
        # Valor (calculado automaticamente)
        self.venda_valor = QLabel("R$ 0.00")
        self.venda_produto_combo.currentIndexChanged.connect(self.calcular_valor_venda)
        self.venda_quantidade.textChanged.connect(self.calcular_valor_venda)
        form_layout.addRow("Valor total:", self.venda_valor)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Botão de registrar venda
        btn_registrar = ModernButton("Registrar Venda")
        btn_registrar.clicked.connect(self.registrar_venda)
        layout.addWidget(btn_registrar)
        
        return tab
    
    def create_relatorios_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtros
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        self.relatorio_mes_combo = QComboBox()
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        self.relatorio_mes_combo.addItems(meses)
        self.relatorio_mes_combo.setCurrentIndex(date.today().month - 1)
        
        self.relatorio_ano = QLineEdit(str(date.today().year))
        
        btn_gerar = ModernButton("Gerar Relatório")
        btn_gerar.clicked.connect(self.gerar_relatorio)
        
        filtros_layout.addWidget(QLabel("Mês:"))
        filtros_layout.addWidget(self.relatorio_mes_combo)
        filtros_layout.addWidget(QLabel("Ano:"))
        filtros_layout.addWidget(self.relatorio_ano)
        filtros_layout.addWidget(btn_gerar)
        filtros_layout.addStretch()
        
        filtros_group.setLayout(filtros_layout)
        layout.addWidget(filtros_group)
        
        # Área do relatório
        self.relatorio_area = QTextEdit()
        self.relatorio_area.setReadOnly(True)
        layout.addWidget(self.relatorio_area)
        
        return tab
    
    def create_configuracoes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel("Configurações do Sistema")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(label)
        
        # Opções de configuração
        config_group = QGroupBox("Opções")
        config_layout = QFormLayout()
        
        self.notificacoes_check = QCheckBox("Ativar notificações")
        self.notificacoes_check.setChecked(True)
        config_layout.addRow(self.notificacoes_check)
        
        self.backup_dias = QComboBox()
        self.backup_dias.addItems(["Diário", "Semanal", "Mensal"])
        config_layout.addRow("Frequência de backup:", self.backup_dias)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Botões de ação
        backup_btn = ModernButton("Fazer Backup do Banco de Dados")
        backup_btn.clicked.connect(self.fazer_backup)
        
        restore_btn = ModernButton("Restaurar Backup")
        restore_btn.clicked.connect(self.restaurar_backup)
        
        notificacoes_btn = ModernButton("Ver Notificações")
        notificacoes_btn.clicked.connect(self.ver_notificacoes)
        
        layout.addWidget(backup_btn)
        layout.addWidget(restore_btn)
        layout.addWidget(notificacoes_btn)
        layout.addStretch()
        
        return tab
    
    def carregar_clientes_combo(self):
        clientes = self.db.get_clientes()
        self.venda_cliente_combo.clear()
        for cliente in clientes:
            self.venda_cliente_combo.addItem(cliente[1], cliente[0])
    
    def carregar_produtos_combo(self):
        produtos = self.db.get_produtos()
        self.venda_produto_combo.clear()
        for produto in produtos:
            self.venda_produto_combo.addItem(f"{produto[1]} - R$ {produto[3]:.2f}", produto[0])
    
    def calcular_valor_venda(self):
        try:
            produto_id = self.venda_produto_combo.currentData()
            quantidade = int(self.venda_quantidade.text())
            
            produtos = self.db.get_produtos()
            produto = next((p for p in produtos if p[0] == produto_id), None)
            
            if produto:
                valor_total = produto[3] * quantidade
                self.venda_valor.setText(f"R$ {valor_total:.2f}")
        except:
            self.venda_valor.setText("R$ 0.00")
    
    def cadastrar_cliente(self):
        # Coletar dados do formulário
        nome = self.nome_input.text().strip()
        telefone = self.telefone_input.text().strip()
        email = self.email_input.text().strip()
        data_nascimento = self.data_nascimento_input.date().toString("yyyy-MM-dd")
        data_cadastro = QDate.currentDate().toString("yyyy-MM-dd")
        preferencias = self.preferencias_input.toPlainText().strip()
        observacoes = self.observacoes_input.toPlainText().strip()
        fumante_ativo = 1 if self.fumante_ativo_check.isChecked() else 0
        
        # Validar dados
        if not nome:
            QMessageBox.warning(self, "Aviso", "O nome do cliente é obrigatório!")
            return
        
        # Preparar dados para inserção
        cliente_data = (nome, telefone, email, data_nascimento, data_cadastro, 
                       preferencias, observacoes, fumante_ativo)
        
        try:
            # Inserir no banco de dados
            self.db.add_cliente(cliente_data)
            
            # Limpar formulário
            self.nome_input.clear()
            self.telefone_input.clear()
            self.email_input.clear()
            self.data_nascimento_input.setDate(QDate(1990, 1, 1))
            self.preferencias_input.clear()
            self.observacoes_input.clear()
            self.fumante_ativo_check.setChecked(True)
            
            QMessageBox.information(self, "Sucesso", "Cliente cadastrado com sucesso!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar cliente: {str(e)}")
    
    def carregar_clientes(self):
        # Limpar layout atual
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Buscar clientes no banco
        clientes = self.db.get_clientes()
        
        if not clientes:
            label = QLabel("Nenhum cliente cadastrado.")
            label.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(label)
            return
        
        # Adicionar cards para cada cliente
        for cliente in clientes:
            card = ClientCard(cliente, self)
            self.cards_layout.addWidget(card)
        
        # Adicionar espaço no final
        self.cards_layout.addStretch()
    
    def pesquisar_clientes(self):
        termo = self.search_input.text().strip()
        
        # Limpar layout atual
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Buscar clientes com o termo
        if termo:
            clientes = self.db.search_clientes(termo)
        else:
            clientes = self.db.get_clientes()
        
        if not clientes:
            label = QLabel("Nenhum cliente encontrado.")
            label.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(label)
            return
        
        # Adicionar cards para cada cliente encontrado
        for cliente in clientes:
            card = ClientCard(cliente, self)
            self.cards_layout.addWidget(card)
        
        # Adicionar espaço no final
        self.cards_layout.addStretch()
    
    def registrar_venda(self):
        cliente_id = self.venda_cliente_combo.currentData()
        produto_id = self.venda_produto_combo.currentData()
        data_compra = self.venda_data.date().toString("yyyy-MM-dd")
        
        try:
            quantidade = int(self.venda_quantidade.text())
        except:
            QMessageBox.warning(self, "Aviso", "Quantidade deve ser um número válido!")
            return
        
        # Calcular valor total
        produtos = self.db.get_produtos()
        produto = next((p for p in produtos if p[0] == produto_id), None)
        
        if not produto:
            QMessageBox.warning(self, "Aviso", "Produto não encontrado!")
            return
        
        valor_total = produto[3] * quantidade
        
        # Preparar dados para inserção
        compra_data = (cliente_id, produto_id, data_compra, quantidade, valor_total)
        
        try:
            # Inserir no banco de dados
            self.db.add_compra(compra_data)
            
            # Criar notificação
            cliente = self.db.get_cliente(cliente_id)
            produto_nome = produto[1]
            
            titulo = "Nova venda registrada"
            mensagem = f"Venda de {quantidade}x {produto_nome} para {cliente[1]} no valor de R$ {valor_total:.2f}"
            
            self.db.add_notificacao((
                titulo, 
                mensagem, 
                date.today().strftime("%Y-%m-%d"), 
                "venda", 
                cliente_id
            ))
            
            QMessageBox.information(self, "Sucesso", "Venda registrada com sucesso!")
            
            # Limpar campos
            self.venda_quantidade.setText("1")
            self.calcular_valor_venda()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar venda: {str(e)}")
    
    def gerar_relatorio(self):
        mes = self.relatorio_mes_combo.currentIndex() + 1
        ano = self.relatorio_ano.text()
        
        try:
            ano = int(ano)
        except:
            QMessageBox.warning(self, "Aviso", "Ano deve ser um número válido!")
            return
        
        # Aqui você implementaria a geração do relatório
        # Por simplicidade, vamos apenas mostrar uma mensagem
        self.relatorio_area.setText(f"Relatório gerado para {mes:02d}/{ano}\n\n")
        
        # Adicionar informações básicas
        clientes = self.db.get_clientes()
        total_clientes = len(clientes)
        clientes_ativos = len([c for c in clientes if c[8] == 1])
        total_vendas = sum(c[9] or 0 for c in clientes)
        
        self.relatorio_area.append(f"Total de clientes: {total_clientes}")
        self.relatorio_area.append(f"Clientes ativos: {clientes_ativos}")
        self.relatorio_area.append(f"Faturamento total: R$ {total_vendas:.2f}")
        self.relatorio_area.append("\n---\n")
        
        # Top 5 clientes que mais gastaram
        clientes_ordenados = sorted(clientes, key=lambda x: x[9] or 0, reverse=True)
        
        self.relatorio_area.append("Top 5 clientes (por gastos):")
        for i, cliente in enumerate(clientes_ordenados[:5]):
            self.relatorio_area.append(f"{i+1}. {cliente[1]} - R$ {cliente[9] or 0:.2f}")
    
    def fazer_backup(self):
        # Simulação de backup
        backup_file = f"backup_tabacaria_{date.today().strftime('%Y%m%d')}.db"
        QMessageBox.information(self, "Backup", f"Backup criado com sucesso: {backup_file}")
    
    def restaurar_backup(self):
        # Simulação de restauração
        QMessageBox.information(self, "Restauração", "Backup restaurado com sucesso")
    
    def ver_notificacoes(self):
        notificacoes = self.db.get_notificacoes_hoje()
        if notificacoes:
            self.mostrar_dialogo_notificacoes(notificacoes)
        else:
            QMessageBox.information(self, "Notificações", "Não há notificações para hoje")
    
    def abrir_edicao_cliente(self, cliente_id):
        cliente = self.db.get_cliente(cliente_id)
        
        if cliente:
            # Aqui você implementaria um diálogo de edição
            QMessageBox.information(self, "Editar Cliente", f"Edição do cliente: {cliente[1]}")
    
    def ver_compras_cliente(self, cliente_id):
        cliente = self.db.get_cliente(cliente_id)
        compras = self.db.get_compras_cliente(cliente_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Compras de {cliente[1]}")
        dialog.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Data", "Produto", "Quantidade", "Valor"])
        
        table.setRowCount(len(compras))
        for row, compra in enumerate(compras):
            table.setItem(row, 0, QTableWidgetItem(compra[0]))
            table.setItem(row, 1, QTableWidgetItem(compra[1]))
            table.setItem(row, 2, QTableWidgetItem(str(compra[2])))
            table.setItem(row, 3, QTableWidgetItem(f"R$ {compra[3]:.2f}"))
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(dialog.close)
        layout.addWidget(btn_fechar)
        
        dialog.setLayout(layout)
        dialog.exec_()

def main():
    app = QApplication(sys.argv)
    
    # Definir estilo da aplicação
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()