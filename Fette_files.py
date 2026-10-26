#=============================================================================================
#=============================================================================================

#App per modificar els arxius excel de les Fettes afegin una columna de velocitat i calculant-la

#Versio: 1.11

#Data:17/10/26

#Aut: Ramon Servitje

#==============================================================================================
#==============================================================================================

#--------------------------------------------------------------------------------------------------

#Llibreries

#--------------------------------------------------------------------------------------------------
import os
import glob
import re #per buscar el nom del producte amb regex
import shutil #per copiar els arxius que han donat error a una carpeta csv_error
from pathlib import Path
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

#------------------------------------------------------------------------------------------------
# CONFIGURACIO: valors per defecte i noms de carpetes/fitxers
# Els directoris escollits per l'usuari a la finestra continuen sent variables.
#------------------------------------------------------------------------------------------------
DIRECTORI_ENTRADA_PER_DEFECTE = Path(r"C:\Proves Albert")
FILTRE_CSV_PER_DEFECTE = "_P1_.csv"
NOM_CARPETA_CSV_ERROR = "csv_error"
SUFIX_FITXER_SORTIDA = "_v"
NOM_FITXER_ICONA = "favicon.ico"

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
        if (
            p.is_file()
            and p.suffix.lower() == ".csv"
            and "_v.csv" not in p.name
            and not any(part.casefold() == "csv_error" for part in p.parts)
        ): #es tene que complir les tres codicins
            if filtre_net.lower() in p.name.lower(): #revisar aquesta condicio
                vector.append(str(p))
    return vector
 # el if es per torar a procesar els arxius que ja tenen _v.csv i no es volen tornar a processar
 
#-------------------------------------------------------------------------------------------

# FUNCIO 2: Helper comprova codificacio si es pot llegir el csv i busca caçaleres, NO guarda i NO borra
#es comproven nomes dos codificacions per si estan barrejades, utf-8 i latin1
#retorna la posicio de la capcalera, l'encoding i totes les linies anteriors
# a la taula per conservar-les tal com apareixen al CSV (incloses les linies buides)
#modificacio en la capçalera que es busca FEtte 2200 te hora te 'Tiempo' no 'Hora'

#------------------------------------------------------------------------------------------

def trobar_capcalera_i_encoding(ruta_csv):
     #Nomes provem dos codificacions per si estan barrejades
    for enc in ('utf-8', 'latin1'): #les posibles codificacions del csv
        #canvien de fer-ho en if a fer-nho en bcule, com hi ha mes comprovacions el if seia massa llarg dintre hi posem el Try per que si funciona   itf-8 
        # ja no s executa el latin1
        try:
            with open(ruta_csv, 'r', encoding=enc, newline='') as f:
                linies_superiors = []
                for i, line in enumerate(f):
                    l = line.lower() # passem tot a minúscules
                    if 'fecha' in l and ('hora' in l or 'tiempo' in l): #Busquem la capçalera que conté "Fecha" i "Hora" o "Tiempo"
                        return i, enc, linies_superiors
                    # Guardem el bloc original complet abans de les columnes,
                    # incloent-hi la fila buida que pot haver-hi al final.
                    linies_superiors.append(line)
        except UnicodeDecodeError:
            continue

    raise ValueError("No capçalera Fecha/Hora o Fecha/Tiempo")

#-----------------------------------------------------------------------------------------------

#FUNCIO 3 : Helper Obrir el csv de forma segura
#per defecte el separador es ; i el decimal es , i el encoding es el que s ha detectat
# amb la funcio trobar_capcalera_i_encoding

#----------------------------------------------------------------------------------------------

def llegir_csv_segur(ruta_csv, linia_cap, encoding_detectat, nrows=None):
    
    return pd.read_csv(ruta_csv, skiprows=linia_cap, sep=';', decimal=',',
                       encoding=encoding_detectat, engine='python', nrows=nrows)
    
#---------------------------------------------------------------------------------------------
  
  #FUNCIO 4: Helper Funcio per extreure el nom del producte del nom
  # del fitxer per crear/ en carpeta de nom de producte 
  
#----------------------------------------------------------------------------------------------
    
def extreure_producte(filename: str) -> str:
    # entre _ o espacio, 5 letras seguidas
    tokens = re.findall(r'(?:^|_|\s)([A-Za-z]{5,})(?=_|\s|$)', filename)
    if not tokens:
        return "DESCONOCIDO"
    # El més llarg i les primeres 7 lletres -> RUPATADINA i RUPATADINE = RUPATAD
    producto = max(tokens, key=len)
    return producto[:7].upper()
    
 #--------------------------------------------------------------------------------------------

