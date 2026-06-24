import pandas as pd
from io import BytesIO
from typing import List
from app.models.document import DocumentoProcesado
from app.utils.logger import logger

def generar_excel_consolidado(lista_documentos: List[DocumentoProcesado]) -> BytesIO:
    logger.info('Generando Excel consolidado para %d documentos', len(lista_documentos))
    datos_para_excel = []
    for doc in lista_documentos:
        fila = {'Título': doc.titulo_excel, 'Nombre de norma (opcional)': doc.nombre_norma_excel, 'Descripción': doc.descripcion_excel, 'Fecha de publicación (dd/mm/yyyy)': doc.fecha_archivo.strftime('%d/%m/%Y'), 'Archivo': doc.url_archivo or '', 'publication_type_id': doc.publication_type_id, 'category_id': doc.category_id, 'Nombre de Archivo': doc.nombre_archivo_formal, 'Compendios Normas ids': '', 'Descripción del documento': doc.descripcion_documento_excel, 'IDE Archivo': '', '_nombre_fisico': doc.nombre_archivo_fisico}
        datos_para_excel.append(fila)
    columnas_finales = ['Título', 'Nombre de norma (opcional)', 'Descripción', 'Fecha de publicación (dd/mm/yyyy)', 'Archivo', 'publication_type_id', 'category_id', 'Nombre de Archivo', 'Compendios Normas ids', 'Descripción del documento']
    df = pd.DataFrame(datos_para_excel)
    added_cols = []
    for col in columnas_finales:
        if col not in df.columns:
            df[col] = ''
            added_cols.append(col)
    if added_cols:
        logger.debug('Se añadieron columnas faltantes: %s', added_cols)
    df_final = df[columnas_finales]
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Importación')
            worksheet = writer.sheets['Importación']
            for i, column in enumerate(worksheet.columns):
                max_length = 0
                column_letter = column[0].column_letter
                try:
                    if column[0].value:
                        max_length = len(str(column[0].value))
                except Exception:
                    pass
                for cell in column[1:51]:
                    try:
                        if cell.value:
                            length = len(str(cell.value))
                            if length > max_length:
                                max_length = length
                    except Exception:
                        pass
                adjusted_width = min(max(max_length + 2, 10), 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    except Exception as e:
        logger.exception('Error generando Excel en memoria: %s', e)
        raise
    else:
        logger.info('Excel generado en memoria: %d filas, %d columnas', len(df_final), len(df_final.columns))
    output.seek(0)
    logger.info('Excel consolidado generado exitosamente (%d bytes)', len(output.getvalue()))
    return output
