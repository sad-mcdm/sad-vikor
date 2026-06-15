import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.pdfgen import canvas

# Branding definition per system mode
BRANDING = {
    'central': {
        'title': 'Nexus MCDM',
        'primary': colors.HexColor('#8B5CF6'),   # Purple
        'secondary': colors.HexColor('#10B981'), # Emerald
        'logo': 'nexus_mcdm.png'
    },
    'smarts_smarter': {
        'title': 'Nexus SMARTS/SMARTER',
        'primary': colors.HexColor('#0D9488'),   # Teal
        'secondary': colors.HexColor('#94A3B8'), # Silver/Slate
        'logo': 'nexus_smarts_smarter.png'
    },
    'ahp': {
        'title': 'Nexus AHP',
        'primary': colors.HexColor('#D97706'),   # Gold/Amber
        'secondary': colors.HexColor('#4B5563'), # Charcoal
        'logo': 'nexus_ahp.png'
    },
    'bwm': {
        'title': 'Nexus BWM',
        'primary': colors.HexColor('#F43F5E'),   # Coral
        'secondary': colors.HexColor('#64748B'), # Slate
        'logo': 'nexus_bwm.png'
    },
    'macbeth': {
        'title': 'Nexus MACBETH',
        'primary': colors.HexColor('#F59E0B'),   # Amber
        'secondary': colors.HexColor('#1E3A8A'), # Dark Blue
        'logo': 'nexus_macbeth.png'
    },
    'bwt': {
        'title': 'Nexus BWT',
        'primary': colors.HexColor('#DC2626'),   # Crimson
        'secondary': colors.HexColor('#D97706'), # Amber/Sand
        'logo': 'nexus_bwt.png'
    },
    'topsis': {
        'title': 'Nexus TOPSIS',
        'primary': colors.HexColor('#2563EB'),   # Sapphire
        'secondary': colors.HexColor('#E2E8F0'), # Platinum/Slate
        'logo': 'nexus_topsis.png'
    },
    'vikor': {
        'title': 'Nexus VIKOR',
        'primary': colors.HexColor('#059669'),   # Emerald
        'secondary': colors.HexColor('#B45309'), # Bronze/Brown
        'logo': 'nexus_vikor.png'
    },
    'electre': {
        'title': 'Nexus ELECTRE',
        'primary': colors.HexColor('#4F46E5'),   # Indigo
        'secondary': colors.HexColor('#7C3AED'), # Violet
        'logo': 'nexus_electre.png'
    },
    'promethee': {
        'title': 'Nexus PROMETHEE',
        'primary': colors.HexColor('#06B6D4'),   # Cyan
        'secondary': colors.HexColor('#6D28D9'), # Deep Purple
        'logo': 'nexus_promethee.png'
    }
}

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Don't draw headers/footers on page 1 (cover)
        if self._pageNumber == 1:
            self.restoreState()
            return

        primary_hex = self.__dict__.get('_primary_color_hex', '#8B5CF6')
        title_text = self.__dict__.get('_system_title_text', 'Nexus MCDM')
        logo_filename = self.__dict__.get('_logo_filename', 'nexus_mcdm.png')
        
        primary = colors.HexColor(primary_hex)

        # Draw Header
        self.setStrokeColor(primary)
        self.setLineWidth(0.5)
        self.line(54, 738, 558, 738)
        
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(primary)
        self.drawString(54, 744, title_text.upper())
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#6B7280'))
        self.drawRightString(558, 744, "DOCUMENTAÇÃO OFICIAL")

        # Draw Footer
        self.line(54, 54, 558, 54)
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor('#9CA3AF'))
        self.drawString(54, 42, "Direitos Reservados © 2026 NEXUS-MCDM. Todos os direitos reservados.")
        
        # Page Numbering
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 42, page_str)
        self.restoreState()


