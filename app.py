import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import pandas as pd
from config import Config
from models import db, User, DecisionProblem, Alternative, Criterion, Consequence

# Solvers
from sad_mcdm.smarts_smarter.engine import solve_smarts_smarter
from sad_mcdm.ahp.engine import solve_ahp
from sad_mcdm.macbeth.engine import solve_macbeth
from sad_mcdm.bwm.engine import solve_bwm
from sad_mcdm.bwt.engine import solve_bwt
from sad_mcdm.topsis.engine import solve_topsis
from sad_mcdm.vikor.engine import solve_vikor
from sad_mcdm.electre.engine import solve_electre
from sad_mcdm.promethee.engine import solve_promethee
from sad_mcdm.services.monte_carlo import run_monte_carlo

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

# Helper for login requirement
def get_current_user():
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

# ─── Auth Routes ───────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not username or not email or not password:
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já cadastrado.', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Bem-vindo de volta, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'success')
    return redirect(url_for('landing'))

# ─── Main Hub Routes ───────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('landing'))

@app.route('/landing')
def landing():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    system_mode = app.config.get('SYSTEM_MODE', 'central')
    if system_mode == 'central':
        problems = user.problems.order_by(DecisionProblem.created_at.desc()).all()
    elif system_mode == 'smarts_smarter':
        problems = user.problems.filter(DecisionProblem.method.in_(['smarts', 'smarter'])).order_by(DecisionProblem.created_at.desc()).all()
    else:
        problems = user.problems.filter_by(method=system_mode).order_by(DecisionProblem.created_at.desc()).all()
        
    return render_template('dashboard.html', problems=problems)

@app.route('/problem/new', methods=['POST'])
def create_problem():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Por favor, informe o nome do problema.', 'danger')
        return redirect(url_for('dashboard'))
        
    system_mode = app.config.get('SYSTEM_MODE', 'central')
    default_method = 'smarts'
    if system_mode not in ['central', 'smarts_smarter']:
        default_method = system_mode
        
    # Default values for rationality/problematic
    problem = DecisionProblem(
        user_id=user.id,
        name=name,
        description=description,
        rationality='compensatory',
        problematic='ranking',
        method=default_method
    )
    db.session.add(problem)
    db.session.commit()
    
    return redirect(url_for('select_rationality', problem_id=problem.id))