# FUNCIO 5: Helper Funcio per modificar el nom de l arxius a _P1_v.si s ha afegit la velocitat
#i guardarlo en el directori de sortida escollit o en el mateix directori si no s ha escollit cap directori de sortida
#Fem servir directori d entrada perque si hi han subdirectoris es guardi en el mateix subdirectori i no es barregin els noms

#--------------------------------------------------------------------------------------------

def get_nom_sortida(ruta_csv, dir_sortida=None, directori_entrada=None):
    p = Path(ruta_csv)  # extreu nom del path

    if p.suffix.lower() != ".csv": #comprovem extesio csv
        return None
    nou_nom = p.stem + SUFIX_FITXER_SORTIDA + ".csv"  # posa el sufix al nom de sortida

    # Si s ha triat una carpeta de sortida, hi guardem el resultat con objecte path.
    if dir_sortida:
        carpeta_sortida = Path(dir_sortida) / extreure_producte(p.stem)
        # Conservem les subcarpetes d origen per evitar xocs de noms si hi han subcarpetes amb el mateix nom de fitxer. 
        if directori_entrada:
            ruta_relativa = p.relative_to(Path(directori_entrada)) # guradem la ruta relativa del directori d entrada per poder crear subcarpetes dins de la carpeta de sortida
            carpeta_sortida /= ruta_relativa.parent
        return carpeta_sortida / nou_nom
    else:
        # Si no hi ha carpeta de sortida, el desem al costat de l original.
        return p.with_name(nou_nom)
    
#----------------------------------------------------------------------------------------------

#FUNCIO 6: Helper Funcio per copiar un csv que ha donat error 
# a una carpeta csv_error dins del directori de sortida o dins del directori d entrada

#---------------------------------------------------------------------------------------------

def guardar_csv_error(ruta_csv, dir_sortida=None, directori_entrada=None):
    
    ruta_origen = Path(ruta_csv)
    directori_base = dir_sortida or directori_entrada or ruta_origen.parent
    carpeta_error = Path(directori_base) / NOM_CARPETA_CSV_ERROR # afegim la carpeta per als CSV amb error
    carpeta_error.mkdir(parents=True, exist_ok=True) # Crear carpeta per a fitxers d'error

    ruta_error = carpeta_error / f"{ruta_origen.stem}_error{ruta_origen.suffix}" # constr
    numero = 2 # renombrar si ja existeix un arxiu amb el mateix nom
    while ruta_error.exists(): #revisar bucle crec innecesari
        ruta_error = carpeta_error / (
            f"{ruta_origen.stem}_error_{numero}{ruta_origen.suffix}"
        )
        numero += 1

    shutil.copy2(ruta_origen, ruta_error)
    return ruta_error
    
#---------------------------------------------------------------------------------------------

#FUNCIO 6: Processa un CSV i retorna el dataframe amb les velocitats calculades.
#La capcalera i el guardat es fan despres, en una funcio independent.

#---------------------------------------------------------------------------------------------

def crear_dataframe_velocitat(ruta_csv, linia_cap, encoding_detectat):
    
    # Llegim les dades a partir de la fila de noms de columna detectada per la funcio 2.
    df = llegir_csv_segur(ruta_csv, linia_cap, encoding_detectat)
    
    #---Amb pandas readcsv llegim i tractem el csv si l hem pogut obrir i trobar capçaler
    
    df.columns = [c.strip() for c in df.columns]  #amb strip() eliminem espais en blanc a les capçaleres en bucle desde c=1 fins a len(df.columns)

    # Cal apartar la fila ID=E abans de validar les dates, per evitar que
    # desaparegui quan no tingui una data utilitzable com les files de produccio.
    col_id = next((c for c in df.columns if str(c).strip().casefold() == 'id'), None)
    fila_especial = None
    
    # Si hi ha una fila amb ID=E,  esla fila especial, la separem del dataframe
    # principal i la guardem a part, que representa ques e la fila dels promitjos 
    
    if col_id is not None:
        es_fila_e = df[col_id].astype('string').str.strip().str.casefold().eq('e') # treballem en minuscules per evitar errors
        if es_fila_e.sum() > 1:
            raise ValueError("S'ha trobat mes d'una fila amb E a la columna ID.") # En teoria n hi ha nomes una
        if es_fila_e.any():
    # SI s ha trobat la fila especial, la separem del dataframe principal i la guardem a part
            fila_especial = df.loc[es_fila_e].iloc[0].copy()
            df = df.loc[~es_fila_e].copy()
    # Aqui comencem  amirar el tema del borrat de les columnes buides        
    # Fem servir noms de columna per  en minúscules per evitar errors de majúscules/minúscules.
    noms_cols = [str(c).casefold() for c in df.columns]
    #Busquem la columna de pes per eliminar les columnes buides a partir d ella, 
    # si no hi es no eliminem res
    idx_peso = next(
        (i for i, nom in enumerate(noms_cols) if nom == 'peso'),
        None,
    ) 
    #Pels limits individuals, busquem la ultima columna que comenci amb 'limite individual' 
    idx_limits_individuals = [
        i for i, nom in enumerate(noms_cols)
        if nom == 'limite individual' or nom.startswith('limite individual.')
    ]
    # Si hi ha alguna columna de límits individuals, agafem l'índex de la última; si no, None.  
    idx_ultim_limite = (
        idx_limits_individuals[-1] if idx_limits_individuals else None
    )
    # Agafem les columnes necesaries per el calcul de velocitats
    col_fecha = [c for c in df.columns if 'Fecha' in c][0]
    col_hora = [c for c in df.columns if 'Hora' in c or 'Tiempo' in c][0]
    col_prod = [c for c in df.columns if 'Prod' in c][0]
    
        #Psem la columna de dates de string a datetime per poder calcular

