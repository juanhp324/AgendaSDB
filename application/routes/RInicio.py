from flask import render_template, Blueprint, session

bp = Blueprint('RInicio', __name__)

@bp.route('/inicio')
def inicio():
    return render_template('Inicio.html', active_page='inicio')