@app.route('/problem/<int:problem_id>/delete', methods=['POST'])
def delete_problem(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    db.session.delete(problem)
    db.session.commit()
    flash('Problema removido com sucesso.', 'success')
    return redirect(url_for('dashboard'))

# ─── Wizard Routes ─────────────────────────────────────────────────────

@app.route('/problem/<int:problem_id>/rationality', methods=['GET', 'POST'])
def select_rationality(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        rationality = request.form.get('rationality')
        if rationality not in ['compensatory', 'non-compensatory']:
            flash('Racionalidade inválida.', 'danger')
            return redirect(url_for('select_rationality', problem_id=problem.id))
            
        problem.rationality = rationality
        db.session.commit()
        return redirect(url_for('select_problematic', problem_id=problem.id))
        
    return render_template('wizard_rationality.html', problem=problem)

@app.route('/problem/<int:problem_id>/problematic', methods=['GET', 'POST'])
def select_problematic(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        problematic = request.form.get('problematic')
        if problematic not in ['choice', 'ranking', 'sorting', 'portfolio']:
            flash('Problemática inválida.', 'danger')
            return redirect(url_for('select_problematic', problem_id=problem.id))
            
        problem.problematic = problematic
        db.session.commit()
        
        system_mode = app.config.get('SYSTEM_MODE', 'central')
        if system_mode in ['ahp', 'bwm', 'macbeth', 'bwt', 'topsis', 'vikor', 'electre', 'promethee']:
            problem.method = system_mode
            db.session.commit()
            return redirect(url_for('consequence_matrix', problem_id=problem.id))
        else:
            return redirect(url_for('select_method', problem_id=problem.id))
        
    return render_template('wizard_problematic.html', problem=problem)

@app.route('/problem/<int:problem_id>/method', methods=['GET', 'POST'])
def select_method(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    
    system_mode = app.config.get('SYSTEM_MODE', 'central')
    if system_mode in ['ahp', 'bwm', 'macbeth', 'bwt', 'topsis', 'vikor', 'electre', 'promethee']:
        problem.method = system_mode
        db.session.commit()
        return redirect(url_for('consequence_matrix', problem_id=problem.id))
        
    is_compatible = problem.problematic in ['choice', 'ranking', 'sorting', 'portfolio']
    
    if request.method == 'POST':
        method = request.form.get('method')
        if system_mode == 'smarts_smarter':
            allowed_methods = ['smarts', 'smarter']
        else:
            allowed_methods = ['smarts', 'smarter', 'ahp', 'macbeth', 'bwm', 'bwt', 'topsis', 'vikor', 'electre', 'promethee']
            
        if method not in allowed_methods:
            flash('Método inválido.', 'danger')
            return redirect(url_for('select_method', problem_id=problem.id))
            
        problem.method = method
        db.session.commit()
        return redirect(url_for('consequence_matrix', problem_id=problem.id))
        
    return render_template('wizard_method.html', problem=problem, is_compatible=is_compatible)

@app.route('/problem/<int:problem_id>/matrix', methods=['GET', 'POST'])
def consequence_matrix(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    
    if request.method == 'POST':
        # Retrieve JSON data from form submission
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Nenhum dado enviado'}), 400
            
        try:
            # Delete existing criteria, alternatives, and consequences
            Alternative.query.filter_by(problem_id=problem.id).delete()
            Criterion.query.filter_by(problem_id=problem.id).delete()
            Consequence.query.filter_by(problem_id=problem.id).delete()
            db.session.flush()
            
            # 1. Recreate criteria
            criteria_map = {}
            for index, crit_data in enumerate(data['criteria']):
                criterion = Criterion(
                    problem_id=problem.id,
                    name=crit_data['name'],
                    criteria_type=crit_data['type'],
                    rank_position=index + 1
                )
                db.session.add(criterion)
                db.session.flush()
                criteria_map[crit_data['id']] = criterion
                
            # 2. Recreate alternatives
            alternatives_map = {}
            for alt_data in data['alternatives']:
                alternative = Alternative(
                    problem_id=problem.id,
                    name=alt_data['name']
                )
                db.session.add(alternative)
                db.session.flush()
                alternatives_map[alt_data['id']] = alternative
                
            # 3. Recreate consequences
            for row in data['consequences']:
                cell = Consequence(
                    problem_id=problem.id,
                    alternative_id=alternatives_map[row['alternative_id']].id,
                    criterion_id=criteria_map[row['criterion_id']].id,
                    value=float(row['value'])
                )
                db.session.add(cell)
                
            # Reset user preferences when matrix changes
            problem.preferences = {}
            db.session.commit()
            
            return jsonify({'success': True, 'redirect': url_for('evaluate_method', problem_id=problem.id)})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
            
    # Load current data to render in the template
    criteria = problem.criteria.order_by(Criterion.rank_position).all()
    alternatives = problem.alternatives.all()
    consequences = problem.consequences.all()
    
    # Map to grid
    conseq_grid = {}
    for c in consequences:
        conseq_grid[(c.alternative_id, c.criterion_id)] = c.value
        
    return render_template(
        'matrix_input.html', 
        problem=problem, 
        criteria=criteria, 
        alternatives=alternatives, 
        conseq_grid=conseq_grid
    )

# ─── File Import Route ─────────────────────────────────────────────────

@app.route('/problem/<int:problem_id>/import', methods=['POST'])
def import_matrix(problem_id):
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
        
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
    try:
        # File parsing
        ext = os.path.splitext(file.filename)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(file, header=None)
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file, header=None)
        else:
            return jsonify({'success': False, 'message': 'Formato não suportado. Use CSV, XLS ou XLSX.'}), 400
            
        if df.empty or len(df.columns) < 2:
            return jsonify({'success': False, 'message': 'Matriz muito pequena ou vazia.'}), 400
            
        # Detect if sheet is in TCC Format (at least 9 rows, and row 1 has types 0, 1, 2, 3...)
        is_tcc = False
        if len(df) >= 9:
            row1_vals = df.iloc[1, 1:].dropna().tolist()
            try:
                row1_ints = [int(float(x)) for x in row1_vals if str(x).strip() != '']
                if len(row1_ints) > 0 and all(x in [0, 1, 2, 3, 4, 5] for x in row1_ints):
                    is_tcc = True
            except (ValueError, TypeError):
                pass
                
        if is_tcc:
            # TCC Matrix format
            crit_names = [str(x).strip() for x in df.iloc[0, 1:].tolist()]
            # Map cost/benefit based on integer values (0, 2, 4 = cost, 1, 3, 5 = benefit)
            crit_types_raw = df.iloc[1, 1:].tolist()
            crit_types = []
            for t in crit_types_raw:
                try:
                    val = int(float(t))
                    if val in [0, 2, 4]:
                        crit_types.append('cost')
                    else:
                        crit_types.append('benefit')
                except (ValueError, TypeError):
                    crit_types.append('benefit')
            data_start_row = 8  # index 8 is row 9
        else:
            # Standard format
            # Row 0: Criteria names
            crit_names = [str(x).strip() for x in df.iloc[0, 1:].tolist()]
            
            # Row 1 check
            first_cell_row1 = str(df.iloc[1, 0]).lower().strip()
            has_type_row = first_cell_row1 in ['tipo', 'type', 'direção', 'direction']
            
            if has_type_row:
                crit_types_raw = [str(t).lower().strip() for t in df.iloc[1, 1:]]
                crit_types = ['cost' if 'cust' in t or 'cost' in t or 'min' in t else 'benefit' for t in crit_types_raw]
                data_start_row = 2
            else:
                crit_types = ['benefit' for _ in crit_names]
                data_start_row = 1
                
        parsed_criteria = []
        for name, ctype in zip(crit_names, crit_types):
            name_str = str(name).strip()
            if name_str and name_str.lower() != 'nan' and name_str != '':
                parsed_criteria.append({'name': name_str, 'type': ctype})
                
        num_crit = len(parsed_criteria)
        parsed_alternatives = []
        parsed_consequences = []
        import math
        
        for idx in range(data_start_row, len(df)):
            row = df.iloc[idx]
            alt_name = str(row.iloc[0]).strip()
            if not alt_name or alt_name.lower() == 'nan' or alt_name == '':
                continue
                
            parsed_alternatives.append(alt_name)
            
            row_vals = []
            for val in row.iloc[1:1+num_crit]:
                try:
                    fval = float(val)
                    if math.isnan(fval) or math.isinf(fval):
                        row_vals.append(0.0)
                    else:
                        row_vals.append(fval)
                except (ValueError, TypeError):
                    row_vals.append(0.0)
            parsed_consequences.append(row_vals)
            
        return jsonify({
            'success': True,
            'criteria': parsed_criteria,
            'alternatives': parsed_alternatives,
            'consequences': parsed_consequences
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao ler arquivo: {str(e)}'}), 500

# ─── Evaluation Route ──────────────────────────────────────────────────

@app.route('/problem/<int:problem_id>/evaluate', methods=['GET', 'POST'])
def evaluate_method(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    criteria = problem.criteria.order_by(Criterion.rank_position).all()
    alternatives = problem.alternatives.all()
    
    if not criteria or not alternatives:
        flash('Preencha a matriz de consequências antes de avaliar.', 'warning')
        return redirect(url_for('consequence_matrix', problem_id=problem.id))
        
    # Get consequence matrix data to display as reference
    consequences = problem.consequences.all()
    conseq_grid = {}
    for c in consequences:
        conseq_grid[(c.alternative_id, c.criterion_id)] = c.value
        
    matrix_data = []
    for alt in alternatives:
        row = []
        for crit in criteria:
            row.append(conseq_grid.get((alt.id, crit.id), 0.0))
        matrix_data.append(row)
        
    if request.method == 'POST':
        # Save preference data from forms
        pref_data = request.json
        if not pref_data:
            return jsonify({'success': False, 'message': 'Nenhum dado enviado'}), 400
            
        problem.preferences = pref_data
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('view_results', problem_id=problem.id)})
        
    # Depending on method, render the specific evaluation view
    template_map = {
        'smarts': 'evaluate_smarts.html',
        'smarter': 'evaluate_smarter.html',
        'ahp': 'evaluate_ahp.html',
        'macbeth': 'evaluate_macbeth.html',
        'bwm': 'evaluate_bwm.html',
        'bwt': 'evaluate_bwt.html',
        'topsis': 'evaluate_topsis.html',
        'vikor': 'evaluate_vikor.html',
        'electre': 'evaluate_electre.html',
        'promethee': 'evaluate_promethee.html'
    }
    
    template = template_map.get(problem.method, 'evaluate_smarts.html')
    return render_template(
        template,
        problem=problem,
        criteria=criteria,
        alternatives=alternatives,
        matrix_data=matrix_data
    )

# ─── Results Route ─────────────────────────────────────────────────────

@app.route('/problem/<int:problem_id>/results')
def view_results(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    criteria = problem.criteria.order_by(Criterion.rank_position).all()
    alternatives = problem.alternatives.all()
    
    # Rebuild consequence matrix data
    consequences = problem.consequences.all()
    conseq_grid = {}
    for c in consequences:
        conseq_grid[(c.alternative_id, c.criterion_id)] = c.value
        
    matrix_data = []
    for alt in alternatives:
        row = []
        for crit in criteria:
            row.append(conseq_grid.get((alt.id, crit.id), 0.0))
        matrix_data.append(row)
        
    criteria_types = [c.criteria_type for c in criteria]
    criteria_ids = [c.id for c in criteria]
    alternatives_ids = [a.id for a in alternatives]
    
    # Run solver
    try:
        if problem.method == 'smarts' or problem.method == 'smarter':
            res = solve_smarts_smarter(matrix_data, criteria_types, problem.preferences, criteria_ids, problem.method)
        elif problem.method == 'ahp':
            res = solve_ahp(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'macbeth':
            res = solve_macbeth(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'bwm':
            res = solve_bwm(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'bwt':
            res = solve_bwt(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'topsis':
            res = solve_topsis(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'vikor':
            res = solve_vikor(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'electre':
            res = solve_electre(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'promethee':
            res = solve_promethee(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        else:
            raise ValueError(f"Método desconhecido: {problem.method}")
            
        # Update weights in Database for querying/reporting
        for idx, cid in enumerate(criteria_ids):
            crit = Criterion.query.get(cid)
            crit.weight = res['weights'][idx]
        db.session.commit()
        
    except Exception as e:
        flash(f'Erro nos cálculos do método: {str(e)}', 'danger')
        return redirect(url_for('evaluate_method', problem_id=problem.id))
        
    # Process results for rendering
    # Pair alternatives with their scores and ranks
    results_list = []
    for idx, alt in enumerate(alternatives):
        results_list.append({
            'alternative': alt,
            'score': res['global_scores'][idx],
            'rank': res['ranks'][idx],
            'normalized_values': res['normalized_matrix'][idx]
        })
        
    # Sort by rank
    results_list = sorted(results_list, key=lambda x: x['rank'])
    
    # Highlight winner for Choice problematic
    winners = []
    if problem.problematic == 'choice' and results_list:
        max_score = results_list[0]['score']
        # Find all tied in first place
        winners = [r['alternative'].name for r in results_list if abs(r['score'] - max_score) < 1e-9]
        
    return render_template(
        'results.html',
        problem=problem,
        criteria=criteria,
        results=results_list,
        winners=winners,
        solver_res=res
    )

# ─── Sensitivity Analysis Routes ───────────────────────────────────────

@app.route('/problem/<int:problem_id>/sensitivity', methods=['GET', 'POST'])
def sensitivity_analysis(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    criteria = problem.criteria.order_by(Criterion.rank_position).all()
    alternatives = problem.alternatives.all()
    
    if request.method == 'POST':
        # Retrieve simulation parameters
        num_simulations = int(request.form.get('num_simulations', 10000))
        
        # Variations pct per criterion
        variations_pct = []
        for crit in criteria:
            val_pct = float(request.form.get(f'variation_{crit.id}', 10.0))
            variations_pct.append(val_pct)
            
        # Run Monte Carlo
        consequences = problem.consequences.all()
        conseq_grid = {}
        for c in consequences:
            conseq_grid[(c.alternative_id, c.criterion_id)] = c.value
            
        matrix_data = []
        for alt in alternatives:
            row = []
            for crit in criteria:
                row.append(conseq_grid.get((alt.id, crit.id), 0.0))
            matrix_data.append(row)
            
        criteria_types = [c.criteria_type for c in criteria]
        criteria_ids = [c.id for c in criteria]
        
        # Get current weights from database
        weights = [c.weight if c.weight is not None else 1.0/len(criteria) for c in criteria]
        
        try:
            sim_res = run_monte_carlo(
                matrix_data,
                criteria_types,
                weights,
                variations_pct,
                num_simulations,
                problem.method,
                problem.preferences,
                criteria_ids
            )
            
            # Map alternative names
            alt_names = [a.name for a in alternatives]
            sim_res['alternatives'] = alt_names
            
            return jsonify({'success': True, 'data': sim_res})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
            
    return render_template('sensitivity_input.html', problem=problem, criteria=criteria, alternatives=alternatives)

@app.route('/download/template')
def download_template():
    import io
    data = [
        ['Critério', 'Critério A', 'Critério B', 'Critério C'],
        ['Tipo', 1, 0, 1], # 1 = benefit, 0 = cost
        ['', '', '', ''],
        ['', '', '', ''],
        ['', '', '', ''],
        ['', '', '', ''],
        ['Níveis', 1, 1, 1],
        ['Alternativas', 'Critério A', 'Critério B', 'Critério C'],
        ['Alternativa 1', 10.0, 150.0, 0.8],
        ['Alternativa 2', 12.0, 120.0, 0.9],
        ['Alternativa 3', 8.5, 180.0, 0.7]
    ]
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False, sheet_name='Matriz de Consequências')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='modelo_matriz_tcc.xlsx'
    )

@app.route('/problem/<int:problem_id>/report/pdf')
def generate_results_pdf(problem_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    problem = DecisionProblem.query.filter_by(id=problem_id, user_id=user.id).first_or_404()
    criteria = problem.criteria.order_by(Criterion.rank_position).all()
    alternatives = problem.alternatives.all()
    
    consequences = problem.consequences.all()
    conseq_grid = {}
    for c in consequences:
        conseq_grid[(c.alternative_id, c.criterion_id)] = c.value
        
    matrix_data = []
    for alt in alternatives:
        row = []
        for crit in criteria:
            row.append(conseq_grid.get((alt.id, crit.id), 0.0))
        matrix_data.append(row)
        
    criteria_types = [c.criteria_type for c in criteria]
    criteria_ids = [c.id for c in criteria]
    alternatives_ids = [a.id for a in alternatives]
    
    # Run solver to get identical results
    try:
        if problem.method == 'smarts' or problem.method == 'smarter':
            res = solve_smarts_smarter(matrix_data, criteria_types, problem.preferences, criteria_ids, problem.method)
        elif problem.method == 'ahp':
            res = solve_ahp(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'macbeth':
            res = solve_macbeth(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'bwm':
            res = solve_bwm(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'bwt':
            res = solve_bwt(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'topsis':
            res = solve_topsis(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'vikor':
            res = solve_vikor(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'electre':
            res = solve_electre(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        elif problem.method == 'promethee':
            res = solve_promethee(matrix_data, criteria_types, problem.preferences, criteria_ids, alternatives_ids)
        else:
            raise ValueError(f"Método desconhecido: {problem.method}")
            
    except Exception as e:
        flash(f'Erro nos cálculos do relatório: {str(e)}', 'danger')
        return redirect(url_for('view_results', problem_id=problem.id))
        
    results_list = []
    for idx, alt in enumerate(alternatives):
        results_list.append({
            'alternative': alt,
            'score': res['global_scores'][idx],
            'rank': res['ranks'][idx],
            'normalized_values': res['normalized_matrix'][idx]
        })
    results_list = sorted(results_list, key=lambda x: x['rank'])
    
    # Generate PDF Report
    import io
    from sad_mcdm.services.pdf_generator import generate_results_report_pdf
    
    output = io.BytesIO()
    system_mode = app.config.get('SYSTEM_MODE', 'central')
    
    static_dir = os.path.join(app.root_path, 'static')
    generate_results_report_pdf(output, problem, criteria, results_list, res, system_mode, static_dir=static_dir)
    output.seek(0)
    
    filename = f"relatorio_decisao_{problem.id}.pdf"
    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/docs')
def docs_page():
    return render_template('docs.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
