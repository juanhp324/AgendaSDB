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
        
        obras = self.payLoad.get('obras', [])
        if not isinstance(obras, list):
            obras = []
            
        return {
            'nombre': nombre,
            'historia': self.payLoad.get('historia', '').strip(),
            'tipo': self.payLoad.get('tipo', 'masculino').lower(),
            'obras': obras
        }


class updateCasaValidator:
    def __init__(self, isJson, payLoad):
        self.isJson = isJson
        self.payLoad = payLoad or {}

    def validation(self):
        if not self.isJson:
            raise ValueError("Se espera JSON")
            
        allowed = ['nombre', 'historia', 'obras', 'tipo']
        data = {}
        
        for k, v in self.payLoad.items():
            if k in allowed:
                if isinstance(v, str):
                    data[k] = v.strip()
                else:
                    data[k] = v
                    
        if not data:
            raise ValueError("No hay datos para actualizar")
            
        if 'obras' in data and not isinstance(data['obras'], list):
            data['obras'] = []
            
        return data
