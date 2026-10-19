#=============================================================================================
#=============================================================================================

#App per modificar els arxius excel de les Fettes afegin una columna de velocitat i calculant-la

#Versio: 1.8

#Data:17/10/26

#Aut: Ramon Servitje

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

#------------------------------------------------------------------------------------------------

#FUNCIO 1: Crea el vector de arxius csv que compleixen amb la consicio del filte
#la busqueda es fa dins del directori i subdirctoris amb el comodin **

#------------------------------------------------------------------------------------------------
def crear_vector_arxius(directori, filtre):
    directori = Path(directori)                  # creem directori com a objecte path
    filtre_net = filtre.replace("*", "") #per seguretat netegem el filtre de * si hi ha
    patro = os.path.join(directori, "**", f"*{filtre_net}*") # afegim el comodi ** per buscar dins de subdirectoris
    arxius = glob.glob(patro, recursive=True)  # arxius que contenen el filtre i que son csv dins del directori i subdirectoris
    vector = []                                 # array on carregarem tots els paths del csv que cumplexin
    for f in arxius:                            #carrega a traves de bucle dels pats
        p = Path(f)
        if p.is_file() and p.suffix.lower() == ".csv" and "_v.csv" not in p.name: #es tene que complir les tres codicins
            if filtre_net.lower() in p.name.lower(): #revisar aquesta condicio
                vector.append(str(p))
    return vector
 # el if es per torar a procesar els arxius que ja tenen _v.csv i no es volen tornar a processar
 
#-------------------------------------------------------------------------------------------

# FUNCIO 2: Helper comprova codificacio si es pot llegir el csv i busca caçaleres, NO guarda i NO borra
#es comproven nomes dos codificacions per si estan barrejades, utf-8 i latin1
#si saps que benen barrejades es pot afegir una tercera codificacio. Retorna una tupla 

#------------------------------------------------------------------------------------------

def trobar_capcalera_i_encoding(ruta_csv):
    #Nomes provem dos codificacions per si estan barrejades
    try:
        with open(ruta_csv, 'r', encoding='utf-8') as f: #prova pimer amb utf-8
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

#FUNCIO 3 : Helper Obrir el csv de forma segura
#per defecte el separador es ; i el decimal es , i el encoding es el que s ha detectat
# amb la funcio trobar_capcalera_i_encoding

#----------------------------------------------------------------------------------------------

def llegir_csv_segur(ruta_csv, linia_cap, encoding_detectat, nrows=None):
    
    return pd.read_csv(ruta_csv, skiprows=linia_cap, sep=';', decimal=',',
                       encoding=encoding_detectat, engine='python', nrows=nrows)
     
 #--------------------------------------------------------------------------------------------

#FUNCIO 4: Helper Funcio per modificar el nom de l arxius a _P1_v.si s ha afegit la velocitat
#i guardarlo en el directori de sortida escollit o en el mateix directori si no s ha escollit cap directori de sortida
#Fem servir directori d entrada perque si hi han subdirectoris es guardi en el mateix subdirectori i no es barregin els noms

#--------------------------------------------------------------------------------------------

def get_nom_sortida(ruta_csv, dir_sortida=None, directori_entrada=None):
    p = Path(ruta_csv)  # extreu nom del path

    if p.suffix.lower() != ".csv": #comprovem extesio csv
        return None
    nou_nom = p.stem + "_v.csv"  # posa "_v.csv"

    # Si s ha triat una carpeta de sortida, hi guardem el resultat.
    if dir_sortida:
        carpeta_sortida = Path(dir_sortida)
        # Conservem les subcarpetes d origen per evitar xocs de noms si hi han subcarpetes amb el mateix nom de fitxer. 
        if directori_entrada:
            ruta_relativa = p.relative_to(Path(directori_entrada))
            carpeta_sortida /= ruta_relativa.parent
        return carpeta_sortida / nou_nom
    else:
        # Si no hi ha carpeta de sortida, el desem al costat de l original.
        return p.with_name(nou_nom)
    
#---------------------------------------------------------------------------------------------

#FUNCIO 4: Funcio per modificar UN UNIC csv afegint columna i calculant velocitat i GUARDAR
#Amb ruta_csv inclou les subcarpetes del diroctori d entrada  

#---------------------------------------------------------------------------------------------

def crear_velocitat_i_guardar(ruta_csv, dir_sortida=None, filtre=None, directori_entrada=None):
    
    linia_cap, enc = trobar_capcalera_i_encoding(ruta_csv) # toebme la linia de capcalera i el encoding del csv
    df = llegir_csv_segur(ruta_csv, linia_cap, enc) #obrm csv il asisgnem a objecte panada  datframe)
    
    #---Amb pandas readcsv llegim i tractem el csv si l hem pogut obrir i trobar capçaler
    
    df.columns = [c.strip() for c in df.columns]
  
    col_fecha = [c for c in df.columns if 'Fecha' in c][0]
    col_hora = [c for c in df.columns if 'Hora' in c][0]
    col_prod = [c for c in df.columns if 'Prod' in c][0]
    
        #Psem la columna de dates de string a datetime per poder calcular

