from flask import render_template, Blueprint

bp = Blueprint('RDerechos', __name__)

@bp.route('/derechos')
def derechos():
    return render_template('Derechos.html', active_page='derechos')
