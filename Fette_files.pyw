#=============================================================================================
#=============================================================================================

#App per modificar els arxius excel de les Fettes afegin una columna de velocitat i calculant-la

#Versio: 1.4

#Data:17/10/26

#==============================================================================================
#==============================================================================================

#--------------------------------------------------------------------------------------------------

#Llibreries

#--------------------------------------------------------------------------------------------------
import os
import glob
from pathlib import Path
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from functools import partial

#------------------------------------------------------------------------------------------------

#FUNCIO 1: Crea el vector de arxius csv que compleixen amb la consicio del filte

#------------------------------------------------------------------------------------------------
def crear_vector_arxius(directori, filtre):
    directori = Path(directori)                  # creem directori com a objecte path
    filtre = filtre.strip() or "_P1_.csv"        #Condicio de filtre i el seu decte
    filtre_net = filtre.replace("*", "")
    patro = os.path.join(directori, "**", f"*{filtre_net}*")
    arxius = glob.glob(patro, recursive=True)
    vector = []                                 # array on carregarem tots els paths del csv que cumplexin
    for f in arxius:                            #carrega a traves de bucle dels pats
        p = Path(f)
        if p.is_file() and p.suffix.lower() == ".csv" and "_V.csv" not in p.name: #es tene que complir les tres codicins
            if filtre_net.lower() in p.name.lower(): #revisar aquesta condicio
                vector.append(str(p))
    return vector

#--------------------------------------------------------------------------------------------

#FUNCIO 2: Helper Funcio per modificar el nom de l arxius a _P1_v.si s ha afegit la velocitat
#i guardarlo en el directori de sortida escollit o en el mateix directori si no s ha escollit cap directori de sortida

#--------------------------------------------------------------------------------------------

def get_nom_sortida(ruta_csv, dir_sortida=None):
    p = Path(ruta_csv)
    if "_P1_.csv" in p.name:
        nou_nom = p.name.replace("_P1_.csv", "_P1_V.csv")
    else:
        nou_nom = p.stem + "_V.csv"
    
    if dir_sortida:  #Si s ha escollit un directori de sortida, el guardem allà
        return Path(dir_sortida) / nou_nom
    else: #si no s ha escollit cap directori de sortid
            #el guardem en el mateix directori que l arxiu original
        return p.with_name(nou_nom)
#---------------------------------------------------------------------------------------------

#FUNCIO 3: Funcio per modificar UN UNIC csv afegint columna i calculant velocitat i GUARDAR 

#---------------------------------------------------------------------------------------------

def crear_velocitat_i_guardar(ruta_csv,dir_sortida=None):
    
    linia_cap, enc = trobar_capcalera_i_encoding(ruta_csv)
    df = llegir_csv_segur(ruta_csv, linia_cap, enc)
    
    #---Amb pandas readcsv llegim i tractem el csv si l hem pogut obrir i trobar capçaler
    
    try: #Llgeir l arxiu el separador son ; si canvia a , caldria canviar-o
        df = pd.read_csv(ruta_csv, skiprows=linia_cap, sep=';', decimal=',', encoding='utf-8', engine='python')
    except:
        df = pd.read_csv(ruta_csv, skiprows=linia_cap, sep=';', decimal=',', encoding='latin1', engine='python')

    df.columns = [c.strip() for c in df.columns]
    col_fecha = [c for c in df.columns if 'Fecha' in c][0]
    col_hora = [c for c in df.columns if 'Hora' in c][0]
    col_prod = [c for c in df.columns if 'Prod' in c][0]
    
        #Psem la columna de dates de string a datetime per poder calcular

