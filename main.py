
from fastmcp import FastMCP # Creación del servidor MCP
from datetime import datetime, timedelta # Fechas y tiempos
from pathlib import Path # Manejo de rutas
import json 
import csv 

mcp = FastMCP(name='GastosMCP') # Inicializar MCP

EXPENSES_FILE = 'expenses.csv' # Ruta del archivo CSV
CSV_HEADERS = ['date', 'category', 'amount', 'payment_method', 'description'] # Encabezados CSV

# Valores válidos
CATEGORIES = ['Food', 'Transport', 'Entertainment', 'Utilities', 'Health', 'Education', 'Home', 'Other']
PAYMENT_METHODS = ['cash', 'card', 'debit', 'credit', 'transfer', 'digital_wallet']

# Mapa de traducciones a español usando diccionarios
CAT_ES = {
    'Food': 'Comida', 'Transport': 'Transporte', 'Entertainment': 'Entretenimiento',
    'Utilities': 'Servicios', 'Health': 'Salud', 'Education': 'Educación',
    'Home': 'Hogar', 'Other': 'Otros'
}

PAY_ES = {
    'cash': 'Efectivo', 'card': 'Tarjeta', 'debit': 'Débito',
    'credit': 'Crédito', 'transfer': 'Transferencia', 'digital_wallet': 'Billetera Digital'
}

# funciones auxiliares
def ensure_file():
    """Crea el archivo CSV si no existe."""
    if not Path(EXPENSES_FILE).exists(): # si no existe el archivo
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f: # Crear
            csv.writer(f).writerow(CSV_HEADERS)  # Escribir encabezados

def validate_date(date_str: str) -> tuple[bool, str]: # devuelve (valido, mensaje_error)
    """Valida formato y rango de fecha."""
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d') # Paesar string a fecha con formato YYYY-MM-DD
        now = datetime.now() # Fecha actual
        if d > now + timedelta(days=365): # Más de 1 año en el futuro
            return False, "Fecha muy lejana en el futuro."
        if d < now - timedelta(days=3650): # Más de 10 años en el pasado
            return False, "Fecha muy antigua (máx 10 años)."
        return True, ""
    except ValueError:
        return False, "Formato inválido. Use YYYY-MM-DD."

def validate_amount(amount: float) -> tuple[bool, str]: # devuelve (valido, mensaje_error)
    """Valida monto positivo y razonable."""
    if amount <= 0: # Monto negativo o cero
        return False, "Monto debe ser positivo."
    if amount > 1_000_000: # Monto mayor a 1 millón
        return False, "Monto excede límite ($1,000,000)."
    if round(amount, 2) != amount: # Más de 2 decimales
        return False, "Máximo 2 decimales."
    return True, ""

def sanitize(field: str) -> str:
    """Previene inyección CSV."""
    s = str(field)
    if s and s[0] in ['=', '+', '-', '@', '\t', '\r']: # Si inicia con aracteres peligrosos
        return "'" + s  # Se le antepone apóstrofe para neutralizarlos
    return s # Sino, devolver tal cual

