from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from models import SecurityQuestion

bp = Blueprint('company', __name__, url_prefix='/company')

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('This training account is recovered through the Forgot Login challenge.', 'info')
    return render_template('company/login.html')

@bp.route('/forgot-login', methods=['GET', 'POST'])
def forgot_login():
    questions = SecurityQuestion.query.order_by(SecurityQuestion.position, SecurityQuestion.id).all()
    if request.method == 'POST':
        if not questions:
            flash('The administrator has not configured any questions yet.', 'error')
        else:
            wrong = []
            for q in questions:
                answer = request.form.get(f'answer_{q.id}', '')
                if not q.matches(answer):
                    wrong.append(q.prompt)
            if not wrong:
                session['challenge_complete'] = True
                return redirect(url_for('company.success'))
            for prompt in wrong:
                flash(f'Input for “{prompt}” not recognised.', 'error')
    return render_template('company/forgot_login.html', questions=questions)

@bp.get('/success')
def success():
    if not session.get('challenge_complete'):
        return redirect(url_for('company.forgot_login'))
    return render_template('company/success.html')

@bp.post('/restart')
def restart():
    session.pop('challenge_complete', None)
    return redirect(url_for('company.login'))
