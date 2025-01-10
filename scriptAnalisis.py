import csv
import re
import json
from parseo import normalize_expression
from sympy import sympify
from dicc import ejercicios_por_topico

#Esta funcion busca a que topico pertenece un ejercicio, recibe el contentId de un ejercicio y lo busca en el diccionario ejercicios_por_topico
def buscar_topico(ejercicio):
    for topico, contenido in ejercicios_por_topico.items():
        # Verificar si contenido es un diccionario antes de usar .get
        if isinstance(contenido, dict):
            #Recorremos los subtopicos 
            for subtopico, ejercicios in contenido.items():
                    #Verificamos i el ejercicio pertenece al subtopico, si es asi devolvemos el topico actual
                    if ejercicio in ejercicios:
                        return topico
    return None




#Funcion que corrige el formato de las expresiones con fraccion
def clean_latex_string(latex_str):
    # Eliminar caracteres de control como \x0c
    return latex_str.replace("\x0c", "f")

#Esta función recibe una cadena de texto, busca las barras invertidas y las reemplaza por dos barras invertidas para evitar errores de interpretación.
def preprocess_json(data):
    # Reemplazar directamente las barras invertidas
    return re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', data, flags=re.DOTALL)


#Como el campo extra es formato json, podemos transformarlo de string a json y despues extraer la respuesta
def extract_responses(data):
    try:
        # Preprocesar la cadena JSON para evitar errores de formato
        data = preprocess_json(data)
        
        # Intentar cargar el JSON desde la cadena
        parsed_data = json.loads(data)
        response = parsed_data.get("response", None)
        
        # Si la respuesta es None o es una lista con un único elemento null retornamos un array vacio
        if response is None or response == [None]:
            return []

        # Si la respuesta es un string, devolverlo como array
        if isinstance(response, str):
            return [clean_latex_string(response)]

        # Si la respuesta es una lista
        if isinstance(response, list):
            result = []
            for item in response:
                # Si el item es una lista, procesamos cada elemento dentro de la sublista
                if isinstance(item, list):
                    for subitem in item:
                        result.append(clean_latex_string(subitem))
                #Si es un string, lo procesamos y lo añadimos a la lista
                elif isinstance(item, str):
                    result.append(clean_latex_string(item))
                #Si es un diccionario, lo procesamos y extramos el valor de la llave value para añadirlo al array
                elif isinstance(item, dict) and "value" in item:
                    result.append(clean_latex_string(item["value"]))
            return result

        # Si la respuesta es un diccionario (como selección múltiple)
        if isinstance(response, dict):
            result = []
            for values in response.values():
                #Extraemos las respuestas del campo llamado 'value'
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, dict) and "value" in value:
                            result.append(clean_latex_string(value["value"]))
            return result

        # Devolver array vacío si no se puede procesar
        return []
    except json.JSONDecodeError as e:
        #print(f"Error al decodificar JSON: {e}")
        return []
    