# Herramientas (@mcp.tool)
@mcp.tool
def add_expense(date: str, category: str, amount: float, payment_method: str, description: str = "") -> str:
    """
    Agrega un gasto al archivo expenses.csv.
    
    Args:
        date: Fecha YYYY-MM-DD (ej: 2025-11-22)
        category: Food|Transport|Entertainment|Utilities|Health|Education|Home|Other
        amount: Monto positivo, máx 2 decimales
        payment_method: cash|card|debit|credit|transfer|digital_wallet
        description: Opcional, máx 200 caracteres
    """
    try:
        ensure_file() # Asegurar existencia del archivo
        
        # Validaciones
        ok, err = validate_date(date) # Validar fecha
        if not ok:
            return f"Error: {err}"
        
        if category not in CATEGORIES: # Validar categoría
            return f"Error: Categoría inválida. Use: {', '.join([CAT_ES[c] for c in CATEGORIES])}"
        
        ok, err = validate_amount(amount) # Validar monto
        if not ok:
            return f"Error: {err}"
        
        if payment_method not in PAYMENT_METHODS: # Validar método de pago
            return f"Error: Método inválido. Use: {', '.join([PAY_ES[m] for m in PAYMENT_METHODS])}"
        
        if len(description) > 200: # Validar longitud de descripción
            return "Error: Descripción muy larga (máx 200 caracteres)."
        
        # Escribir
        with open(EXPENSES_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([ # Escribir fila (sanitizado valores)
                sanitize(date), sanitize(category), f"{amount:.2f}",
                payment_method, sanitize(description)
            ])
        
        return (f"  Gasto registrado:\n" # Detalles del gasto agregado
                f" • Fecha: {date}\n"
                f" • Categoría: {CAT_ES[category]}\n"
                f" • Monto: ${amount:.2f}\n"
                f" • Método: {PAY_ES[payment_method]}"
                + (f"\n • Nota: {description}" if description else ""))
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def delete_expense(date: str, category: str, amount: float) -> str:
    """
    Elimina un gasto específico.
    
    Args:
        date: Fecha del gasto (YYYY-MM-DD)
        category: Categoría del gasto
        amount: Monto exacto
    """
    try:
        ensure_file() # Asegurar existencia del archivo
        expenses = [] # Lista para almacenar gastos a mantener
        found = False # bandera para saber si se encontró el gasto
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f) # Leer archivo
            headers = next(reader, None) # Leer encabezados
            
            for row in reader: # recorrer cada fila
                if len(row) >= 3: # Asegurar que tenga al menos 3 columnas (fecha, categoría, monto)
                    try: 
                        if (row[0] == date and row[1] == category and # Coincidencia exacta
                            abs(float(row[2]) - amount) < 0.01): # Comparar con tolerancia
                            found = True # Marcar como encontrado
                            continue
                    except ValueError:
                        pass
                expenses.append(row) # Mantener fila si no coincide
        
        if not found:
            return f"Gasto no encontrado: {date} - {CAT_ES.get(category, category)} - ${amount:.2f}"
        
        with open(EXPENSES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f) # Reescribir archivo
            if headers: # Escribir encabezados si existen
                writer.writerow(headers)
            writer.writerows(expenses) # Escribir gastos restantes
        
        return f"Gasto eliminado: {date} - {CAT_ES[category]} - ${amount:.2f}"
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool
def get_summary(days: int = 7) -> str:
    """
    Resumen de gastos de los últimos N días.
    
    Args:
        days: Días hacia atrás (1-365, default 7)
    """
    try:
        ensure_file() # Asegurar existencia del archivo
        
        if not 1 <= days <= 365: # Validar rango de días (1-365)
            return " Días debe estar entre 1 y 365."
        
        cutoff = datetime.now() - timedelta(days=days) # Fecha límite (de ahora hasta N días atrás)
        total = 0.0
        by_cat = {} # Gastos por categoría (diccionario)
        by_pay = {} # Gastos por método de pago (diccionario)
        count = 0   # Contador de transacciones
        recent = [] # Lista de gastos recientes
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f) # Leer archivo
            next(reader, None) # Saltar encabezados
            
            for row in reader: # recorrer cada fila
                if len(row) >= 4: # Asegurar que tenga al menos 4 columnas (fecha, categoría, monto, método)
                    try: 
                        exp_date = datetime.strptime(row[0].strip(), '%Y-%m-%d') # Parsear fecha (YYYY-MM-DD)
                        amt = float(row[2].strip()) # Parsear monto
                        cat = row[1].strip() # Categoría
                        pay = row[3].strip() # Método de pago
                        
                        if exp_date >= cutoff: # Si está dentro del rango de días
                            total += amt # Sumar al total
                            count += 1   # Incrementar contador
                            by_cat[cat] = by_cat.get(cat, 0) + amt # Sumar por categoría
                            by_pay[pay] = by_pay.get(pay, 0) + amt # Sumar por método de pago
                            recent.append({'date': row[0], 'cat': cat, 'amt': amt, 'pay': pay}) # Agregar a recientes
                    except:
                        continue
        
        if count == 0: # Si no hay gastos
            return f" No hay gastos en los últimos {days} días."
        
        recent.sort(key=lambda x: x['date'], reverse=True) # Ordenar recientes por fecha descendente
        
        res = f" **Resumen - Últimos {days} Días**\n\n"
        res += f" Total: ${total:.2f}\n"
        res += f" Transacciones: {count}\n"
        res += f" Promedio: ${total/count:.2f}\n\n"
        
        res += " **Por Categoría:**\n" # Desglose por categoría 
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = (amt/total)*100
            res += f"  • {CAT_ES.get(cat, cat)}: ${amt:.2f} ({pct:.1f}%)\n"
        
        res += "\n **Por Método:**\n" # Desglose por método de pago
        for pay, amt in sorted(by_pay.items(), key=lambda x: x[1], reverse=True):
            pct = (amt/total)*100
            res += f"  • {PAY_ES.get(pay, pay)}: ${amt:.2f} ({pct:.1f}%)\n"
        
        res += "\n **Recientes:**\n" # Últimos 5 gastos
        for exp in recent[:5]:
            res += f"  • {exp['date']} — {CAT_ES.get(exp['cat'], exp['cat'])} — ${exp['amt']:.2f}\n"
        
        return res
    
    except Exception as e:
        return f" Error: {str(e)}"

