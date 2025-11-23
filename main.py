from fastmcp import FastMCP # Importa la clase FastMCP
from datetime import datetime # Importa datetime para validación de fechas
import json

# Crea una instancia de FastMCP con el nombre 'GastosMCP' del servidor MCP
mcp = FastMCP(name = 'GastosMCP') 

# Herramienta para agregar gastos
@mcp.tool
def add_expense(date: str, category: str, amount: float, payment_method: str):
    """
    Agrega un gasto al archivo expenses.csv.
    """
    with open('expenses.csv', 'a') as file:
        try: 
            # Validaciones                                  
            if category not in ['Food', 'Transport', 'Entertainment', 'Utilities', 'Health', 'Education', 'Other']:
                return "Categoría inválida."
            
            if amount <= 0:
                return "El monto debe ser positivo."
            
            if payment_method not in ['cash', 'card', 'transfer']:
                return "Método de pago inválido."
            
            datetime.strptime(date, '%Y-%m-%d')  # Verifica formato de fecha
            
            # Agrega el gasto al archivo
            file.write(f"{date},{category},{amount:.2f},{payment_method}\n")
            
        except ValueError:
            return "Formato de fecha inválido. Use YYYY-MM-DD."
        
    return "Gasto agregado exitosamente."

# Recurso para acceder al archivo de gastos
@mcp.resource("resources://expenses")
def get_expenses_file():
    """
    Devuelve todos los gastos contenidos en `expenses.csv` como una cadena JSON.
    La salida es una lista de objetos con las claves: `date`, `category`, `amount`, `payment_method`.
    """
    records = []
    try:
        with open('expenses.csv', 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                # Ignora la cabecera si está presente
                if line.lower().startswith('date,'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 4:
                    continue
                date, category, amount_str, payment_method = parts[0], parts[1], parts[2], parts[3]
                try:
                    amount = float(amount_str)
                except Exception:
                    try:
                        amount = float(amount_str.replace('$', '').replace(',', ''))
                    except Exception:
                        amount = None

                records.append({
                    'date': date,
                    'category': category,
                    'amount': amount,
                    'payment_method': payment_method
                })
    except FileNotFoundError:
        return json.dumps([], ensure_ascii=False)

    return json.dumps(records, ensure_ascii=False)

# Prompt del asistente
@mcp.prompt
def expense_report_prompt():
    return """
    Asistente de gastos personales.

    Antes de analizar, llama a `get_expenses_file()` (recurso `resources://expenses`) y úsalo como única fuente de datos.

    Filtra registros de los últimos 7 días (incluye hoy). Si no hay registros en ese rango, responde exactamente: "No hay gastos en los últimos 7 días." y nada más.

    Con los registros filtrados, responde en español (solo texto, sin código ni plantillas):
    - Total gastado.
    - Total por categoría.
    - Número de transacciones.
    - Promedio por transacción.
    - Hasta 5 gastos más recientes en formato: YYYY-MM-DD — Categoría — Monto — Método.
    - 1–3 frases cortas de observaciones relevantes.

    No pidas ni muestres instrucciones para `add_expense` ni expliques el procesamiento.
    """

if __name__ == "__main__":
    mcp.run() # Ejecuta el servidor MCP
