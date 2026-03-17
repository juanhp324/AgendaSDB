class getCasaValidator:
    def __init__(self, casa_data):
        self.casa_data = casa_data

    def validation(self):
        if not self.casa_data:
            raise LookupError("Casa Salesiana no encontrada")
        return self.casa_data


class createCasaValidator:
    def __init__(self, isJson, payLoad):
        self.isJson = isJson
        self.payLoad = payLoad or {}

    def validation(self):
        if not self.isJson:
            raise ValueError("Se espera JSON")
        nombre = self.payLoad.get('nombre', '').strip()
        if not nombre:
            raise ValueError("El campo 'nombre' es obligatorio")
        return {
            'nombre': nombre,
            'telefono': self.payLoad.get('telefono', '').strip(),
            'direccion': self.payLoad.get('direccion', '').strip(),
            'web': self.payLoad.get('web', '').strip(),
            'correo': self.payLoad.get('correo', '').strip(),
            'ciudad': self.payLoad.get('ciudad', '').strip(),
            'historia': self.payLoad.get('historia', '').strip(),
            'logo_filename': self.payLoad.get('logo_filename', '').strip(),
            'contacto': self.payLoad.get('contacto', '').strip(),
            'telefono_contacto': self.payLoad.get('telefono_contacto', '').strip(),
        }


class updateCasaValidator:
    def __init__(self, isJson, payLoad):
        self.isJson = isJson
        self.payLoad = payLoad or {}

    def validation(self):
        if not self.isJson:
            raise ValueError("Se espera JSON")
        allowed = ['nombre', 'telefono', 'direccion', 'web', 'correo', 'ciudad',
                   'historia', 'logo_filename', 'contacto', 'telefono_contacto']
        data = {k: v.strip() if isinstance(v, str) else v
                for k, v in self.payLoad.items() if k in allowed}
        if not data:
            raise ValueError("No hay datos para actualizar")
        return data