# data a datetime barrejant el format de la data i hora per defecte es %d.%m.%Y %H:%M:%S
    fecha_hora = df[col_fecha].astype(str) + ' ' + df[col_hora].astype(str)
    df['datetime'] = pd.to_datetime(
        fecha_hora,
        format='%d.%m.%Y %H:%M:%S',
        errors='coerce',
        dayfirst=True,
    )
    # Si hi ha dates que no s'han pogut convertir amb el format específicat, provem amb el format europeu per defecte.
    fechas_no_convertides = df['datetime'].isna()
    if fechas_no_convertides.any():
        df.loc[fechas_no_convertides, 'datetime'] = pd.to_datetime(
            fecha_hora.loc[fechas_no_convertides],
            dayfirst=True,
            errors='coerce',
        )
    # Eliminem les files amb dates no vàlides i ordenem el dataframe per data i hora.
    df = df.dropna(subset=['datetime']).sort_values('datetime').reset_index(drop=True)
   #Comprobem les columnes desde pes finsla de limit per saber di estan buides
   #Comprobem columna a columna, si la columna esta completamen buida omplim el vector columnes a eliminar
    if idx_peso is not None:
        columnes_a_eliminar = []
        for columna in df.columns[idx_peso:]:
            text = df[columna].astype('string').str.strip()
            es_buit = text.isna() | text.eq('') # condicio llarga de string
            valors_numerics = pd.to_numeric( 
                text.str.replace(',', '.', regex=False),
                errors='coerce',
            )
            es_zero = valors_numerics.eq(0).fillna(False)# condicio  llarga numerica de 0
            if (es_buit | es_zero).all(): # condicio de columna buida (numerica i de string simplificades en les linees anteriors)
                columnes_a_eliminar.append(columna) #despres de la comprobacio si cumpleix afegim al vectro
        df = df.drop(columns=columnes_a_eliminar) #ELiminem les columnes NOMES buidwa

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

    #  l Albert demana aixo: la primera fila no te diferencia anterior, per tant rep les velocitats
    # calculades a la segona fila i no queda amb els camps buits.
    if len(df) > 1:
        df.loc[df.index[0], 'velocidad'] = df.loc[df.index[1], 'velocidad']
        df.loc[df.index[0], 'velocidad_pzas_h'] = df.loc[df.index[1], 'velocidad_pzas_h']

    # Arrodonim les dues columnes de velocitat a dues xifres decimals.
    df[['velocidad', 'velocidad_pzas_h']] = df[['velocidad', 'velocidad_pzas_h']].round(2)

    # Eliminem les columnes temporals abans d'afegir la fila especial E, que no les utilitza.
    df = df.drop(columns=['datetime', 'diff_prod', 'diff_seg'])

    # Calculem les velocitats de la fila E a partir de la seva Produccion
    # dividida pel seu temps; la segona velocitat expressa el resultat per hora.
    if fila_especial is not None:
        fila_especial = fila_especial.reindex(df.columns)
        produccio_e = pd.to_numeric(
            str(fila_especial[col_prod]).strip().replace(',', '.'),
            errors='coerce',)*1000 # passem  la produccio a numeric
        #El temps pel calcul de velocitats calpasar-lo a numeric
        temps_e_text = str(fila_especial[col_hora]).strip()
        temps_e = pd.to_numeric(temps_e_text.replace(',', '.'), errors='coerce')
        if pd.isna(temps_e):
            temps_e = pd.to_timedelta(temps_e_text, errors='coerce')
            temps_e = temps_e.total_seconds() if not pd.isna(temps_e) else np.nan
        if pd.isna(produccio_e) or pd.isna(temps_e) or temps_e == 0:
            raise ValueError(
                "No es poden calcular les velocitats de la fila ID=E: "
                "Produccion o Tiempo/Hora no es valid."
            )

        fila_especial['velocidad'] = round(produccio_e / temps_e, 2)
        fila_especial['velocidad_pzas_h'] = round(abs(produccio_e) * 3600 / temps_e, 2)
    # ATENCIOOO: retornem la fila E separada perquè només es gestioni una vegada en desar.
    return df, fila_especial

