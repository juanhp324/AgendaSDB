from flask import render_template, request, Blueprint, jsonify, session, current_app
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
        tipo = request.args.get('tipo', 'todos').strip()
        print(f"DEBUG: get_casas received tipo='{tipo}', q='{query}'")
        casas_list = MCasas.getAllCasas(query if query else None, tipo)
        print(f"DEBUG: Found {len(casas_list)} casas")
        result = []
        for c in casas_list:
            print(f"DEBUG: Casa '{c.get('nombre')}' has tipo='{c.get('tipo')}'")
            result.append({
                '_id': str(c['_id']),
                'nombre': c.get('nombre', ''),
                'obras': c.get('obras', []),
                'historia': c.get('historia', ''),
                'tipo': c.get('tipo', 'masculino')
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
                'obras': casa.get('obras', []),
                'historia': casa.get('historia', ''),
                'tipo': casa.get('tipo', 'masculino')
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
        import os
        # Logo Image
        logo_path = os.path.join(current_app.root_path, 'presentation', 'static', 'img', 'logo_sdb.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 20)
            
        # Institutional Text shifted to the right
        self.set_y(12)
        self.set_x(33)
        self.set_font("helvetica", "B", 12)
        self.set_text_color(44, 62, 80) # SDB Blue
        self.cell(0, 6, "CONGREGACIÓN SALESIANA", ln=True, align='L')
        
        self.set_x(33)
        self.set_font("helvetica", "", 10)
        self.cell(0, 5, "INSPECTORÍA SAN JUAN BOSCO - JARABACOA", ln=True, align='L')
        
        # Right-aligned Title
        self.set_y(12)
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
        
        # Table Header Configuration
        cols = ["Nombre de la Obra", "Ciudad", "Teléfono", "Contacto"]
        w = [60, 35, 40, 55] # Widths for columns
        
        for c in casas_list:
            nombre_casa = c.get('nombre', '').strip()
            obras = c.get('obras', [])
            
            # 1. Casa Header Row (Full Width)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_fill_color(44, 62, 80) # SDB Blue
            pdf.set_text_color(255, 255, 255)
            pdf.cell(sum(w), 9, f" CASA: {nombre_casa.upper()}", border=1, ln=True, fill=True, align='L')
            
            # 2. Sub-header for Columns
            pdf.set_font("helvetica", "B", 9)
            pdf.set_fill_color(220, 30, 70) # SDB Red
            pdf.set_text_color(255, 255, 255)
            for i in range(len(cols)):
                pdf.cell(w[i], 8, cols[i], border=1, fill=True, align='C')
            pdf.ln()
            
            # 3. Obras Rows
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            
            if not obras:
                pdf.set_fill_color(255, 255, 255)
                pdf.cell(w[0], 8, " (Sin obras registradas)", border=1, fill=True)
                pdf.cell(w[1], 8, "—", border=1, fill=True, align='C')
                pdf.cell(w[2], 8, "—", border=1, fill=True, align='C')
                pdf.cell(w[3], 8, "—", border=1, fill=True, align='C')
                pdf.ln()
            else:
                fill = False
                for o in obras:
                    if fill:
                        pdf.set_fill_color(248, 249, 250)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                    
                    nombre_obra = (o.get('nombre_obra') or '—')[:40]
                    # Ciudad + Apartado Postal
                    ap = o.get('apartado_postal')
                    ciudad_text = o.get('ciudad') or '—'
                    if ap:
                        ciudad_text = f"{ciudad_text} (AP: {ap})"
                    ciudad = str(ciudad_text)[:20]
                    
                    # Teléfono(s)
                    telfs = o.get('telefono', [])
                    if isinstance(telfs, list):
                        tel = ", ".join([str(t) for t in telfs])[:20]
                    else:
                        tel = str(telfs)[:20] if telfs else "—"
                        
                    cont = (o.get('contacto') or '—')[:30]
                    
                    pdf.cell(w[0], 8, f" {nombre_obra}", border=1, fill=True)
                    pdf.cell(w[1], 8, ciudad, border=1, fill=True, align='C')
                    pdf.cell(w[2], 8, tel, border=1, fill=True, align='C')
                    pdf.cell(w[3], 8, cont, border=1, fill=True)
                    pdf.ln()
                    fill = not fill
            
            pdf.ln(4) # Space between Casas
            
        # Output to buffer
        # Output PDF as a stream
        output = io.BytesIO()
        pdf_output = pdf.output()
        output.write(pdf_output)
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
        
        # History section
        historia = casa.get('historia', '').strip()
        if historia:
            pdf.set_font("helvetica", "B", 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, "  Reseña Histórica", ln=True, fill=True)
            pdf.ln(4)
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 6, historia)
            pdf.ln(5)

        # Obras
        obras = casa.get('obras', [])
        if obras:
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(220, 30, 70)
            pdf.cell(0, 10, "Obras Asociadas", ln=True)
            pdf.set_text_color(0, 0, 0)
            
            for o in obras:
                detalles_obra = [
                    ("Ciudad:", o.get('ciudad', '—')),
                    ("Teléfono:", o.get('telefono', '—')),
                    ("Dirección:", o.get('direccion', '—')),
                    ("Sitio Web:", o.get('web', '—')),
                    ("Correo:", o.get('correo', '—')),
                    ("Persona Contacto:", o.get('contacto', '—')),
                    ("Tlf. Contacto:", o.get('telefono_contacto', '—'))
                ]
                
                # Calcular altura necesaria: Cabecera(10) + Espacio(2) + Detalles(8 cada uno) + Margen(5)
                valid_detalles = [v for l, v in detalles_obra if v and str(v).strip() != '—']
                needed_h = 10 + 2 + (len(valid_detalles) * 8) + 5
                
                if pdf.get_y() + needed_h > 275: # Umbral para página A4
                    pdf.add_page()

                pdf.set_font("helvetica", "B", 12)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 10, f"  {o.get('nombre_obra', 'Obra')}", ln=True, fill=True)
                pdf.ln(2)
                
                for label, value in detalles_obra:
                    if value and str(value).strip() != '—':
                        pdf.set_font("helvetica", "B", 10)
                        pdf.cell(40, 8, label)
                        pdf.set_font("helvetica", "", 10)
                        pdf.cell(0, 8, str(value), ln=True)
                pdf.ln(5)
            
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

@bp.route('/reporte_obra/<casa_id>/<obra_id>')
def reporte_obra(casa_id, obra_id):
    try:
        casa = MCasas.getCasaById(casa_id)
        if not casa:
            return "Casa no encontrada", 404
            
        obras = casa.get('obras', [])
        obra_data = next((o for o in obras if o.get('id') == obra_id), None)
        if not obra_data:
            return "Obra no encontrada", 404
            
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
        pdf.cell(0, 10, obra_data.get('nombre_obra', 'Detalle de la Obra'), ln=True, align='C')
        
        # Subtitle Casa Perteneciente
        casa_nombre = (casa.get('nombre') or '—') if casa else "—"
        pdf.cell(0, 8, f"Perteneciente a: {casa_nombre}", ln=True, align='C')
        pdf.ln(10)
        
        # Info sections
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  Información General", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        telfs = obra_data.get('telefono', [])
        if isinstance(telfs, list):
            telf_str = ", ".join([str(t) for t in telfs])
        else:
            telf_str = str(telfs) if telfs else "—"

        details = [
            ("Ciudad:", obra_data.get('ciudad', '—')),
            ("Apartado Postal:", obra_data.get('apartado_postal', '—')),
            ("Teléfonos:", telf_str),
            ("Dirección:", obra_data.get('direccion', '—')),
            ("Sitio Web:", obra_data.get('web', '—')),
            ("Correo:", obra_data.get('correo', '—')),
        ]
        
        for label, value in details:
            if value and str(value).strip() != '—':
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
        pdf.cell(0, 8, str(obra_data.get('contacto', '—')), ln=True)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(40, 8, "Teléfono:")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, str(obra_data.get('telefono_contacto', '—')), ln=True)
        
        # Buffer
        output = io.BytesIO()
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        
        clean_name = secure_filename(obra_data.get('nombre_obra', 'Obra'))
        filename = f"Reporte_{clean_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as exc:
        print(f"Error generando reporte de obra: {exc}")
        return "Error al generar el reporte", 500