# data a datetime
    fecha_hora = df[col_fecha].astype(str) + ' ' + df[col_hora].astype(str)
    df['datetime'] = pd.to_datetime(
        fecha_hora,
        format='%d.%m.%Y %H:%M:%S',
        errors='coerce',
        dayfirst=True,
    )

    fechas_no_convertidas = df['datetime'].isna()
    if fechas_no_convertidas.any():
        df.loc[fechas_no_convertidas, 'datetime'] = pd.to_datetime(
            fecha_hora.loc[fechas_no_convertidas],
            dayfirst=True,
            errors='coerce',
        )

    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

    # produccio a numeric - amb coma europaea tambe
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
    ruta_nova = get_nom_sortida(ruta_csv, dir_sortida=dir_sortida, directori_entrada=directori_entrada)
    
    if ruta_nova is None:
        raise ValueError("La ruta d'entrada ha de ser un fitxer CSV.")
    
    #creem el directori de sortida (mkdir) si no existeix amb parents=True crea tots els subdirectoris que falten
    ruta_nova.parent.mkdir(parents=True, exist_ok=True) 
    #guardem l arxiu amb el nom creat com a csv amb separador ; i decimal , i sense index
    df.to_csv(ruta_nova, index=False, sep=';', decimal=',', encoding='utf-8')
    return ruta_nova
       
#-----------------------------------------------------------------------------------------------------------------

#FUNCIO 6 Gestio de les finestres i control de fluxe del programa

#-----------------------------------------------------------------------------------------------------


def main_gui():
    root = tk.Tk() #--crea i disenya finestra inicial------------
    root.title("Càlcul de velocitats Fette")#--Titol de la finestra
    root.geometry("380x280") #-Tamany de la finestra
    root.resizable(False, False) #-modificacio de tamany de la finestra desactivada
    ruta_icono = Path(__file__).resolve().parent / "favicon.ico" # ruta reliativa del icono de la finestra
    if ruta_icono.exists():
        root.iconbitmap(str(ruta_icono))# -favicon de la finestra
    
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
    #Directori de sortida per defecte esta fet pe programacio.
    # si es volgues posar un altre per defecte seria:
    #entry_sortida.insert(0, r"C:\Dir per defecte diferent al d entrada")
    
    # Input box per seleccionar el filtr del csv, per defecte 
    tk.Label(root, text="Filtre dels csv:").pack(anchor="w", padx=10, pady=(15,2))
    frame_ext = tk.Frame(root)
    frame_ext.pack(fill="x", padx=12)
    entry_ext = tk.Entry(frame_ext, width=35)
    entry_ext.insert(0, "_P1_.csv")
    entry_ext.pack(side="left")
    #Directori der defecte d entrada
    entry_path.insert(0, r"C:\Proves Albert")
    
    #----S executa al apretar el boto verd d execucio; es el fluxe d execucio del programa
    def accio_ok():
        directori = entry_path.get().strip() #agafem el directori d entrada del input box
        filtre = entry_ext.get().strip() or "_P1_.csv" #agafem el filtre del input box si no hi ha res agafem el de defecte
        dir_sortida = entry_sortida.get().strip() or None  #si es None per programacio agafa el d entrad
        if not directori or not Path(directori).exists(): #aquet es el d entrda que te que estar selcecionat si o si
            messagebox.showerror("Error", "Has de seleccionar un directori vàlid", parent=root)
            return
        root.withdraw() # Amaguem la finestra principal mentre es processa
        finestra_tancada = False
        try:
            vector = crear_vector_arxius(directori, filtre) #creem el vector amb els arxius que compleixen amb el filtre

            if not vector:
                messagebox.showwarning(
                    "Cap arxiu",
                    f"No s'ha trobat cap arxiu amb el filtre '{filtre}' a:\n{directori}",
                    parent=root,
                )
                return

            messagebox.showinfo(
                "Arxius trobats",
                f"S'han trobat {len(vector)} arxius amb l'extensió '{filtre}'.\n\n"
                "Clica OK per continuar amb el càlcul de velocitat.",
                parent=root,
            )

            arxius_error = []
            ok_count = 0
            omesos_count = 0
            # Amb el bucle for recorrem el vector amb els arxius que compleixen amb el filtre i 
            #   cridem la funcio crear_velocitat_i_guardar
            for ruta in vector:
                desti = get_nom_sortida(
                    ruta,
                    dir_sortida,
                    directori_entrada=directori,
                )
                if desti and desti.exists():
                    omesos_count += 1
                    continue
                try:
                    crear_velocitat_i_guardar(
                        ruta,
                        dir_sortida,
                        directori_entrada=directori,
                    )
                    ok_count += 1
                except Exception as exc:
                    arxius_error.append( # anem omplint el vector amb els errors que es produeixen en el procesament dels arxius
                        f"{Path(ruta).name}: {type(exc).__name__}: {exc}"
                    )

            detall_errors = arxius_error[:20]
            if len(arxius_error) > 20:
                detall_errors.append(f"... i {len(arxius_error) - 20} errors més")

            messagebox.showinfo(
                "Fet - Mode lent",
                f"CSV trobats: {len(vector)}\n"
                f"Processats correctament: {ok_count}\n"
                f"Omesos (ja tenien resultat): {omesos_count}\n"
                f"Errors: {len(arxius_error)}\n\n"
                + ("\n".join(detall_errors) if detall_errors else "Cap"),
                parent=root,
            )
            root.destroy()
            finestra_tancada = True
        except OSError as exc:
            root.deiconify()
            messagebox.showerror(
                "Error d'accés als fitxers",
                f"{type(exc).__name__}: {exc}",
                parent=root,
            )
        finally:
            if not finestra_tancada:
                root.deiconify()

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
