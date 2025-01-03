import csv
import bisect
import json
import re


#es mas eficiente tener una lista con los ejercicios y luego dentro de cada ejercicio tener otra lista con la informacion de los pasos(respuestas incorrectas blabla)
class Ejercicio:
    def __init__(self, contentCode, id, steps):
        self.contentCode = contentCode #string
        self.id = id #int
        self.steps = steps #Lista de pasos del ejercicio, para cada paso se tendra una lista de respuestas incorrectas, para cada una se tendra su frecuencia y la lista de estudiantes que contestaron esa respuesta

class Paso:
    def __init__(self, contentCodeEj, stepId, cantRespuestas, respuestaCorrecta, incorrectas):
        self.contentCodeEj = contentCodeEj #String
        self.stepId = stepId #int
        self.cantRespuestas=cantRespuestas  #Cantidad de respuestas que tiene el paso
        self.correctAnswer = respuestaCorrecta #Respuesta correcta de ese paso en especifico
        self.wrongAnswers = incorrectas #Lista de respuestas incorrectas, para cada una se tendra su frecuencia y la lista de estudiantes que contestaron esa respuesta

class Respuestaincorrecta:
    def __init__(self, contentCodeExcercise, answer, frecuency, students):
        self.contentCodeExercise = contentCodeExcercise #String
        self.answer = answer #lista de strings(ya que en un paso pueden haber varias respuestas)
        self.frecuency = frecuency
        self.students = students #tendra los ids de los estudiantes que hayan contestado esta respuesta incorrecta(lista de enteros)

class Respuestacorrecta:
    def __init__(self, contentCode,stepId,answer):
        self.contentCode=contentCode
        self.stepId=stepId
        self.answer=answer
#Con esta funcion se añadiran ejercicios a la lista de forma ordenada, para que la busqueda sea mas eficiente
def addExercise(listaEjercicios, ejercicio):
    bisect.insort(listaEjercicios, ejercicio, key=lambda ej: ej.contentCode)

#Busqueda binaria adaptada para una lista de elementos de tipo Ejercicio, se busca segun la id de los ejercicios
def binarySearchExercise(listaEjercicios, codeX, left, right):
    if right>=left :
        mid = (left+right)//2
        if listaEjercicios[mid].contentCode==codeX:
            return mid #Retornamos el indice dela lista donde se encuentra el ejercicio buscado
        elif codeX < listaEjercicios[mid].contentCode:
            return binarySearchExercise(listaEjercicios, codeX, left, mid-1)
        else:
            return binarySearchExercise(listaEjercicios, codeX, mid+1,right)
    else:
        return -1

#Funcion que añade un paso a la lista de pasos de un ejercicio, se iran añadiendo de manera ordenada de acuerdo a la id del paso
def addStep(listaPasos, paso):
    bisect.insort(listaPasos, paso, key=lambda step: step.stepId)
    
#Busqueda binaria adaptada para una lista de elementos de tipo Paso, se busca segun la id de los pasos
def binarySearchStep(listaPasos, idPaso, left, right):
    if right>=left :
        mid = (left+right)//2
        if listaPasos[mid].stepId==idPaso:
            return mid #Retornamos el indice dela lista donde se encuentra el paso buscado
        elif idPaso < listaPasos[mid].stepId:
            return binarySearchStep(listaPasos, idPaso, left, mid-1)
        else:
            return binarySearchStep(listaPasos, idPaso, mid+1,right)
    else:
        return -1

#Recibe el arreglo con las distintas respuestas incorrectas a un paso y una respuesta incorrecta y debe buscarla en el array 
def searchWrongAnswer(listaRespuestas, respuestaIncorrecta):
    largo=len(listaRespuestas)
    i=0
    while(i<largo and listaRespuestas[i].answer != respuestaIncorrecta):
        i=i+1
    if i<largo:
        return i
    else:
        return -1

def addStudent(listaEstudiantes, idEstudiante):
    # Encontrar la posición donde debería estar el estudiante
    pos = bisect.bisect_left(listaEstudiantes, idEstudiante)
    # Verificar si el estudiante ya existe
    if pos == len(listaEstudiantes) or listaEstudiantes[pos] != idEstudiante:
        listaEstudiantes.insert(pos, idEstudiante)
        return True  # Se agregó el estudiante
    return False  # El estudiante ya existía


#Funcion que extrae las respuestas del campo extra
def clean_latex_string(latex_str):
    # Eliminar caracteres de control como \x0c
    return latex_str.replace("\x0c", "f")

def preprocess_json(data):
    # Reemplazar barras invertidas no escapadas
    data = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', data)
    return data