# Función para añadir un ejercicio y sus respuestas
def anadir_ejercicio(contentCode, paso, respuesta, respuesta_parseada, id_estudiante, es_correcta, id_topico):
    global ejercicios
    # Verificar si el ejercicio ya existe
    #Si no esta, lo añadimos al diccionario ejercicios
    if contentCode not in ejercicios:
        #Obtenemos el topico del ejercicio segun su contentId
        topico=buscar_topico(contentCode)
        #Añadimos el ejercicio
        ejercicios[contentCode] = {
            "topico": topico,  # o el tópico que desees
            "pasos": {}
        }
   

    # Verificar si el paso existe en el ejercicio
    #Si no esta, lo añadimos al diccionario de pasos del ejercicio actual
    if paso not in ejercicios[contentCode]["pasos"]:
        ejercicios[contentCode]["pasos"][paso] = {
            "respuesta_correcta": None,  # Inicialmente vacío
            "respuesta_correcta_parseada": None,
            "respuestas_incorrectas": {}  # Diccionario de respuestas incorrectas
        }

    # Si la respuesta es correcta, la agregamos en el campo correspondiente
    if es_correcta:
        # Verificar si la respuesta correcta ya está asignada
        respuesta_correcta_actual = ejercicios[contentCode]["pasos"][paso].get("respuesta_correcta", None)
        # Si no está asignada, la asignamos
        if respuesta_correcta_actual is None:
            ejercicios[contentCode]["pasos"][paso]["respuesta_correcta"] = respuesta
            ejercicios[contentCode]["pasos"][paso]["respuesta_correcta_parseada"] = respuesta_parseada
    

    else:
        # Si es incorrecta, procedemos a agregar la respuesta incorrecta
        respuesta_str = str(respuesta)  # Usamos la representación en string de la respuesta para poder compararla con las otras respuestas
        clave=None
        # Verificar si la respuesta ya existe en alguna de las respuestas incorrectas
        respuesta_encontrada = False
        respuesta_equivalente=None
        for clave_respuesta, datos_respuesta in ejercicios[contentCode]["pasos"][paso]["respuestas_incorrectas"].items():
            # Buscar la respuesta en las listas de respuestas y respuestas_sympy
            #Comparamos las respuestas como string, en su forma bruta
            if datos_respuesta["respuestas"]==respuesta:

                respuesta_encontrada = True
                clave=clave_respuesta
                break
            #Si no eran exactamente iguales, procedemos a comparar su version parseada con sympy
            elif respuesta_parseada and respuesta_parseada == datos_respuesta["respuestas_sympy"]:
                respuesta_encontrada = True
                #Si son iguales, eso quiere decir que las respuestas son lo mismo matematicamente, pero son distintas expresiones, por lo tanto, son respuestas equivalentes
                respuesta_equivalente=respuesta
                clave=clave_respuesta
                break
        
        # Si no se encuentra la respuesta, la agregamos como nueva
        if not respuesta_encontrada:
            #Creamos el ejercicio y lo añadimos, la clave sera la misma respuesta en bruto pero en formato string
            clave=respuesta_str
            ejercicios[contentCode]["pasos"][paso]["respuestas_incorrectas"][clave] = {
                "frecuencia": 1,
                "estudiantes": [id_estudiante],
                "respuestas": respuesta,
                "respuestas_sympy": respuesta_parseada,
                "respuestas_equivalentes": []
            }
            return

        # Si ya exisitia la respuesta incrementamos la frecuencia, agregamos el id del estudiante y añadimos las respuestas equivalentes a la lista si es que las hay
        respuestas_incorrectas = ejercicios[contentCode]["pasos"][paso]["respuestas_incorrectas"][clave]
        respuestas_incorrectas["frecuencia"] += 1
        if id_estudiante not in respuestas_incorrectas["estudiantes"]:
            respuestas_incorrectas["estudiantes"].append(id_estudiante)
        if respuesta_equivalente!=None and respuesta_equivalente not in respuestas_incorrectas["respuestas_equivalentes"]:
            respuestas_incorrectas["respuestas_equivalentes"].append(respuesta_equivalente)
        


    
#En el diccionario ejercicios almacenaremos toda la informacion de los ejercicios(pasos, respuestas,etc), la forma es la siguiente
'''
"ejercicio":{
    "topico": topico
    "pasos":{
        "numPaso":{
            "respuesta_correcta":[expresion1,expresion2]
            "respuesta_correcta_parseada": [expresion1_parseada, expresion2_parseada]
            "respuestas_incorrectas": {
                                "Incorrecta 1": {
                                    "frecuencia": 3,
                                    "estudiantes": [101, 102, 103],
                                    "respuestas": ["expresión 1", "expresión 2"],
                                    "respuestas_sympy": ["expresión 1 sympy", "expresión 2 sympy"]
                                    "respuestas_equivalentes": [["expresion1", "expresion2"]]
                                },
                                "Incorrecta 2": {
                                    "frecuencia": 2,
                                    "estudiantes": [104, 105],
                                    "respuestas": ["expresión A", "expresión B"],
                                    "respuestas_sympy": ["expresión A sympy", "expresión B sympy"]
                                    "respuestas_equivalentes": [["expresion1", "expresion2"]]
                                }
                }
            }
        }
                    '''
ejercicios={}
cont=0
cont2=0
#Abrimos el archivo .csv y procesamos las lineas
with open("datos-trystep-noexcel.csv", "r") as archivo:
    lector = csv.reader(archivo)
    next(lector)
    #Recorremos las lineas del archivo
    for linea in lector:
        
        if ("tryStep" in linea) and linea[9].isdigit():  # Revisa si "tryStep" está en cualquier campo e ignorar los ejercicios wp
            # Procesamos la línea aquí, extraemos el contentId, la respuesta, el id que nos dice si es correcta o no, el numero del paso y la id del estudiante
            cont2=cont2+1
            contentId=linea[0]
            isCorrect=int(linea[4])
            respuesta=extract_responses(linea[13])
            paso=int(linea[9])
            respuesta_parseada=[]
            idEstudiante=int(linea[6])
            try:
                id_topico=int(linea[8])
            except Exception as e:
                id_topico=0
            
            if(isCorrect==0):
                isCorrectBool=False
            else:
                isCorrectBool=True
            #Intentamos parsear las respuestas
            try:
                #Las vamos añadiendo al array de respuestas parseadas
                for i in range(0,len(respuesta)):
                    expresion=normalize_expression(respuesta[i])
                    expresion=sympify(expresion)
                    respuesta_parseada.append(expresion)
                anadir_ejercicio(contentId,paso,respuesta,respuesta_parseada,idEstudiante,isCorrectBool,id_topico)
            except Exception as e:
                #Si no podemos parsear una respuesta, dejamos el array de respuestas parseadas en None
                cont=cont+1
                respuesta_parseada=None
                anadir_ejercicio(contentId,paso,respuesta,respuesta_parseada,idEstudiante,isCorrectBool,id_topico)


