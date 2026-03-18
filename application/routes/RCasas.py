from flask import render_template, request, Blueprint, jsonify, session
import infrasture.model.MCasas as MCasas
import domain.VCasas as VCasas
from domain.VPermisos import requiere_permiso
import os
from werkzeug.utils import secure_filename
from fpdf import FPDF
from datetime import datetime
from flask import send_file
import io

bp = Blueprint('RCasas', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', '..', 'presentation', 'static', 'uploads', 'logos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Vistas ─────────────────────────────────────────────

@bp.route('/casas')
def casas():
    return render_template('Casas/Casas.html', active_page='casas')

@bp.route('/casa/<casa_id>')
def detalle_casa(casa_id):
    return render_template('Casas/Casas.html', casa_id=casa_id, active_page='casas')

# ── API JSON ────────────────────────────────────────────

@bp.route('/get_casas', methods=['GET'])
def get_casas():
    try:
        query = request.args.get('q', '').strip()
        casas_list = MCasas.getAllCasas(query if query else None)
        result = []
        for c in casas_list:
            result.append({
                '_id': str(c['_id']),
                'nombre': c.get('nombre', ''),
                'telefono': c.get('telefono', ''),
                'direccion': c.get('direccion', ''),
                'web': c.get('web', ''),
                'correo': c.get('correo', ''),
                'ciudad': c.get('ciudad', ''),
                'historia': c.get('historia', ''),
                'logo_filename': c.get('logo_filename', ''),
                'contacto': c.get('contacto', ''),
                'telefono_contacto': c.get('telefono_contacto', ''),
            })
        return jsonify({"success": True, "casas": result})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/get_casa/<casa_id>', methods=['GET'])
def get_casa(casa_id):
    try:
        casa_data = MCasas.getCasaById(casa_id)
        validator = VCasas.getCasaValidator(casa_data)
        casa = validator.validation()
        return jsonify({
            "success": True,
            "casa": {
                '_id': str(casa['_id']),
                'nombre': casa.get('nombre', ''),
                'telefono': casa.get('telefono', ''),
                'direccion': casa.get('direccion', ''),
                'web': casa.get('web', ''),
                'correo': casa.get('correo', ''),
                'ciudad': casa.get('ciudad', ''),
                'historia': casa.get('historia', ''),
                'logo_filename': casa.get('logo_filename', ''),
                'contacto': casa.get('contacto', ''),
                'telefono_contacto': casa.get('telefono_contacto', ''),
            }
        })
    except LookupError as exc:
        return jsonify({"success": False, "message": str(exc)}), 404
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/upload_logo', methods=['POST'])
@requiere_permiso('casas', 'crear')
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({"success": False, "message": "No se envió archivo"}), 400
    file = request.files['logo']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Archivo no válido"}), 400
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({"success": True, "filename": filename})

@bp.route('/create_casa', methods=['POST'])
@requiere_permiso('casas', 'crear')
def create_casa():
    try:
        data = request.get_json(silent=True)
        validator = VCasas.createCasaValidator(isJson=request.is_json, payLoad=data)
        casa_data = validator.validation()
        result = MCasas.createCasa(casa_data)
        return jsonify({
            "success": True,
            "message": "Casa Salesiana creada exitosamente",
            "casa_id": str(result.inserted_id)
        }), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/update_casa/<casa_id>', methods=['PUT'])
@requiere_permiso('casas', 'editar')
def update_casa(casa_id):
    try:
        data = request.get_json(silent=True)
        validator = VCasas.updateCasaValidator(isJson=request.is_json, payLoad=data)
        casa_data = validator.validation()
        result = MCasas.updateCasa(casa_id, casa_data)
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Casa actualizada exitosamente"})
        return jsonify({"success": False, "message": "No se realizaron cambios"}), 200
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

@bp.route('/delete_casa/<casa_id>', methods=['DELETE'])
@requiere_permiso('casas', 'eliminar')
def delete_casa(casa_id):
    try:
        result = MCasas.deleteCasa(casa_id)
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Casa eliminada exitosamente"})
        return jsonify({"success": False, "message": "Casa no encontrada"}), 404
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500

class PDF(FPDF):
    def header(self):
        # Logo placeholder / Institutional Text
        self.set_font("helvetica", "B", 12)
        self.set_text_color(44, 62, 80) # SDB Blue
        self.cell(0, 10, "CONGREGACIÓN SALESIANA", ln=True, align='L')
        
        self.set_font("helvetica", "", 10)
        self.cell(0, 5, "INSPECTORÍA SAN JUAN BOSCO - JARABACOA", ln=True, align='L')
        
        # Right-aligned Title
        self.set_y(10)
        self.set_font("helvetica", "B", 14)
        self.set_text_color(220, 30, 70) # SDB Red
        self.cell(0, 15, "DIRECTORIO DE OBRAS", ln=True, align='R')
        
        # Line
        self.set_draw_color(220, 30, 70)
        self.set_line_width(0.8)
        self.line(10, 28, 200, 28)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align='C')
        self.cell(0, 10, "Agenda SDB - Sistema de Gestión", align='R')