#Como el campo extra es formato json, podemos transformarlo de string a json y despues extraer la respuesta
def extract_responses(data):
    try:
        # Preprocesar la cadena JSON para evitar errores de formato
        data = preprocess_json(data)
        
        # Intentar cargar el JSON desde la cadena
        parsed_data = json.loads(data)
        response = parsed_data.get("response", None)
        
        # Si la respuesta es None o es una lista con un único elemento null
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
                elif isinstance(item, str):
                    result.append(clean_latex_string(item))
                elif isinstance(item, dict) and "value" in item:
                    result.append(clean_latex_string(item["value"]))
            return result

        # Si la respuesta es un diccionario (como selección múltiple)
        if isinstance(response, dict):
            result = []
            for values in response.values():
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, dict) and "value" in value:
                            result.append(clean_latex_string(value["value"]))
            return result

        # Devolver array vacío si no se puede procesar
        return []
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return []
    



#Creamos una lista donde iran los ejercicios, se iran añadiendo los ejercicios de manera ordenada segun su id
ejercicios=[]
respuestasCorrectas=[]


#encoding='utf-8', se usa '""' como quotechar por el campo 'extra', ya que este tiene ',' dentro
with open('Copy of data-1734621405509.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    #Saltamos a la seguna linea, ya que la primera contiene los nombres de los campos
    next(spamreader)
 
    #Recorremos el archivo csv linea por linea
    for row in spamreader:
        verbName=row[2]
        #hay 332 ejercicios, 5 de los cuales tiene stepId como array y otros 25 no tienen respuestas incorrectas
        
        if(verbName=="tryStep"):
            isCorrect = int(row[4])
            contentCode= row[0]
            if isCorrect==0 :
                
                try:
                    numPaso=int(row[9])
                    #Ignorar los ejercicios wp(word problems) no seran modificados, tienen stepId como array
                except ValueError:
                    continue
                respuesta=extract_responses(row[13])   
            
                exerciseIndex=binarySearchExercise(ejercicios, contentCode, 0, len(ejercicios)-1)
                #Si el ejercicio no esta en la lista,lo añadimos
                if (exerciseIndex)==-1 :
                    #Creamos un objeto de tipo respuestaIncorrecta, frecuencia 1 ya que es la primera respuesta incorrecta de este tipo
                    wrongAnswer=Respuestaincorrecta(contentCode,respuesta,1,[int(row[6])])
                    #Creamos un objeto de tipo Paso, cantidad de respuestas que tiene el paso  y respuesta correcta aun no se añaden
                    paso=Paso(contentCode,numPaso,None,None,[wrongAnswer])
                    #Creamos un objeto de tipo Ejercicio
                    idEjercicio=int(row[1])
                    ejercicioNuevo = Ejercicio(contentCode, idEjercicio, [paso])
                    addExercise(ejercicios, ejercicioNuevo)
                    continue
                #Si el ejercicio esta, pero no esta el paso, entonces lo añadimos a la lista de pasos de ese ejercicio
                stepIndex=binarySearchStep(ejercicios[exerciseIndex].steps, numPaso, 0, len(ejercicios[exerciseIndex].steps)-1)
                if (stepIndex==-1):
                    ejercicio=ejercicios[exerciseIndex]
                    #Creamos un objeto de tipo respuestaIncorrecta, frecuencia 1 ya que es la primera respuesta incorrecta de este tipo
                    wrongAnswer=Respuestaincorrecta(contentCode,respuesta,1,[int(row[6])])
                    #Creamos un objeto de tipo Paso, cantidad de respuestas que tiene el paso  y respuesta correcta aun no se añaden
                    paso=Paso(contentCode,numPaso,None,None,[wrongAnswer])
                    #Añadimos el paso al ejercicio
                    addStep(ejercicio.steps, paso)
                    continue
                wrongAnswerIndex=searchWrongAnswer(ejercicios[exerciseIndex].steps[stepIndex].wrongAnswers, respuesta)
                #Si esta el ejercicio y el paso, pero no esa respuesta, entonces la añadimos
                if (wrongAnswerIndex==-1):
                    #Creamos la respuesta y la agregamos
                    wrongAnswer=Respuestaincorrecta(contentCode,respuesta,1,[int(row[6])])
                    ejercicios[exerciseIndex].steps[stepIndex].wrongAnswers.append(wrongAnswer)
                    continue
                #Si ya existia el ejercicio, el paso y la respuesta, entonces modificamos la frecuencia y añadimos a la lista de estudiantes(si es que no estaba)
                ejercicios[exerciseIndex].steps[stepIndex].wrongAnswers[wrongAnswerIndex].frecuency+=1
                addStudent(ejercicios[exerciseIndex].steps[stepIndex].wrongAnswers[wrongAnswerIndex].students,int(row[6]))
            #Si nos encontramos con una respuesta correcta, la añadimos
            else:
                correctAnswer=extract_responses(row[13])
                try:
                    numPaso=int(row[9])
                    #Ignorar los ejercicios wp(word problems) no seran modificados, tienen stepId como array
                except ValueError:
                    continue
                #Buscamos el ejercicio
                exerciseIndex=binarySearchExercise(ejercicios, contentCode, 0, len(ejercicios)-1)
                #Si el ejercicio no esta en la lista,lo añadimos
                if (exerciseIndex)==-1 :
                    #Creamos un objeto de tipo Paso con la respuesta correcta del paso, cantidad de respuestas que tiene el paso aun no se añaden
                    paso=Paso(contentCode,numPaso,None,correctAnswer,[])
                    #Creamos un objeto de tipo Ejercicio
                    idEjercicio=int(row[1])
                    ejercicioNuevo = Ejercicio(contentCode, idEjercicio, [paso])
                    addExercise(ejercicios, ejercicioNuevo)
                    continue
                #Buscamos el paso
                stepIndex=binarySearchStep(ejercicios[exerciseIndex].steps, numPaso, 0, len(ejercicios[exerciseIndex].steps)-1)
                #Si esta el ejercicio pero no el paso, lo creamos y ponemos la respuesta correcta
                if (stepIndex==-1):
                    ejercicio=ejercicios[exerciseIndex]
                    #Creamos un objeto de tipo Paso con la respuesta correcta del paso, cantidad de respuestas que tiene el paso aun no se añade
                    paso=Paso(contentCode,numPaso,None,correctAnswer,[])
                    #Añadimos el paso al ejercicio
                    addStep(ejercicio.steps, paso)
                    continue
                if (ejercicios[exerciseIndex].steps[stepIndex].correctAnswer==None):
                    ejercicios[exerciseIndex].steps[stepIndex].correctAnswer=correctAnswer


# Crear y escribir en el archivo CSV
archivo = "salida.csv"

with open(archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
    escritor = csv.writer(archivo_csv)

    # Escribir encabezados
    encabezados = ["ContentCode", "stepId", "Respuesta correcta","Respuesta Incorrecta 1","Respuesta Incorrecta 2","Respuesta Incorrecta 3","Respuesta Incorrecta 4","Respuesta Incorrecta 5"]
    escritor.writerow(encabezados)

    # Iterar sobre los arreglos y escribirlos en el archivo
    for ejercicio in ejercicios:
        contentCode=ejercicio.contentCode
        for paso in ejercicio.steps:
            idPaso=paso.stepId
            respuestasCorrecta=paso.correctAnswer
            linea=[contentCode,str(idPaso),respuestasCorrecta]
            
            if(paso.wrongAnswers==None):
                for i in range(0,5):
                    respuestaBlanco="\"\",0,0"
                    linea.append(respuestaBlanco)
            elif(len(paso.wrongAnswers)<5):
                #Añadimos las repsuestas que haya
                respuestasIncorrectas=paso.wrongAnswers.sort(key=lambda x: x.frecuency, reverse=True)
                for i in range(0,len(paso.wrongAnswers)):
                    respuestaMala=str(paso.wrongAnswers[i].answer) +','+ str(len(paso.wrongAnswers[i].students)) + ',' + str(paso.wrongAnswers[i].frecuency)
                    linea.append(respuestaMala)
                #El resto lo completamos con respuestas en blanco
                for i in range(0,5-len(paso.wrongAnswers)):
                    respuestaBlanco="\"\",0,0"
                    linea.append(respuestaBlanco)

                #["combfracc","0","'fracc4{}5'","'frac{}34',3,2"....]
            else:
                respuestasIncorrectas=paso.wrongAnswers.sort(key=lambda x: x.frecuency, reverse=True)
                #Añadimos las repsuestas que haya
                for i in range(0,5):
                    respuestaMala=str(paso.wrongAnswers[i].answer) +","+str(len(paso.wrongAnswers[i].students))+ "," + str(paso.wrongAnswers[i].frecuency)
                    linea.append(respuestaMala)
            escritor.writerow(linea)


print(f"Archivo {archivo} creado con éxito.")

                
#primero ver si el ejercicio existe, luego ver si ya han habido respuestas para ese paso, luego ver si ya existia esa respuesta incorrecta, si no habia alguna, se crea
#Primero almacenar en un struct(lista)
#code del ejercicio, paso, respuesta correcta, lista de respuestas incorrectas con su frecuencia y una lista con estudiantes que dieron esa respuesta incorrecta