# data a datetime
    df['datetime'] = pd.to_datetime(df[col_fecha].astype(str) + ' ' + df[col_hora].astype(str),
                                format='%d.%m.%Y %H:%M:%S', errors='coerce', dayfirst=True)

    if df['datetime'].isna().all():
        df['datetime'] = pd.to_datetime(df[col_fecha].astype(str) + ' ' + df[col_hora].astype(str),
                                    dayfirst=True, errors='coerce')

    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

    # producció a numèric - amb coma europaea tambe
    df[col_prod] = pd.to_numeric(df[col_prod].astype(str).str.replace(',', '.'), errors='coerce')

    # --- Fem les diferencies amb la cel.la anterior ---
    df['diff_prod'] = df[col_prod].diff()*1000
    df['diff_seg'] = df['datetime'].diff().dt.total_seconds()
    #-----creem les columnes de velocitat i velocitat_pzas_h amb valors nans
    df['velocidad'] = np.nan
    df['velocidad_pzas_h'] = np.nan
    #-Concio d us de les diferencies per calcular la velocitat i velocitat_pzas_h
    mask = (df['diff_seg'] != 0) & df['diff_seg'].notna() & df['diff_prod'].notna()
    #---Calculem la velocitat i velocitat_pzas_h amb les condicions de la mascara
    df.loc[mask, 'velocidad'] = df.loc[mask, 'diff_prod'] / df.loc[mask, 'diff_seg']
    df.loc[mask, 'velocidad_pzas_h'] = (df.loc[mask, 'diff_prod'].abs()) / (df.loc[mask, 'diff_seg'] / 3600)

    # opcional, esborra les columnes auxiliars
    #df = df.drop(columns=['diff_prod', 'diff_seg'])            
    #si no hi han errors guardem l arxiu amb nova extensio i en e
    # el directori de sortida escollit o en el mateix directori si no s ha escollit cap directori de sortida
    ruta_nova = get_nom_sortida(ruta_csv, dir_sortida=dir_sortida)
    #guardem l arxiu amb el nom creat
    df.to_csv(ruta_nova, index=False, sep=';', decimal=',', encoding='utf-8')
    return ruta_nova

#-------------------------------------------------------------------------------------------

# FUNCIO 4: Helper comprova codificacio si es pot llegir, NO guarda i NO borra