#------------------------------------------------------------------------------------------------

#FUNCIO 7: Construucio del nou csv : Afegeix el bloc original de capcalera al dataframe 
#Les linies es copien del fitxer d'origen; aixi tambe es conserva la fila buida.

#------------------------------------------------------------------------------------------------

def afegir_encapcalament_i_guardar(
    df, linies_encapcalament, ruta_csv, encoding_detectat,
    dir_sortida=None, directori_entrada=None, fila_especial=None,
):
    # Calculem el nom i la ubicacio del fitxer de sortida.
    ruta_nova = get_nom_sortida(
        ruta_csv,
        dir_sortida=dir_sortida,
        directori_entrada=directori_entrada,
    )
    if ruta_nova is None:
        raise ValueError("La ruta d'entrada ha de ser un fitxer CSV.")

    # Creem les carpetes de sortida que encara no existeixin.
    ruta_nova.parent.mkdir(parents=True, exist_ok=True)

    # NOU: desem la fila E separada, sense tornar-la a cercar dins del dataframe.
    with open(ruta_nova, 'w', encoding=encoding_detectat, newline='') as fitxer_sortida:
        fitxer_sortida.writelines(linies_encapcalament)
        df.to_csv(fitxer_sortida, index=False, sep=';', decimal=',')
        if fila_especial is not None:
            fitxer_sortida.write('\n')
            fila_especial.to_frame().T.to_csv(
                fitxer_sortida,
                index=False,
                header=True,
                sep=';',
                decimal=',',
            )
    return ruta_nova
       
#-----------------------------------------------------------------------------------------------------------------

#FUNCIO 8: Gestio de les finestres i control del flux del programa

#-----------------------------------------------------------------------------------------------------

def main_gui():
    root = tk.Tk() #--crea i disenya finestra inicial------------
    root.title("Càlcul de velocitats Fette")#--Titol de la finestra
    root.geometry("380x280") #-Tamany de la finestra
    root.resizable(False, False) #-modificacio de tamany de la finestra desactivada
    ruta_icono = Path(__file__).resolve().parent / NOM_FITXER_ICONA # ruta relativa de la icona de la finestra
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
    entry_ext.insert(0, FILTRE_CSV_PER_DEFECTE)
    entry_ext.pack(side="left")
    #Directori der defecte d entrada
    entry_path.insert(0, str(DIRECTORI_ENTRADA_PER_DEFECTE))
    
    #----S executa al apretar el boto verd d execucio; es el fluxe d execucio del programa
    def accio_ok():
        directori = entry_path.get().strip() #agafem el directori d entrada del input box
        filtre = entry_ext.get().strip() or FILTRE_CSV_PER_DEFECTE # agafem el filtre indicat o el valor per defecte
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
            #   cridem les funcions de lectura, calcul i guardat per separat
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
                    linia_cap, encoding, linies_encapcalament = (
                        trobar_capcalera_i_encoding(ruta)
                    )
                    df, fila_especial = crear_dataframe_velocitat(
                        ruta,
                        linia_cap,
                        encoding,
                    )
                    afegir_encapcalament_i_guardar(
                        df,
                        linies_encapcalament,
                        ruta,
                        encoding,
                        dir_sortida=dir_sortida,
                        directori_entrada=directori,
                        fila_especial=fila_especial,
                    )
                    ok_count += 1
                except Exception as exc:
                    detall_error = (
                        f"{Path(ruta).name}: {type(exc).__name__}: {exc}"
                    )
                    try:
                        ruta_error = guardar_csv_error(
                            ruta,
                            dir_sortida=dir_sortida,
                            directori_entrada=directori,
                        )
                        detall_error += f" (CSV copiat a {ruta_error})"
                    except Exception as error_copia:
                        detall_error += (
                            f" (no s'ha pogut copiar a csv_error: "
                            f"{type(error_copia).__name__}: {error_copia})"
                        )
                    arxius_error.append(detall_error)

            detall_errors = arxius_error[:20]
            if len(arxius_error) > 20:
                detall_errors.append(f"... i {len(arxius_error) - 20} errors més")

            messagebox.showinfo(
                "Fet!!!!!!",
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