print(100-((cont/cont2)*100))

# Crear y escribir en el archivo CSV
nombre_archivo = "salida.csv"


with open(nombre_archivo,mode="w", newline='', encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)


    # Escribir encabezado
    encabezado = [
        "ContentCode", "topico", "stepId", "Respuesta Correcta", "Incorrectas equivalentes a correcta",
        "Respuesta Incorrecta 1", "Respuesta Incorrecta 2", 
        "Respuesta Incorrecta 3", "Respuesta Incorrecta 4", 
        "Respuesta Incorrecta 5"
    ]
    escritor.writerow(encabezado)

    # Recorrer el diccionario ejercicios
    for content_code, datos in ejercicios.items():
        #Obtemeos la informacion para poner en las columnas
        topico = datos["topico"]
        if topico!=None:
            for step_id, paso_data in datos["pasos"].items():
                # Respuesta correcta
                respuesta_correcta = str(paso_data["respuesta_correcta"]) if paso_data["respuesta_correcta"] else ""             

                # Obtener respuestas incorrectas ordenadas por frecuencia
                respuestas_incorrectas = sorted(
                    paso_data["respuestas_incorrectas"].items(),
                    key=lambda item: item[1]["frecuencia"],
                    reverse=True
                ) 

                #Seleccionamos las respuestas equivalentes a la respuesta correctas:
                respuestas_equivalentes_correcta=[]
                #Respuestas correcta equivalente
                if paso_data["respuesta_correcta_parseada"]!=None:
                    for i in range(0, len(respuestas_incorrectas)):
                        clave, datos_respuesta = respuestas_incorrectas[i]
                        #Si respuesta ibcorrecta sympy es igual a respuesta correcta parseada, añadimos la lista de todas las respuestas incorrectas
                        if datos_respuesta["respuestas_sympy"]!=None and paso_data["respuesta_correcta_parseada"]==datos_respuesta["respuestas_sympy"]:
                            respuestas_equivalentes_correcta.append(datos_respuesta["respuestas"])
                            respuestas_equivalentes_correcta+=datos_respuesta.get("respuestas_equivalentes", [])
                if not (respuestas_equivalentes_correcta):
                    respuestas_equivalentes_correcta_string='"'
                else:
                    
                    respuestas_equivalentes_correcta_string=""
                    for j in range(0,len(respuestas_equivalentes_correcta)):
                        respuestas_equivalentes_correcta_string+=str(respuestas_equivalentes_correcta[j])
                   
                # Seleccionar hasta 5 respuestas incorrectas, y expandir si hay empates en N de estudiantes
                respuestas_incorrectas_columnas = []
                num_estudiantes_quinta = None

                for idx, (clave, datos_respuesta) in enumerate(respuestas_incorrectas):
                    respuesta_original = str(datos_respuesta["respuestas"])
                    respuestas_equivalentes = "".join(map(str, datos_respuesta.get("respuestas_equivalentes", [])))
                    frecuencia = datos_respuesta["frecuencia"]
                    num_estudiantes = len(set(datos_respuesta["estudiantes"]))

                    # Añadir respuestas:
                    if idx < 5:
                        num_estudiantes_quinta = num_estudiantes  # Actualizar el N de estudiantes de la quinta
                    elif num_estudiantes_quinta != num_estudiantes:
                        break  # Salir si el número de estudiantes ya no coincide

                    # Construir columna y agregar
                    respuestas_incorrectas_columnas.append(
                        f"{respuesta_original}{respuestas_equivalentes},{num_estudiantes},{frecuencia}"
                    )

                # Rellenar con valores vacíos si hay menos de 5 respuestas incorrectas
                while len(respuestas_incorrectas_columnas) < 5:
                    respuestas_incorrectas_columnas.append('",0,0')

                # Escribir fila
                fila = [
                    content_code,
                    topico,
                    step_id,
                    respuesta_correcta,
                    respuestas_equivalentes_correcta_string,
                    *respuestas_incorrectas_columnas
                ]
                escritor.writerow(fila)

print("Archivo generado correctamente.")