#------------------------------------------------------------------------------------------
def trobar_capcalera_i_encoding(ruta_csv):
    #Nomes provem dos codificacions per si estan barrejades
    try:
        with open(ruta_csv, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if 'Fecha' in line and 'Hora' in line: # busca la linea on apareix  Hora i Fecha
                    return i, 'utf-8' #la sortida es una tupla amb el n de lineade la Fecha i el codi del csv
    except UnicodeDecodeError:
        pass

    # si no era utf-8, és latin1
    with open(ruta_csv, 'r', encoding='latin1', errors='ignore') as f:
        for i, line in enumerate(f):
            if 'Fecha' in line and 'Hora' in line:  #busca la linea on apareix  Hora i Fecha
                return i, 'latin1' #la sortida es una tupla amb el n de lineade la Fecha i el codi del csv

    raise ValueError("No capçalera Fecha/Hora")

#-----------------------------------------------------------------------------------------------

#FUNCIO 5 : Helper Obrir el csv de forma segura

#----------------------------------------------------------------------------------------------

def llegir_csv_segur(ruta_csv, linia_cap, encoding_detectat, nrows=None):
    """Ja no prova codificacions, usa la que li passes."""
    return pd.read_csv(ruta_csv, skiprows=linia_cap, sep=';', decimal=',',
                       encoding=encoding_detectat, engine='python', nrows=nrows)

        
#-----------------------------------------------------------------------------------------------------------------

#FUNCIO 6 Gestio de les finestres i control de fluxe del programa

#-----------------------------------------------------------------------------------------------------


def main_gui():
    root = tk.Tk() #--crea i disenya finestra inicial------------
    root.title("Càlcul de velocitats Fette")
    root.geometry("380x280")
    root.resizable(False, False)
    
    # Input box per seleccionar direcctori de entrada, 
    tk.Label(root, text="Directori on hi ha els arxius:").pack(anchor="w", padx=10, pady=(15,2))
    frame_path = tk.Frame(root)
    frame_path.pack(fill="x", padx=10)
    entry_path = tk.Entry(frame_path, width=30)
    entry_path.pack(side="left", fill="x", expand=True)
    def triar_directori_entrada():
        dir_sel_entr = filedialog.askdirectory(title="Selecciona directori d´entrada on hi ha els CSV")
        if dir_sel_entr:
            entry_path.delete(0, tk.END)
            entry_path.insert(0, dir_sel_entr)
    tk.Button(frame_path, text="Seleccionar", command=triar_directori_entrada).pack(side="left", padx=5)
    
    # Input box per seleccionar direcctori de sortida, si es deixa buit es guardara en el mateix directori
    tk.Label(root, text="Directori de sortida (buit = mateixa carpeta):").pack(anchor="w", padx=10, pady=(10,2))
    frame_sortida = tk.Frame(root)
    frame_sortida.pack(fill="x", padx=10)
    entry_sortida = tk.Entry(frame_sortida, width=35)
    entry_sortida.pack(side="left", fill="x", expand=True)
    def triar_directori_sortida():
        dir_sel = filedialog.askdirectory(title="Selecciona directori de SORTIDA")
        if dir_sel:
            entry_sortida.delete(0, tk.END)
            entry_sortida.insert(0, dir_sel)
    tk.Button(frame_sortida, text="Seleccionar", command=triar_directori_sortida).pack(side="left", padx=5)
    
    # Input box per seleccionar el filtr del csv, per defecte 
    tk.Label(root, text="Filtre dels csv:").pack(anchor="w", padx=10, pady=(15,2))
    frame_ext = tk.Frame(root)
    frame_ext.pack(fill="x", padx=10)
    entry_ext = tk.Entry(frame_ext, width=35)
    entry_ext.insert(0, "_P1_.csv")
    entry_ext.pack(side="left", fill="x", expand=True)
    
    entry_path.insert(0, r"C:\Proves Albert")
    
    #----S executa al apretar el boto verd d execucio
    def accio_ok():
        directori = entry_path.get().strip()
        filtre = entry_ext.get().strip() or "_P1_.csv"
        dir_sortida = entry_sortida.get().strip() or None  # NOU - llegir so
        if not directori or not Path(directori).exists():
            messagebox.showerror("Error", "Has de seleccionar un directori vàlid", parent=root)
            return
        root.withdraw() # Amaguem la finestra principal mentre es processa
        
        vector = crear_vector_arxius(directori, filtre) # Eexecutem la funcio 1 vector arxius

        if not vector:   # Si no trova arxius amb l extensio
            messagebox.showwarning("Cap arxiu", f"No s'ha trobat cap arxiu amb extesio '{filtre}' a:\n{directori}")
            root.deiconify() # Fem apareixer la finestra principal de nou
            return

        messagebox.showinfo("Arxius trobats", f"S'han trobat {len(vector)} arxius amb l'extensió '{filtre}'.\n\nClica OK per continuar amb el càlcul de velocitat.")

        func_amb_sortida = partial(crear_velocitat_i_guardar, dir_sortida=dir_sortida)  # Funció amb el directori de sortida fixat
        
        # Intent ràpid amb MAP
        try:
            nous = list(map(func_amb_sortida, vector))  
            messagebox.showinfo("Fet - MAP ràpid", f"S'han tractat {len(nous)} arxius amb MAP.\nGuardats com *_P1_V.csv")
            root.destroy()
            return
        except Exception:
            # Si map falla mirem quins fallen SENSE borrar els ja creats
            arxius_error = []
            for ruta in vector:
                # Si ja té _V.csv creat pel MAP abans de fallar, no el comptem com error
                if get_nom_sortida(ruta).exists():
                    continue
                try:
                    linia_cap, enc = trobar_capcalera_i_encoding(ruta)
                    llegir_csv_segur(ruta, linia_cap, enc, nrows=5)
                except:
                    arxius_error.append(Path(ruta).name)

            llistat = "\n".join(arxius_error[:20])
            if len(arxius_error) > 20:
                llistat += f"\n... i {len(arxius_error)-20} més"

            ja_fets = sum(1 for r in vector if get_nom_sortida(r).exists())

            missatge = (
                f"El mode ràpid MAP ha fallat.\n"
                f"S'han processat {ja_fets} arxius, que es conserven.\n\n"
                f"S ha trobat el següent arxiu amb error: ({len(arxius_error)}):\n{llistat}\n\n"
                f"S'executarà mode lent per la resta."
            )

            if not messagebox.askokcancel("Error mode ràpid", missatge):
                root.deiconify()
                return

            # Mode lent: només processem els que NO tenen _V.csv
            ok_count = ja_fets
            errors_finals = []
            for ruta in vector:
                if get_nom_sortida(ruta).exists():
                    continue # ja processat, el deixem
                try:
                    crear_velocitat_i_guardar(ruta)
                    ok_count += 1
                except Exception:
                    errors_finals.append(Path(ruta).name)

            messagebox.showinfo("Fet - Mode lent", 
                f"S'han tractat {ok_count} de {len(vector)} arxius. \n\nErrors finals ({len(errors_finals)}):\n" + "\n".join(errors_finals[:20])
            )
            root.destroy()

    def accio_sortir():
        root.destroy()

    frame_botons = tk.Frame(root)
    frame_botons.pack(pady=20)
    #Al apretar aque boto executem accio_ok
    tk.Button(frame_botons, text="Processar", command=accio_ok, width=18, height=2, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
    tk.Button(frame_botons, text="Sortir", command=accio_sortir, width=12, height=2, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

    root.mainloop()

#Execucio d inici del programa si es executa directament l aprimera funcio que s executa es
# la funcio main_gui()

if __name__ == "__main__":
    main_gui()