@mcp.tool
def check_budget(category: str, limit: float, days: int = 30) -> str:
    """
    Verifica estado de presupuesto de una categoría.
    
    Args:
        category: Categoría a verificar
        limit: Límite de presupuesto
        days: Período en días (default 30)
    """
    try:
        ensure_file() # Asegurar existencia del archivo
        
        if category not in CATEGORIES: # Validar categoría
            return f" Categoría inválida. Use: {', '.join([CAT_ES[c] for c in CATEGORIES])}"
        
        ok, err = validate_amount(limit) # Validar límite del presupuesto
        if not ok: 
            return f" Límite inválido: {err}"
        
        cutoff = datetime.now() - timedelta(days=days) # Fecha límite (de ahora hasta N días atrás)
        cat_total = 0.0 # Total gastado en la categoría
        count = 0       # Contador de transacciones en la categoría
        
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f) # Leer archivo
            next(reader, None) # Saltar encabezados
            
            for row in reader: # recorrer cada fila
                if len(row) >= 3: # Asegurar que tenga al menos 3 columnas (fecha, categoría, monto)
                    try:
                        exp_date = datetime.strptime(row[0].strip(), '%Y-%m-%d') # Parsear fecha (YYYY-MM-DD)
                        if exp_date >= cutoff and row[1].strip() == category: # Si está dentro del rango y categoría coincide
                            cat_total += float(row[2].strip()) # Sumar al total de la categoría
                            count += 1   # Incrementar contador
                    except:
                        continue
        
        pct = (cat_total/limit)*100 # Porcentaje del presupuesto usado
        remaining = limit - cat_total # Monto restante
        
        if pct < 70:
            status = "Dentro del presupuesto"
        elif pct < 90:
            status = "Acercándose al límite"
        elif pct < 100:
            status = "Cerca del límite"
        else:
            status = "Presupuesto excedido"
        
        res = f" **Presupuesto - {CAT_ES[category]}**\n\n"
        res += f" Período: {days} días\n"
        res += f" Presupuesto: ${limit:.2f}\n"
        res += f" Gastado: ${cat_total:.2f} ({pct:.1f}%)\n"
        res += f" Restante: ${remaining:.2f}\n"
        res += f" Transacciones: {count}\n"
        res += f" {status}\n"
        
        if pct > 80:
            res += f"\n Considera reducir gastos en {CAT_ES[category]}."
        
        return res
    
    except Exception as e:
        return f" Error: {str(e)}"

# Recursos (@mcp.resource)
@mcp.resource("resources://expenses")
def get_expenses() -> str:
    """Devuelve todos los gastos en formato JSON."""
    records = [] # Lista para almacenar registros de gastos
    try:
        ensure_file() # Asegurar existencia del archivo
        with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f) # Leer archivo
            next(reader, None) # Saltar encabezados
            for row in reader: # recorrer cada fila
                if len(row) >= 4: # Asegurar que tenga al menos 4 columnas (fecha, categoría, monto, método)
                    try:
                        records.append({ # Agregar registro a la lista (Formato JSON)
                            'date': row[0].strip(), 
                            'category': row[1].strip(),
                            'amount': float(row[2].strip()),
                            'payment_method': row[3].strip(),
                            'description': row[4].strip() if len(row) > 4 else ""
                        })
                    except:
                        continue
    except:
        pass
    return json.dumps(records, ensure_ascii=False) # Devolver como JSON

@mcp.resource("resources://categories")
def get_categories() -> str:
    """Devuelve categorías válidas en JSON bilingüe."""
    return json.dumps([ # Lista de categorías en formato JSON
        {'id': c, 'english': c, 'spanish': CAT_ES[c]} # Lista de categorías (id, inglés, español)
        for c in CATEGORIES
    ], ensure_ascii=False) # Permitir caracteres especiales

@mcp.resource("resources://payment_methods")
def get_payment_methods() -> str:
    """Devuelve métodos de pago válidos en JSON bilingüe."""
    return json.dumps([ # Lista de métodos de pago en formato JSON
        {'id': m, 'english': m, 'spanish': PAY_ES[m]} # Lista de métodos de pago (id, inglés, español)  
        for m in PAYMENT_METHODS
    ], ensure_ascii=False) # Permitir caracteres especiales

# Prompts (@mcp.prompt)
@mcp.prompt
def expense_analyst() -> str:
    """Prompt para análisis de gastos."""
    return """Eres un Asistente de Gastos. SIEMPRE obtén datos con get_expenses() primero.

ANÁLISIS (últimos 7 días por defecto):
- Si NO hay gastos: responde " No hay gastos en los últimos [N] días." y detente.
- Si hay gastos: muestra total, desglose por categoría/método (con %), transacciones, promedio, y 5 gastos recientes.

FORMATO:
- Todo en español
- Traduce categorías/métodos
- Números: $XX.XX y porcentajes
- Conciso pero completo

HERRAMIENTAS:
- add_expense(): agregar gasto
- delete_expense(): eliminar gasto
- get_summary(days): resumen rápido
- check_budget(): verificar presupuesto

NO expliques procesos técnicos. Sé directo y útil."""

@mcp.prompt
def budget_advisor() -> str:
    """Prompt para asesoría de presupuesto."""
    return """Eres un Asesor Financiero. Analiza gastos con get_expenses() y proporciona:

ANÁLISIS:
- Categorías con mayor gasto
- Patrones y tendencias
- Áreas de optimización

RECOMENDACIONES:
- Límites de presupuesto razonables
- Oportunidades de ahorro concretas
- Acciones específicas

FORMATO:
- Tono amigable y motivador
- Datos reales (no generalices)
- Español, números claros

USA: get_summary(), check_budget()

Sé específico y accionable."""

# Ejecutar MCP
if __name__ == "__main__":
    ensure_file()
    mcp.run()
