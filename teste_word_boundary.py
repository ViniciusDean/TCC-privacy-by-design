"""
teste_word_boundary.py
Valida que 'age' em 'user_agent' NÃO gera falso positivo após correção do Bug 2.
"""

# Antes da correção, isso geraria alerta falso:
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  # ❌ Gerava DADO_HARDCODED falso

# Mas 'age' como campo sensível isolado ainda deve gerar alerta:
idade = 25  # Não hardcoded, variável numérica — OK
user_age = input("Digite a idade: ")  # Não literal — OK

# Apenas isso deve gerar alerta (valor literal em campo sensível):
age_literal = "25"  # ✅ Isso SIM deve gerar DADO_HARDCODED

# Compostos com 'age' que NÃO são campo sensível isolado (após Bug 2):
message_age = "Mensagem com age"  # OK - 'age' está dentro de 'message_age'
average_age_group = 30  # OK - 'age' está dentro de 'average_age_group'
