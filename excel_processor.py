import pandas as pd
import io

def combine_excel_sheets(files, file_type):
    all_data = []
    log = []

    for filename, file_content in files:
        try:
            log.append(f"Procesando archivo: {filename}")
            xls = pd.ExcelFile(io.BytesIO(file_content))

            for sheet_name in xls.sheet_names:
                if file_type == "Estudiantes Activos":
                    df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=6, usecols="B:H")
                    df = normalize_columns(df)
                else:  # Estudiantes Moodle
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    df = process_estudiantes_moodle(df)

                df = df.dropna(how="all")

                if not df.empty:
                    df["SheetName"] = sheet_name
                    df["FileName"] = filename
                    all_data.append(df)

            log.append(f"Archivo procesado con éxito: {filename}")
        except Exception as e:
            log.append(f"Error al procesar el archivo {filename}: {e}")

    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data = finalize_combined_data(combined_data, file_type)
        return combined_data, log
    else:
        log.append("No se encontraron datos para combinar.")
        return pd.DataFrame(), log

def normalize_columns(df):
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    column_mapping = {
        "APELLIDO 1": "apellido1",
        "APELLIDO 2": "apellido2",
        "NOMBRE 1": "nombre1",
        "NOMBRE 2": "nombre2",
        "# CELULAR": "TELEFONO",
        "CELULAR": "TELEFONO",
        "CORREO ELECTRONICO": "CORREO",
        "CORREO ELECTRÓNICO": "CORREO",
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df[new_col] = df.get(new_col, df[old_col])
            if old_col != new_col:
                df = df.drop(columns=[old_col])

    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(how="all")

    return df

def process_estudiantes_moodle(df):
    if 'firstname' in df.columns:
        df[['nombre1', 'nombre2']] = df['firstname'].str.extract(r'(\S+)\s*(.*)', expand=True)
    if 'lastname' in df.columns:
        df[['apellido1', 'apellido2']] = df['lastname'].str.extract(r'(\S+)\s*(.*)', expand=True)
    
    df = df.rename(columns={
        'idnumber': 'CEDULA',
        'profile_field_Proaca': 'estado_u',
        'email': 'CORREO'
    })

    return df[['CEDULA', 'apellido1', 'apellido2', 'nombre1', 'nombre2', 'CORREO', 'estado_u']]

def finalize_combined_data(combined_data, file_type):
    if 'CEDULA' in combined_data.columns:
        combined_data['CEDULA'] = pd.to_numeric(combined_data['CEDULA'], errors='coerce')
        combined_data.dropna(subset=['CEDULA'], inplace=True)
        combined_data['CEDULA'] = combined_data['CEDULA'].astype(int).astype(str)

    if 'TELEFONO' in combined_data.columns:
        combined_data['TELEFONO'] = pd.to_numeric(combined_data['TELEFONO'], errors='coerce')
        combined_data.dropna(subset=['TELEFONO'], inplace=True)
        combined_data['TELEFONO'] = combined_data['TELEFONO'].astype(int).astype(str)

    if file_type == "Estudiantes Activos":
        combined_data['jornada'] = combined_data['FileName'].apply(
            lambda x: 'FS' if 'FS' in x else ('DIU' if 'DIU' in x else ('NOC' if 'NOC' in x or 'ESPECIALIZA' in x else '')))
        combined_data['estado_u'] = combined_data['FileName'].apply(
            lambda x: 'Diplomado' if 'DIPLOMADO' in x else ('Tecnico' if 'TECNICO' in x else ('Profesional' if 'PROF' in x or 'DERECHO' in x else ('Especialización' if 'ESPECIALIZA' in x else ''))))

    column_order = [
        "CEDULA",
        "apellido1",
        "apellido2",
        "nombre1",
        "nombre2",
        "TELEFONO",
        "CORREO",
        "estado_u",
        "jornada",
        "SheetName",
        "FileName",
    ]
    
    result = combined_data[[col for col in column_order if col in combined_data.columns]]
    
    result.columns = result.columns.str.lower()
     
    return result