@bp.route('/reporte_casas')
def reporte_casas():
    try:
        casas_list = MCasas.getAllCasas()
        
        # Create PDF instance
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report Date
        pdf.set_font("helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 8, f"Fecha de emisión: {now}", ln=True, align='R')
        pdf.ln(2)
        
        # Table Header
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(44, 62, 80) # SDB Blue Header
        pdf.set_text_color(255, 255, 255)
        
        # Column widths
        w = [55, 35, 45, 55] # Total ~190
        
        cols = ["Nombre de la Casa", "Ciudad", "Teléfono", "Contacto"]
        for i in range(len(cols)):
            pdf.cell(w[i], 10, cols[i], border=1, fill=True, align='C')
        pdf.ln()
        
        # Table Body
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        
        fill = False
        for c in casas_list:
            # Alternating background color (Zebra)
            if fill:
                pdf.set_fill_color(248, 249, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            
            # Clean data and truncate if necessary
            nombre = c.get('nombre', '').strip()[:35]
            ciudad = c.get('ciudad', '').strip()[:20]
            tel = c.get('telefono', '').strip()[:20]
            cont = c.get('contacto', '').strip()[:30]
            
            # Draw cells
            pdf.cell(w[0], 8, nombre, border=1, fill=True)
            pdf.cell(w[1], 8, ciudad, border=1, fill=True)
            pdf.cell(w[2], 8, tel, border=1, fill=True)
            pdf.cell(w[3], 8, cont, border=1, fill=True)
            pdf.ln()
            
            fill = not fill # Switch for next row
            
        # Output to buffer
        output = io.BytesIO()
        pdf_content = pdf.output()
        output.write(pdf_content)
        output.seek(0)
        
        filename = f"Reporte_Casas_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as exc:
        print(f"Error generando reporte: {exc}")
        return "Error al generar el reporte", 500

@bp.route('/reporte_casa/<casa_id>')
def reporte_casa(casa_id):
    try:
        casa = MCasas.getCasaById(casa_id)
        if not casa:
            return "Casa no encontrada", 404
            
        # Create PDF instance
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Report Date
        pdf.set_font("helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 8, f"Ficha generada el: {now}", ln=True, align='R')
        pdf.ln(5)
        
        # Title
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, casa.get('nombre', 'Detalle de la Casa'), ln=True, align='C')
        pdf.ln(10)
        
        # Info sections
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  Información General", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        details = [
            ("Ciudad:", casa.get('ciudad', '—')),
            ("Teléfono:", casa.get('telefono', '—')),
            ("Dirección:", casa.get('direccion', '—')),
            ("Sitio Web:", casa.get('web', '—')),
            ("Correo:", casa.get('correo', '—')),
        ]
        
        for label, value in details:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(40, 8, label)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 8, str(value), ln=True)
            
        pdf.ln(5)
        
        # Contact section
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  Información de Contacto", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(40, 8, "Persona:")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, str(casa.get('contacto', '—')), ln=True)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(40, 8, "Teléfono:")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, str(casa.get('telefono_contacto', '—')), ln=True)
        
        pdf.ln(10)
        
        # History section
        historia = casa.get('historia', '').strip()
        if historia:
            pdf.set_font("helvetica", "B", 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, "  Reseña Histórica", ln=True, fill=True)
            pdf.ln(4)
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 6, historia)
            
        # Buffer
        output = io.BytesIO()
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        
        clean_name = secure_filename(casa.get('nombre', 'Casa'))
        filename = f"Reporte_{clean_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as exc:
        print(f"Error generando reporte de casa: {exc}")
        return "Error al generar el reporte", 500
