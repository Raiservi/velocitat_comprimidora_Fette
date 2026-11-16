import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class VisorSQLite:
    def __init__(self, root):
        self.root = root
        self.root.title("Visor SQLite Local")
        self.root.geometry("850x500")
        self.conexion = None

        # Barra superior amb botons i selector de taules
        frame_top = tk.Frame(root, pady=10, padx=10)
        frame_top.pack(fill=tk.X)

        btn_abrir = tk.Button(frame_top, text="📂 Obrir Base de Dades (.db)", command=self.abrir_db, bg="#0078D7", fg="white", padx=10)
        btn_abrir.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(frame_top, text="Selecciona una taula:").pack(side=tk.LEFT)
        self.combo_tablas = ttk.Combobox(frame_top, state="readonly", width=30)
        self.combo_tablas.pack(side=tk.LEFT, padx=5)
        self.combo_tablas.bind("<<ComboboxSelected>>", self.cargar_datos)

        btn_refrescar = tk.Button(frame_top, text="🔄 Actualitzar", command=self.cargar_datos)
        btn_refrescar.pack(side=tk.LEFT, padx=5)

        # Taula central amb barres de desplaçament
        frame_tabla = tk.Frame(root, padx=10, pady=5)
        frame_tabla.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(frame_tabla, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def abrir_db(self):
        ruta = filedialog.askopenfilename(
            title="Selecciona la teva base de dades SQLite",
            filetypes=[("Bases de dades SQLite", "*.db *.sqlite *.sqlite3"), ("Tots els arxius", "*.*")]
        )
        if not ruta:
            return

        try:
            if self.conexion:
                self.conexion.close()
            self.conexion = sqlite3.connect(ruta)
            cursor = self.conexion.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = [fila[0] for fila in cursor.fetchall()]

            self.combo_tablas["values"] = tablas
            if tablas:
                self.combo_tablas.current(0)
                self.cargar_datos()
            else:
                messagebox.showinfo("Buit", "Aquesta base de dades encara no té cap taula.")
        except Exception as e:
            messagebox.showerror("Error", f"No s'ha pogut obrir l'arxiu:\n{e}")

    def cargar_datos(self, event=None):
        tabla = self.combo_tablas.get()
        if not tabla or not self.conexion:
            return

        # Netejar taula anterior
        self.tree.delete(*self.tree.get_children())

        cursor = self.conexion.cursor()
        cursor.execute(f"SELECT * FROM {tabla}")
        filas = cursor.fetchall()
        columnas = [descripcion[0] for descripcion in cursor.description]

        self.tree["columns"] = columnas
        self.tree["show"] = "headings"

        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor=tk.W)

        for fila in filas:
            self.tree.insert("", tk.END, values=fila)

if __name__ == "__main__":
    root = tk.Tk()
    app = VisorSQLite(root)
    root.mainloop()