def create_pdf(output_path, system_mode, doc_type='user_guide_pt'):
    brand = BRANDING.get(system_mode, BRANDING['central'])
    primary = brand['primary']
    secondary = brand['secondary']
    title = brand['title']
    logo_file = brand['logo']
    
    # Locate assets
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, 'static', 'images', 'logos', logo_file)
    if not os.path.exists(logo_path):
        # Fallback to central logo if specific logo not found
        logo_path = os.path.join(base_dir, 'static', 'images', 'logos', 'nexus_mcdm.png')

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles matching visual identity
    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary,
        alignment=1, # Center
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4B5563'),
        alignment=1, # Center
        spaceAfter=30
    ))

    styles.add(ParagraphStyle(
        name='Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=secondary,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name='Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='Body_Bold',
        parent=styles['Body_Custom'],
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='Code_Custom',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=4
    ))

    story = []

    # ──── PAGE 1: COVER PAGE ────
    story.append(Spacer(1, 40))
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=80, height=80, hAlign='CENTER'))
    story.append(Spacer(1, 20))
    
    main_title = f"{title}"
    if doc_type == 'user_guide_pt':
        doc_subtitle = "Guia do Usuário — Documentação Oficial"
    elif doc_type == 'user_guide_en':
        doc_subtitle = "User Guide — Official Documentation"
    else:
        doc_subtitle = "Manual do Programador & Especifcações de Resolvedores"

    story.append(Paragraph(main_title, styles['DocTitle']))
    story.append(Paragraph(doc_subtitle, styles['DocSubtitle']))
    story.append(Spacer(1, 100))
    
    # Metadata block
    meta_text = f"""
    <b>Organização:</b> NEXUS-MCDM<br/>
    <b>Status:</b> Distribuição Geral<br/>
    <b>Ambiente:</b> Integrado / Standalone<br/>
    <b>Copyright:</b> Todos os direitos reservados à NEXUS-MCDM.
    """
    t = Table([[Paragraph(meta_text, styles['Body_Custom'])]], colWidths=[350], hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINELEFT', (0,0), (0,0), 3, primary),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ──── PAGE 2: CONTENT ────
    if doc_type == 'user_guide_pt':
        story.append(Paragraph("1. Introdução ao Ecossistema Nexus MCDM", styles['Heading1_Custom']))
        story.append(Paragraph(
            f"O sistema <b>{title}</b> é parte integrante da família NEXUS-MCDM de sistemas de apoio à decisão multicritério. "
            "Ele oferece uma interface moderna e intuitiva para guiar os decisores no processo de modelagem de problemas complexos, "
            "garantindo rigor matemático e facilidade de operação tanto no modo integrado quanto em instalações isoladas.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("2. Formulações Matemáticas de Normalização", styles['Heading1_Custom']))
        story.append(Paragraph(
            "Em problemas de decisão multicritério, os critérios físicos frequentemente possuem unidades distintas (ex: R$, Kg, % de rendimento, dias). "
            "A normalização é o processo de transformar essas escalas heterogêneas em valores adimensionais em um intervalo comum, usualmente [0, 1]. "
            "O sistema Nexus implementa as seguintes formulações principais de normalização:",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("A. Normalização Linear para Critérios de Benefício (Maximizar):", styles['Heading2_Custom']))
        story.append(Paragraph(
            "Para critérios onde valores maiores são mais desejáveis (ex: Qualidade, Lucro, Desempenho), calcula-se:<br/>"
            "<b>r_ij = (x_ij - min(x_j)) / (max(x_j) - min(x_j))</b><br/>"
            "Onde: <i>x_ij</i> é o valor original na matriz; <i>min(x_j)</i> é o pior desempenho físico naquele critério; "
            "e <i>max(x_j)</i> é o melhor desempenho.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("B. Normalização Linear para Critérios de Custo (Minimizar):", styles['Heading2_Custom']))
        story.append(Paragraph(
            "Para critérios onde valores menores são preferíveis (ex: Custo, Tempo de Entrega, Riscos), calcula-se:<br/>"
            "<b>r_ij = (max(x_j) - x_ij) / (max(x_j) - min(x_j))</b><br/>"
            "Dessa forma, o menor custo físico recebe a maior utilidade (1.0) e o maior custo recebe a menor utility (0.0).",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("C. Normalização Vetorial:", styles['Heading2_Custom']))
        story.append(Paragraph(
            "Utilizada principalmente em resolvedores baseados em distância geométrica (como TOPSIS), divide cada elemento pela norma do vetor:<br/>"
            "<b>r_ij = x_ij / sqrt( soma_{k=1}^m ( x_kj^2 ) )</b><br/>"
            "Essa normalização preserva a proporcionalidade dos dados originais sob transformações geométricas.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("3. O Assistente de Decisão (Wizard)", styles['Heading1_Custom']))
        story.append(Paragraph(
            "O fluxo de trabalho para estruturar e resolver qualquer problema de decisão é composto de 5 passos sequenciais:",
            styles['Body_Custom']
        ))
        
        steps = [
            ("Passo 1: Racionalidade", "Definição do modelo de preferência: Racionalidade <b>Compensatória</b> (métodos como AHP, TOPSIS, VIKOR e SMARTS, onde desempenhos ruins em um critério podem ser compensados por desempenhos excelentes em outros) ou Racionalidade <b>Não-Compensatória</b> (como ELECTRE e PROMETHEE, onde limites estritos de preferência e limiares de veto barram a compensação)."),
            ("Passo 2: Problemática de Decisão", "• <b>Escolha (α):</b> Identificar a alternativa vencedora (ou grupo restrito).<br/>"
                                                 "• <b>Ordenação (β):</b> Rankear todas as alternativas do primeiro ao último lugar.<br/>"
                                                 "• <b>Classificação (γ):</b> Agrupar alternativas em categorias (ex: Ótimo, Aceitável, Insatisfatório).<br/>"
                                                 "• <b>Portfólio (δ):</b> Selecionar uma combinação ideal sujeita a restrições de orçamento (PROMETHEE V)."),
            ("Passo 3: Seleção do Método", "Escolha do motor de cálculo compatível com as definições de racionalidade e problemática selecionadas."),
            ("Passo 4: Matriz de Consequências", "Preenchimento dos desempenhos físicos das alternativas. A plataforma suporta inserção manual e importação robusta de planilhas nos formatos .csv, .xlsx e .xls de acordo com o modelo de Matriz de Consequências do TCC."),
            ("Passo 5: Elicitação de Parâmetros e Resultados", "Configuração de pesos (importância) e parâmetros locais. Após o salvamento, o sistema processa os dados, exibe os rankings, gera o gráfico de utilidade global e oferece o download do Relatório Técnico Completo em PDF.")
        ]
        
        for step_title, step_desc in steps:
            story.append(Paragraph(f"<b>{step_title}</b>", styles['Heading2_Custom']))
            story.append(Paragraph(step_desc, styles['Body_Custom']))

    elif doc_type == 'user_guide_en':
        story.append(Paragraph("1. Introduction to the Nexus MCDM Ecosystem", styles['Heading1_Custom']))
        story.append(Paragraph(
            f"The <b>{title}</b> system belongs to the NEXUS-MCDM family of multi-criteria decision-making software. "
            "It delivers a state-of-the-art interface designed to guide users through structured decision modeling, "
            "ensuring mathematical consistency and ease of operation in both integrated and standalone installations.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("2. Mathematical Formulation of Normalization", styles['Heading1_Custom']))
        story.append(Paragraph(
            "In MCDM, physical criteria values often come in heterogeneous units (e.g. currency, weight, efficiency, delay). "
            "Normalization is the procedure that converts these varying scales into a common, dimensionless range, typically [0, 1]. "
            "The Nexus system uses the following standard normalization formulations:",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("A. Linear Normalization for Benefit Criteria (Maximize):", styles['Heading2_Custom']))
        story.append(Paragraph(
            "For criteria where higher physical values represent better options (e.g. Quality, Profit, Throughput):<br/>"
            "<b>r_ij = (x_ij - min(x_j)) / (max(x_j) - min(x_j))</b><br/>"
            "Where: <i>x_ij</i> is the physical consequence; <i>min(x_j)</i> is the worst performance; and <i>max(x_j)</i> is the best performance.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("B. Linear Normalization for Cost Criteria (Minimize):", styles['Heading2_Custom']))
        story.append(Paragraph(
            "For criteria where lower physical values are desired (e.g. Cost, Lead Time, Risk):<br/>"
            "<b>r_ij = (max(x_j) - x_ij) / (max(x_j) - min(x_j))</b><br/>"
            "Thus, the lowest cost achieves the highest utility score (1.0), and the highest cost maps to the lowest utility (0.0).",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("C. Vector Normalization:", styles['Heading2_Custom']))
        story.append(Paragraph(
            "Typically applied in distance-based MCDM solvers (such as TOPSIS), it divides each cell value by the column vector length:<br/>"
            "<b>r_ij = x_ij / sqrt( sum_{k=1}^m ( x_kj^2 ) )</b><br/>"
            "This preserves the geometric proportion of raw data under vector transformation.",
            styles['Body_Custom']
        ))
        
        story.append(Paragraph("3. The 5-Step Decision Wizard", styles['Heading1_Custom']))
        story.append(Paragraph(
            "Building and resolving any decision problem follows 5 sequential steps:",
            styles['Body_Custom']
        ))
        
        steps = [
            ("Step 1: Rationality Definition", "Select between <b>Compensatory</b> Rationality (where strong criteria performances can compensate for poor ones, e.g. AHP, TOPSIS, VIKOR) or <b>Non-Compensatory</b> Rationality (where veto thresholds strictly block trade-offs, e.g. ELECTRE, PROMETHEE)."),
            ("Step 2: Decision Problematic", "• <b>Choice (α):</b> Identify the best single option or a short elite list.<br/>"
                                             "• <b>Ranking (β):</b> Classify all alternatives in order of preference (1st to last place).<br/>"
                                             "• <b>Sorting (γ):</b> Assign alternatives to predefined categories.<br/>"
                                             "• <b>Portfolio (δ):</b> Choose a combination of projects under a resource constraint (PROMETHEE V)."),
            ("Step 3: MCDM Solver Selection", "Pick the mathematical solver that fits the chosen rationality and problematic."),
            ("Step 4: Consequence Matrix Input", "Enter the performance matrix. The application supports manual input and file imports from CSV, XLSX, and XLS in accordance with the TCC Consequence Matrix standard format."),
            ("Step 5: Preferences and Results", "Configure criterion weights and local threshold curves. The engine then resolves the model, plots utilities, and enables download of the Complete Technical PDF Report.")
        ]
        
        for step_title, step_desc in steps:
            story.append(Paragraph(f"<b>{step_title}</b>", styles['Heading2_Custom']))
            story.append(Paragraph(step_desc, styles['Body_Custom']))

    else:
        # ──── PROGRAMMER MANUAL (PSEUDOCODES) ────
        story.append(Paragraph("1. Arquitetura de Software do Hub", styles['Heading1_Custom']))
        story.append(Paragraph(
            "O ecossistema Nexus MCDM é estruturado com uma separação clara entre a interface do usuário (Flask/Jinja2) "
            "e os motores de cálculo matemáticos localizados em <code>modules/</code>. Cada resolvedor é implementado em "
            "Python utilizando estruturas vetoriais do NumPy e solucionadores de Programação Linear.",
            styles['Body_Custom']
        ))

        story.append(Paragraph("2. Pseudocódigos dos Solucionadores MCDM", styles['Heading1_Custom']))
        story.append(Paragraph(
            "Abaixo estão listados os pseudocódigos fundamentais dos principais resolvedores do sistema:",
            styles['Body_Custom']
        ))

        # TOPSIS Pseudocode
        topsis_code = """
<b>ALGORITMO 1: TOPSIS Engine</b>
1: Receber Matriz X (m x n), pesos W, e critérios de custo/benefício C_types
2: Para cada coluna j = 1 a n:
3:     Denom = raiz_quadrada( soma( x_ij^2 ) para i = 1 a m )
4:     Para cada linha i = 1 a m:
5:         r_ij = x_ij / Denom
6:         v_ij = r_ij * w_j
7: Identificar Ideal Positivo (A+) e Negativo (A-):
8:     Se C_types[j] == 'benefit': A_j+ = max(v_j), A_j- = min(v_j)
9:     Se C_types[j] == 'cost':    A_j+ = min(v_j), A_j- = max(v_j)
10: Para cada alternativa i = 1 a m:
11:    S_i+ = raiz_quadrada( soma( (v_ij - A_j+)^2 ) para j = 1 a n )
12:    S_i- = raiz_quadrada( soma( (v_ij - A_j-)^2 ) para j = 1 a n )
13:    C_i = S_i- / (S_i+ + S_i-)
14: Retornar ranking ordenado decrescente baseado em C_i
        """
        
        # VIKOR Pseudocode
        vikor_code = """
<b>ALGORITMO 2: VIKOR Engine</b>
1: Receber Matriz X, pesos W, critério de custo/benefício, e parâmetro v
2: Determinar melhores (f_j*) e piores (f_j-) valores físicos por critério
3: Para cada alternativa i = 1 a m:
4:     S_i = soma( w_j * (f_j* - x_ij) / (f_j* - f_j-) ) para j = 1 a n
5:     R_i = max( w_j * (f_j* - x_ij) / (f_j* - f_j-) ) para j = 1 a n
6: Determinar S* = min(S_i), S- = max(S_i), R* = min(R_i), R- = max(R_i)
7: Para cada alternativa i = 1 a m:
8:     Q_i = v * (S_i - S*) / (S- - S*) + (1-v) * (R_i - R*) / (R- - R*)
9: Retornar ranking ordenado crescente baseado em Q_i
        """

        # ELECTRE TRI Pseudocode
        electre_code = """
<b>ALGORITMO 3: ELECTRE TRI Category Sorting</b>
1: Receber Perfis Limites b_1, b_2, ..., b_k, pesos W, e limiares (q, p, v)
2: Para cada alternativa a_i e perfil b_h:
3:     Calcular Concordância c(a_i, b_h) agregada por pesos
4:     Calcular Discordância local d_j(a_i, b_h) e verificar limiar de Veto
5:     Determinar Credibilidade rho(a_i, b_h) incorporando concordância e vetos
6: Relação de Sobreclassificação: a_i S b_h se rho(a_i, b_h) >= lambda
7: Alocação Pessimista:
8:     Encontrar o maior perfil b_h (de k a 1) onde a_i S b_h
9:     Alocar a_i para a categoria h + 1 (Categoria 1 é a pior)
        """

        # PROMETHEE V Pseudocode
        promethee_code = """
<b>ALGORITMO 4: PROMETHEE V Portfolio Optimization</b>
1: Receber Fluxos Líquidos Net_Phi(a_i), Custos c_i, e Orçamento limite B
2: Definir Variáveis de Decisão Binárias: x_i em {0, 1}
3: Maximizar a Função Objetivo: Z = soma( Net_Phi(a_i) * x_i )
4: Sujeito a Restrição Orçamentária: soma( c_i * x_i ) <= B
5: Resolver via Otimização de Mochila Inteira (0-1 Knapsack)
6: Retornar projetos selecionados (x_i = 1)
        """

        story.append(KeepTogether([
            Paragraph(topsis_code.replace('\n', '<br/>'), styles['Code_Custom']),
            Spacer(1, 15)
        ]))
        story.append(KeepTogether([
            Paragraph(vikor_code.replace('\n', '<br/>'), styles['Code_Custom']),
            Spacer(1, 15)
        ]))
        story.append(KeepTogether([
            Paragraph(electre_code.replace('\n', '<br/>'), styles['Code_Custom']),
            Spacer(1, 15)
        ]))
        story.append(KeepTogether([
            Paragraph(promethee_code.replace('\n', '<br/>'), styles['Code_Custom']),
            Spacer(1, 15)
        ]))

    # Render document using dynamic custom canvas to inject header/footers
    doc.build(story, canvasmaker=NumberedCanvas)


def generate_results_report_pdf(output_path, problem, criteria, results, solver_res, system_mode):
    """
    Generates a beautiful multi-page PDF Report of the decision results.
    """
    brand = BRANDING.get(system_mode, BRANDING['central'])
    primary = brand['primary']
    secondary = brand['secondary']
    title = brand['title']
    logo_file = brand['logo']
    
    # Configure canvas globally
    NumberedCanvas._primary_color_hex = primary.hexval()
    NumberedCanvas._system_title_text = title
    NumberedCanvas._logo_filename = logo_file
    
    # Locate assets
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, 'static', 'images', 'logos', logo_file)
    if not os.path.exists(logo_path):
        logo_path = os.path.join(base_dir, 'static', 'images', 'logos', 'nexus_mcdm.png')

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Style definitions
    styles.add(ParagraphStyle(
        name='RepTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary,
        alignment=1, # Center
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='RepSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#4B5563'),
        alignment=1, # Center
        spaceAfter=25
    ))
    styles.add(ParagraphStyle(
        name='RepH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name='RepBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='RepBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1F2937')
    ))
    styles.add(ParagraphStyle(
        name='TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    ))
    styles.add(ParagraphStyle(
        name='TC',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1F2937')
    ))
    styles.add(ParagraphStyle(
        name='TCB',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1F2937')
    ))

    story = []

    # ──── COVER PAGE ────
    story.append(Spacer(1, 35))
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=80, height=80, hAlign='CENTER'))
    story.append(Spacer(1, 20))
    story.append(Paragraph("RELATÓRIO TÉCNICO DE DECISÃO", styles['RepTitle']))
    story.append(Paragraph(f"Problema: {problem.name}", styles['RepSubtitle']))
    story.append(Spacer(1, 80))
    
    # Metadata Block
    from datetime import datetime
    formatted_date = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    meta_text = f"""
    <b>Problema de Decisão:</b> {problem.name}<br/>
    <b>Método Solucionador:</b> {problem.method.upper()}<br/>
    <b>Racionalidade:</b> {'Compensatória' if problem.rationality == 'compensatory' else 'Não-Compensatória'}<br/>
    <b>Problemática:</b> {problem.problematic.capitalize()}<br/>
    <b>Data de Emissão:</b> {formatted_date}<br/>
    <b>Provedor Tecnológico:</b> NEXUS-MCDM
    """
    
    t_meta = Table([[Paragraph(meta_text, styles['RepBody'])]], colWidths=[380], hAlign='CENTER')
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINELEFT', (0,0), (0,0), 3, primary),
    ]))
    story.append(t_meta)
    story.append(PageBreak())

    # ──── CONTENT PAGE 2+ ────
    story.append(Paragraph("1. Resumo Executivo e Recomendação", styles['RepH1']))
    desc_problem = problem.description or "Nenhuma descrição fornecida para o problema de decisão."
    story.append(Paragraph(f"Este relatório apresenta a análise estruturada e a solução para o problema <b>{problem.name}</b>. Descrição: {desc_problem}", styles['RepBody']))
    
    # WINNER SHOWCASE IN PDF
    winner_names = []
    if results:
        best_score = results[0]['score']
        winner_names = [r['alternative'].name for r in results if abs(r['score'] - best_score) < 1e-9]
        
    rec_text = ""
    if problem.problematic == 'choice' and winner_names:
        rec_text = f"<b>Alternativa Recomendada (Vencedora):</b> {', '.join(winner_names)} (Pontuação: {best_score:.4f})"
    elif problem.problematic == 'ranking' and results:
        rec_text = f"<b>Alternativa Recomendada:</b> {results[0]['alternative'].name} (1º Lugar - Pontuação: {best_score:.4f})"
    elif problem.problematic == 'sorting' and results:
        rec_text = "<b>Classificação em Categorias:</b> Alternativas alocadas com sucesso conforme as especificações de limites."
    
    # Check if ELECTRE kernel exists
    kernel = solver_res.get('extra', {}).get('kernel')
    if problem.method == 'electre' and kernel:
        kernel_names = []
        for item in results:
            if item['alternative'].id in kernel:
                kernel_names.append(item['alternative'].name)
        rec_text += f"<br/><b>Núcleo de Alternativas (Kernel ELECTRE):</b> {', '.join(kernel_names)}"
        
    # Check if PROMETHEE V portfolio exists
    selected_portfolio = solver_res.get('extra', {}).get('selected_portfolio')
    if problem.method == 'promethee' and selected_portfolio:
        portfolio_names = []
        for item in results:
            if item['alternative'].id in selected_portfolio:
                portfolio_names.append(item['alternative'].name)
        budget = solver_res.get('extra', {}).get('budget', 0.0)
        rec_text += f"<br/><b>Portfólio Selecionado (PROMETHEE V, Orçamento: {budget}):</b> {', '.join(portfolio_names)}"

    t_rec = Table([[Paragraph(rec_text, styles['RepBody'])]], colWidths=[504], hAlign='LEFT')
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5') if problem.problematic in ['choice', 'ranking'] else colors.HexColor('#F5F3FF')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINELEFT', (0,0), (0,0), 3, colors.HexColor('#10B981') if problem.problematic in ['choice', 'ranking'] else primary),
    ]))
    story.append(t_rec)
    story.append(Spacer(1, 10))

    # SECTION 2: MATRIX
    story.append(Paragraph("2. Matriz de Consequências (Dados de Entrada)", styles['RepH1']))
    story.append(Paragraph("Valores das consequências físicas de cada alternativa em cada critério:", styles['RepBody']))
    
    matrix_headers = [Paragraph("Alternativa", styles['TH'])]
    for crit in criteria:
        matrix_headers.append(Paragraph(f"{crit.name} ({'Max' if crit.criteria_type == 'benefit' else 'Min'})", styles['TH']))
        
    matrix_table_data = [matrix_headers]
    for r in results:
        alt = r['alternative']
        row = [Paragraph(alt.name, styles['TCB'])]
        # Find consequence values
        for crit in criteria:
            val = 0.0
            for alt_obj in problem.alternatives:
                if alt_obj.id == alt.id:
                    for conseq in alt_obj.consequences:
                        if conseq.criterion_id == crit.id:
                            val = conseq.value
            row.append(Paragraph(f"{val:.2f}", styles['TC']))
        matrix_table_data.append(row)
        
    # Calculate widths
    num_cols = len(criteria) + 1
    col_w = [120] + [384 / len(criteria)] * len(criteria) if len(criteria) > 0 else [504]
    t_matrix = Table(matrix_table_data, colWidths=col_w, hAlign='LEFT')
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 10))

    # SECTION 3: WEIGHTS
    story.append(Paragraph("3. Parâmetros e Pesos dos Critérios", styles['RepH1']))
    story.append(Paragraph("Ponderações de importância e parâmetros de limites locais configurados:", styles['RepBody']))
    
    weights_headers = [
        Paragraph("Critério", styles['TH']),
        Paragraph("Direção", styles['TH']),
        Paragraph("Peso Obtido", styles['TH'])
    ]
    
    # Check if local thresholds exist (ELECTRE / PROMETHEE)
    has_thresholds = problem.method in ['electre', 'promethee']
    if has_thresholds:
        weights_headers.extend([
            Paragraph("Indiferença (q)", styles['TH']),
            Paragraph("Preferência (p)", styles['TH']),
            Paragraph("Veto (v)", styles['TH'])
        ])
        
    weights_table_data = [weights_headers]
    for crit in criteria:
        row = [
            Paragraph(crit.name, styles['TCB']),
            Paragraph("Maximização (Benefício)" if crit.criteria_type == 'benefit' else "Minimização (Custo)", styles['TC']),
            Paragraph(f"{((crit.weight or 0.0) * 100):.1f}%", styles['TCB'])
        ]
        if has_thresholds:
            # Load values
            q, p, v = 0.0, 0.0, 999999.0
            if problem.method == 'electre':
                t_pref = problem.preferences.get('thresholds', {}).get(str(crit.id), {})
                q = t_pref.get('q', 0.0)
                p = t_pref.get('p', 0.1)
                v = t_pref.get('v', 999999.0)
            elif problem.method == 'promethee':
                t_pref = problem.preferences.get('functions', {}).get(str(crit.id), {})
                q = t_pref.get('q', 0.0)
                p = t_pref.get('p', 1.0)
                v = t_pref.get('v', 999999.0)
            
            row.extend([
                Paragraph(f"{q:.2f}", styles['TC']),
                Paragraph(f"{p:.2f}", styles['TC']),
                Paragraph(f"{v:.2f}" if v < 99999 else "Sem Veto", styles['TC'])
            ])
        weights_table_data.append(row)
        
    col_w_weights = [150, 150, 100] + ([34, 34, 36] if has_thresholds else [])
    t_weights = Table(weights_table_data, colWidths=col_w_weights, hAlign='LEFT')
    t_weights.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_weights)
    
    # Display consistency metrics
    cr = solver_res.get('criteria_cr')
    xi = solver_res.get('consistency_xi')
    if cr is not None:
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Razão de Consistência das Comparações (CR):</b> {cr*100:.2f}% (Aceitável: &lt; 10%)", styles['RepBody']))
    elif xi is not None:
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Índice de Consistência de Proporções (&xi;):</b> {xi:.4f}", styles['RepBody']))
        
    story.append(Spacer(1, 10))

    # SECTION 4: RANKING
    story.append(Paragraph("4. Classificação e Ordenação Final", styles['RepH1']))
    story.append(Paragraph("Ranking ordenado das alternativas de acordo com os resultados consolidados:", styles['RepBody']))
    
    ranks_headers = [
        Paragraph("Classificação (Rank)", styles['TH']),
        Paragraph("Alternativa", styles['TH']),
        Paragraph("Pontuação Global", styles['TH'])
    ]
    ranks_table_data = [ranks_headers]
    for r in results:
        row = [
            Paragraph(f"{r['rank']}º Lugar", styles['TCB']),
            Paragraph(r['alternative'].name, styles['TC']),
            Paragraph(f"{r['score']:.4f}", styles['TCB'])
        ]
        ranks_table_data.append(row)
        
    t_ranks = Table(ranks_table_data, colWidths=[120, 234, 150], hAlign='LEFT')
    t_ranks.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_ranks)
    story.append(Spacer(1, 10))

    # SECTION 5: METHOD NOTES
    story.append(Paragraph("5. Notas Metodológicas de Auditoria", styles['RepH1']))
    method_desc_map = {
        'smarts': "O método SMARTS (Simple Multi-Attribute Rating Technique with Swing) calcula a utilidade linear normalizada a partir dos valores mínimos e máximos da matriz de consequências físicas, agregando as utilidades parciais por soma ponderada linear dos pesos swing.",
        'smarter': "O método SMARTER (Simple Multi-Attribute Rating Technique Extended to Ranking) utiliza pesos centróides ROC (Rank-Order Centroid) calculados exclusivamente a partir do ranking ordinal de importância fornecido, garantindo robustez matemática e atenuando vieses subjetivos.",
        'ahp': "O AHP (Analytic Hierarchy Process) resolve o vetor de prioridades através do autovetor principal das matrizes de comparações par a par de Saaty. A coerência interna das comparações é verificada através da Razão de Consistência (CR).",
        'macbeth': "O método MACBETH utiliza programação linear (PL) para converter escalas qualitativas semânticas de comparações de atratividade em escalas cardinais puras com ancoragens em alternativas de referência.",
        'bwm': "O BWM (Best Worst Method) otimiza os pesos por meio de programação linear minimax baseada nas comparações estruturadas do melhor critério para os demais, e dos demais para o pior, minimizando a inconsistência.",
        'bwt': "O BWT (Best Worst Tradeoff) combina taxas reais de tradeoffs inter-critério com bisseções de utilidade intra-critério locais resolvidas por programação linear para obter funções de valor com realismo físico absoluto.",
        'topsis': "O TOPSIS calcula a distância euclidiana de cada alternativa normalizada e ponderada em relação à solução ideal positiva e ideal negativa. As pontuações são representadas pelo coeficiente de proximidade relativa (C_i).",
        'vikor': "O VIKOR estabelece uma solução de compromisso multicritério integrando o valor de utilidade máxima de grupo (S_i) e o arrependimento individual (R_i), ranqueando as opções pelo índice de compromisso Q_i.",
        'electre': "A família ELECTRE estabelece relações de sobreclassificação baseadas em concordância e discordância de pesos agregados, ativando limiares de veto estritos que bloqueiam a compensação.",
        'promethee': "O PROMETHEE estabelece fluxos de preferência líquida a partir de funções de preferência locais, gerando ordenações parciais (PROMETHEE I) ou completas baseadas em fluxos líquidos (PROMETHEE II)."
    }
    method_text = method_desc_map.get(problem.method, "Resolvedor MCDM configurado e processado sob auditoria matemática.")
    story.append(Paragraph(method_text, styles['RepBody']))
    
    # Render document using dynamic NumberedCanvas for headers/footers
    doc.build(story, canvasmaker=NumberedCanvas)


def generate_all_pdfs_for_mode(system_mode, docs_dir):
    os.makedirs(docs_dir, exist_ok=True)
    
    brand = BRANDING.get(system_mode, BRANDING['central'])
    
    # Inject variables onto NumberedCanvas globally so ReportLab can read them
    NumberedCanvas._primary_color_hex = brand['primary'].hexval()
    NumberedCanvas._system_title_text = brand['title']
    NumberedCanvas._logo_filename = brand['logo']
    
    # Paths
    guide_pt_path = os.path.join(docs_dir, 'user_guide_pt.pdf')
    guide_en_path = os.path.join(docs_dir, 'user_guide_en.pdf')
    prog_manual_path = os.path.join(docs_dir, 'programmer_manual.pdf')
    
    # Generate
    create_pdf(guide_pt_path, system_mode, 'user_guide_pt')
    create_pdf(guide_en_path, system_mode, 'user_guide_en')
    create_pdf(prog_manual_path, system_mode, 'programmer_manual')
    
    print(f"Generated PDFs for mode '{system_mode}' successfully.")


if __name__ == '__main__':
    # Test generation for central mode
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_docs_dir = os.path.join(base_dir, 'static', 'docs')
    generate_all_pdfs_for_mode('central', test_docs_dir)
