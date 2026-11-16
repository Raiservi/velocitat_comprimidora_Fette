import sqlite3

#Creem conexio i cursor

conexion = sqlite3.connect("bbdd_fettes.db")
cursor = conexion.cursor()

# creem BBDD amb la primera taula.
cursor.execute ("""
    CREATE TABLE IF NOT EXISTS fettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lote TEXT NOT NULL,
        equipo TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        produccion_total REAL,
        velocidad_promedio REAL
    )
""")

# Insertar valors de proba
cursor.execute("""
    INSERT INTO fettes (lote, equipo, fecha_inicio, fecha_fin,produccion_total,velocidad_promedio) 
    VALUES (?, ?, ? ,? ,? ,?)
""", ("325600", "Fette_1200_1", "2026-01-12", "2026-01-13",2300,23.1))

# Guardar canvis
conexion.commit()

# Llegim valors de proba
cursor.execute("SELECT * FROM fettes")
resultados = cursor.fetchall()

for fila in resultados:
    print(fila)  

# Tancar conexio
conexion.close()
