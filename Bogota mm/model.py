from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from agents import personas
import random

#Variables globales sobre las camas y las ucis
CAMAS_DISPONIBLES=47
UCIS_DISPONIBLES=14

#Variables globales sobre el testing aleatorio
PRUEBAS_DISPONIBLES = 0
TIEMPO = 64
OLAS = 0
ACTIVACION_TESTING_ALEATORIO = False

#Variables gobales sobre el contact-tracing
ACTIVACION_CONTACT_TRACING = False

#Variables para la activación de la cuarentena regular
ACTIVACION_CUARENTENA = False
DIA_INICIO_CUARENTENA = 4
DURACION_CUARENTENA = 0
PORCENTAJE_EN_CUARENTENA = 0

#Variables para la activación de la cuarentena por acordeón
ACTIVACION_CUARENTENA_ACORDEON = False
DIA_INICIO_ACORDEON = 0
INTERVALO_ACORDEON = 0

#Variables para la aplicación de la cuarentena zonificada
TIEMPO_ZONIFICACION = 0

class ciudad(Model):
    "Inicialización del modelo"
    "Se necesita incluir la base de datos, suponiendo que tendremos varias ciudades para que la inicialización sea genérica"
    def __init__(self,n,m,width,height,porcentaje_infectados, densidad, acumedad,sexo, edades, transporte, Casillas_zona, acummovilidad, movilidad,dias_cuarentena,long_paso, porcentaje_en_cuarentena, 
                pruebas_disponibles,activacion_testing_aleatorio,activacion_contact_tracing,activación_cuarentena_acordeon,
                 dia_inicio_acordeon,intervalo_acordeon, tiempo_zonificacion):
        self.total_agentes = n #número de agentes a iniciar
        self.schedule = RandomActivation(self) #inicialización en paralelo de todos los agentes
        self.grid = MultiGrid(width,height,True) #creación de la grilla genérica

        global PRUEBAS_DISPONIBLES 
        global ACTIVACION_CONTACT_TRACING
        global ACTIVACION_TESTING_ALEATORIO
        global OLAS
        global ACTIVACION_CUARENTENA_ACORDEON
        global DIA_INICIO_ACORDEON
        global INTERVALO_ACORDEON
        global ACTIVACION_CUARENTENA
        global DURACION_CUARENTENA
        global PORCENTAJE_EN_CUARENTENA
        global ACTIVACION_CUARENTENA_ZONIFICADA
        global DURACION_CUARENTENA_ZONIFICADA
        global PORCENTAJE_EN_CUARENTENA_ZONIFICADA
        global TIEMPO_ZONIFICACION

        #Inicialización de las variables globales
        PRUEBAS_DISPONIBLES = pruebas_disponibles
        ACTIVACION_CONTACT_TRACING = activacion_contact_tracing
        ACTIVACION_TESTING_ALEATORIO =  activacion_testing_aleatorio
        OLAS = round(PRUEBAS_DISPONIBLES/12)
        ACTIVACION_CUARENTENA_ACORDEON = activación_cuarentena_acordeon
        DIA_INICIO_ACORDEON = dia_inicio_acordeon
        INTERVALO_ACORDEON = intervalo_acordeon
        ACTIVACION_CUARENTENA = (True if dias_cuarentena > 0 else False)
        DURACION_CUARENTENA = dias_cuarentena
        PORCENTAJE_EN_CUARENTENA = porcentaje_en_cuarentena
        TIEMPO_ZONIFICACION = tiempo_zonificacion
        
        "Creación de cada agente"
        for i in range(self.total_agentes):
            n_id = random.random()
            estado = (2 if n_id > porcentaje_infectados else 1)
            tcontagio = (random.randint(5,9) if estado == 2 else 0)
            nuevo = personas(i,self,self.total_agentes,m,estado,tcontagio, densidad, acumedad, sexo, edades, 
            transporte, Casillas_zona, acummovilidad, movilidad, dias_cuarentena,long_paso,porcentaje_en_cuarentena) #asignación del id
            self.schedule.add(nuevo) #creación del agente en el sistema
            
        "Asignación del hogar"
        for i in Casillas_zona:
            values = Casillas_zona.get(i)
            for j in values:
                agentes = self.grid.get_cell_list_contents(j)
                if len(agentes)>0:
                    num_hogares = (1 if round(len(agentes)/4) == 0 else round(len(agentes)/4))
                    lista = [e for e in range(0,num_hogares)]
                    for z in agentes:
                        z.hogar = random.choice(lista)
        
        
        "Configurar el recolector de datos"
        self.datacollector = DataCollector(
            model_reporters = {"Susceptibles": susceptibles,"Total infectados": total_infectados,"Graves": infectados_graves,
                             "Críticos": infectados_criticos,"Leves": infectados_leves,"Recuperados":recuperados,"Rt": rt, "Recuento_zonas":recuento_zonas,
                             "0-4": recuento_ge1,"5-19": recuento_ge2,"20-39": recuento_ge3,
                              "40-59": recuento_ge4,">60": recuento_ge5,"En_cuarentena":en_cuarentena,"Vivos":agentes_vivos,
                              "Día":dia,"Contactos_prom_trabajo":prom_contactos_trabajo,"Contactos_prom_transporte":prom_contactos_transporte,
                              "Contactos_prom_casa": prom_contactos_casa,"Nuevos_infectados": nuevos_infectados,"Detectados":detectados, 
                              "En_testing": en_testing,"En_cama":en_cama,"En_UCI":en_uci,"Detectados_por_intervencion":detectados_interv,
                              "#Intervenidos":intervenidos}
        )
        self.running = True
    
    "Avanzar el modelo"
    def step(self):
        global PRUEBAS_DISPONIBLES
        global ACTIVACION_TESTING_ALEATORIO
        global ACTIVACION_CONTACT_TRACING
        global OLAS
        global ACTIVACION_CUARENTENA_ACORDEON
        global DIA_INICIO_ACORDEON
        global INTERVALO_ACORDEON
        global ACTIVACION_CUARENTENA
        global DIA_INICIO_CUARENTENA
        global DURACION_CUARENTENA
        global PORCENTAJE_EN_CUARENTENA
        
        self.datacollector.collect(self)
        self.cuarentena_regular(ACTIVACION_CUARENTENA,DIA_INICIO_CUARENTENA,DURACION_CUARENTENA,PORCENTAJE_EN_CUARENTENA)
        self.cuarentena_acordeon(ACTIVACION_CUARENTENA_ACORDEON,DIA_INICIO_ACORDEON,INTERVALO_ACORDEON)
        self.schedule.step()
        self.dinamica_hospitales()
        self.testing_aleatorio(PRUEBAS_DISPONIBLES,ACTIVACION_TESTING_ALEATORIO)
        self.contact_tracing(ACTIVACION_CONTACT_TRACING)
        self.cuarentena_zonificada(0.2)
        
    def cuarentena_zonificada(self,porcentaje_cierre):
        global TIEMPO_ZONIFICACION 
        agentes = [agent for agent in self.schedule.agents]
        zonas = []
        #Saca la lista de zonas
        for i in agentes:
            zonas.append(i.zona)
        zonas = unique(zonas)
        
        #Cálculo del porcentaje de detectados para cada zona
        for i in range(len(zonas)):
            suma_agentes_en_zona = 0
            suma_detectados = 0
            for j in agentes:
                if j.zona == i:
                    suma_agentes_en_zona +=1
                    suma_detectados += j.detectado
            porcentaje = suma_detectados/suma_agentes_en_zona
            if porcentaje > porcentaje_cierre:
                for j in agentes:
                    if j.cuarentena == 0:
                        j.activar_zonificacion(i,TIEMPO_ZONIFICACION)
                

    def cuarentena_regular(self,activacion,inicio,duracion,porcentaje):
        if activacion == True:
            t = self.schedule.time
            if t == inicio:
                agentes = [agent for agent in self.schedule.agents]
                print(activacion,inicio,duracion,porcentaje)
                for i in agentes:
                    i.activar_cuarentena(activacion,porcentaje,duracion)
                    print(i.cuarentena," t:",i.tcuarentena, " dt:",i.dias_cuarentena)
                    
    
    def cuarentena_acordeon(self,activacion,inicio,intervalo):
        global DIA_INICIO_ACORDEON
        global INTERVALO_ACORDEON
        global PORCENTAJE_EN_CUARENTENA
        if activacion == True:
            t = self.schedule.time
            if t == inicio:
                agentes = [agent for agent in self.schedule.agents]
                for i in agentes:
                    i.activar_cuarentena(activacion,PORCENTAJE_EN_CUARENTENA,intervalo)
                DIA_INICIO_ACORDEON += 2*INTERVALO_ACORDEON

    def contact_tracing(self,activacion):
        global PRUEBAS_DISPONIBLES
        if activacion == True:
            if PRUEBAS_DISPONIBLES > 0:
                lista_para_contact_tracing = []
                lista_para_intervenir = []
                agentes = [agent for agent in self.schedule.agents]
                for i in agentes:
                    if i.para_contact == 1 and i.detectado == 1:
                        lista_para_contact_tracing.append(i)
                if len(lista_para_contact_tracing)>0:
                    for i in lista_para_contact_tracing:
                        i.recopilar_contactos(lista_para_intervenir)
                    if len(lista_para_intervenir)>0:
                        lista_para_intervenir = unique(lista_para_intervenir)
                        for i in lista_para_intervenir:
                            if PRUEBAS_DISPONIBLES > 1:
                                i.contact_tracing()
                                PRUEBAS_DISPONIBLES-=1 

    def testing_aleatorio(self,pruebas,activacion):
        global TIEMPO
        global PRUEBAS_DISPONIBLES
        global OLAS
        if activacion == True:
            t = self.schedule.time
            agentes = [agent for agent in self.schedule.agents]
            if t == TIEMPO and pruebas > 0 and OLAS>0:
                disponibles = pruebas/OLAS
                if OLAS == 1:
                    for i in range(pruebas):
                        n_agente = random.choice(agentes)
                        n_agente = self.agente_valido(n_agente)
                        n_agente.testeado = 1
                        n_agente.intervencion = 1     
                        PRUEBAS_DISPONIBLES-=1     
                else:
                    for i in range(round(disponibles)):
                        n_agente = random.choice(agentes)
                        n_agente = self.agente_valido(n_agente)
                        n_agente.testeado = 1
                        n_agente.intervencion = 1
                        PRUEBAS_DISPONIBLES-=1 
                TIEMPO += 3
                OLAS -= 1

    def dinamica_hospitales(self):
        global CAMAS_DISPONIBLES
        global UCIS_DISPONIBLES
        agentes = [agent for agent in self.schedule.agents] #recopila los agentes del modelo
        agentes_para_hospital = []
        
        #0. trabajar solo con el arreglo de agentes graves o críticos
        for i in agentes:
            if i.estado == 3 or i.estado == 4:
                agentes_para_hospital.append(i)
        
        liberar_cama = []
        liberar_uci = []
        requerir_cama = []
        if len(agentes_para_hospital)>0:
            for i in agentes_para_hospital:
                #crear arreglos para priorizar salidas sobre ingresos en la orden de ejecución
                if i.estado == 3 and i.en_cama == 0: #ingresa a los graves a hospitalización
                    requerir_cama.append(i)                                  
                if i.estado == 3 and i.en_cama == 1 and i.thospitalizado == 8: #sale de hospitalización
                    liberar_cama.append(i)                
                if i.estado == 4 and i.en_cama == 1 and i.thospitalizado >= 6: #sale de hospitalización a UCI
                    liberar_cama.append(i)     
                if i.estado == 4 and i.en_uci == 1 and i.tuci >= 10:
                    liberar_uci.append(i)
                if i.estado == 4 and i.en_cama == 1 and i.thospitalizado == 6 and i.tcontagio >= 24:
                    liberar_cama.append(i)
        
        #Se van a liberar las personas de la cama
        if len(liberar_cama)>0:
            for i in liberar_cama: 
                if i.estado == 3 and i.en_cama == 1: #libero cama si son solo hospitalizados
                    i.en_cama = 0
                    CAMAS_DISPONIBLES +=1
                if i.estado == 4:
                    if i.en_cama == 1 and i.thospitalizado == 6 and i.tcontagio >= 24: #libero la cama de segunda estancia
                        i.en_cama = 0
                        CAMAS_DISPONIBLES +=1
                    else:
                        if i.en_cama == 1:
                            suma = UCIS_DISPONIBLES - 1
                            if suma >= 0: #libero cama si lo puedo meter en UCI
                                i.procesado = 1
                                i.en_cama = 0
                                i.thospitalizado = 0
                                CAMAS_DISPONIBLES +=1
                                i.en_uci = 1
                                UCIS_DISPONIBLES -=1
                            else:
                                i.procesado = 0
        #Se van a liberar las UCIs y se meten en camas si hay disponibles
        if len(liberar_uci)>0:
            #print("liberando UCIs")
            for i in liberar_uci:
                if i.en_uci == 1:
                    suma = CAMAS_DISPONIBLES - 1
                    if suma >= 0:
                        i.en_uci = 0
                        UCIS_DISPONIBLES += 1
                        i.en_cama = 1
                        CAMAS_DISPONIBLES -= 1
        #Se van a asignar cama para los que las necesitan
        if len(requerir_cama)>0:
            #print("asignado camas")
            for i in requerir_cama:
                if i.en_cama == 0:
                    suma = CAMAS_DISPONIBLES - 1
                    if suma >= 0:    
                        i.en_cama = 1
                        i.procesado = 1
                        CAMAS_DISPONIBLES -= 1
                
    def agente_valido(self,n_agente):
        if n_agente.testeado == 0 and n_agente.detectado==0 and n_agente.edad > 17 and n_agente.edad< 70:
            return n_agente
        else:
            agentes = [agent for agent in self.schedule.agents]
            return self.agente_valido(random.choice(agentes))    

        
#Cálculos por grupos de edad
import numpy as np

def unique(lista):
    unique_list = []
    for x in lista:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

def intervenidos(model):
    intervenidos = [agent.intervencion for agent in model.schedule.agents]
    suma = 0
    for i in intervenidos:
        suma+=i
    return suma

def detectados_interv(model):
    detectados = [agent.detectado_intervencion for agent in model.schedule.agents]
    suma = 0
    for i in detectados:
        suma+= i
    return suma

def en_cama(model):
    camas = [agent.en_cama for agent in model.schedule.agents]
    suma = 0 
    for i in camas:
        suma+=i
    return suma

def en_uci(model):
    camas = [agent.en_uci for agent in model.schedule.agents]
    suma = 0 
    for i in camas:
        suma+=i
    return suma

def recuento_ge1 (model): #grupo de 0-4
    estado = [agent.estado for agent in model.schedule.agents]
    ledad= [agent.edad for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        suma_nuevos = 0
        suma_detectados = 0
        for j in range(len(estado)):
            if (ledad[j]<5 and estado[j]==i):
                suma +=1
                suma_nuevos+= nuevos[j]
                suma_detectados+= detectados[j]
        l.append(suma)
        l.append(suma_nuevos)
        l.append(suma_detectados)
    return l
def recuento_ge2 (model): #grupo de 5-19
    estado = [agent.estado for agent in model.schedule.agents]
    ledad= [agent.edad for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        suma_nuevos = 0
        suma_detectados = 0
        for j in range(len(estado)):
            if (ledad[j]<20 and ledad[j]>=5 and estado[j]==i):
                suma +=1
                suma_nuevos+= nuevos[j]
                suma_detectados+= detectados[j]
        l.append(suma)
        l.append(suma_nuevos)
        l.append(suma_detectados)
    return l
def recuento_ge3 (model): #grupo de 20-39
    estado = [agent.estado for agent in model.schedule.agents]
    ledad= [agent.edad for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        suma_nuevos = 0
        suma_detectados = 0
        for j in range(len(estado)):
            if (ledad[j]<40 and ledad[j]>=20 and estado[j]==i):
                suma +=1
                suma_nuevos+= nuevos[j]
                suma_detectados+= detectados[j]
        l.append(suma)
        l.append(suma_nuevos)
        l.append(suma_detectados)
    return l
def recuento_ge4 (model): #grupo de 40-59
    estado = [agent.estado for agent in model.schedule.agents]
    ledad= [agent.edad for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        suma_nuevos = 0
        suma_detectados = 0
        for j in range(len(estado)):
            if (ledad[j]<60 and ledad[j]>=40 and estado[j]==i):
                suma +=1
                suma_nuevos+= nuevos[j]
                suma_detectados+= detectados[j]
        l.append(suma)
        l.append(suma_nuevos)
        l.append(suma_detectados)
    return l
def recuento_ge5 (model): #grupo >=60
    estado = [agent.estado for agent in model.schedule.agents]
    ledad= [agent.edad for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        suma_nuevos = 0
        suma_detectados = 0
        for j in range(len(estado)):
            if (ledad[j]>=60 and estado[j]==i):
                suma +=1
                suma_nuevos+= nuevos[j]
                suma_detectados+= detectados[j]
        l.append(suma)
        l.append(suma_nuevos)
        l.append(suma_detectados)
    return l

#Cálculos globales
import statistics as st

def detectados(model):
    detectados = [agent.detectado for agent in model.schedule.agents]
    suma = 0
    for i in detectados:
        suma += i
    return suma
def en_testing(model):
    testeados = [agent.testeado for agent in model.schedule.agents]
    suma = 0
    for i in testeados:
        suma += i
    return suma

def nuevos_infectados(model):
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    suma = 0
    for i in nuevos:
        suma += i
    return suma

def prom_contactos_trabajo(model):
    contactos = [agent.contactos_trabajo for agent in model.schedule.agents]
    return st.mean(contactos)

def prom_contactos_transporte(model):
    contactos = [agent.contactos_transporte for agent in model.schedule.agents]
    return st.mean(contactos)

def prom_contactos_casa(model):
    contactos = [agent.contactos_casa for agent in model.schedule.agents]
    return st.mean(contactos)

def total_infectados(model):
    return infectados_leves(model) + infectados_graves(model) + infectados_criticos(model)

def susceptibles(model):
    infectados = [agent.estado for agent in model.schedule.agents]
    cuenta = 0
    for i in infectados:
        if i==1:
            cuenta+=1
    return cuenta

def infectados_leves(model):
    infectados = [agent.estado for agent in model.schedule.agents]
    cuenta = 0
    for i in infectados:
        if i==2:
            cuenta+=1
    return cuenta

def infectados_graves(model):
    infectados = [agent.estado for agent in model.schedule.agents]
    cuenta = 0
    for i in infectados:
        if i==3: 
            cuenta+=1
    return cuenta

def infectados_criticos(model):
    infectados = [agent.estado for agent in model.schedule.agents]
    cuenta = 0
    for i in infectados:
        if i==4:
            cuenta+=1
    return cuenta

def recuperados(model):
    infectados = [agent.estado for agent in model.schedule.agents]
    cuenta = 0
    for i in infectados:
        if i==5:
            cuenta+=1
    return cuenta

def agentes_vivos(model):
    return model.schedule.get_agent_count()

def dia(model):
    return model.schedule.time

def en_cuarentena(model):
    estado = [agent.estado for agent in model.schedule.agents]
    cuarentena = [agent.cuarentena for agent in model.schedule.agents]
    k = [1,2,3,4,5]
    l = []
    for i in k:
        suma = 0
        for j in range(len(cuarentena)):
            if (cuarentena[j]==1 and estado[j]==i):
                suma +=1
        l.append(suma)
    return l

def rt(model):
    infectados = [agent.infectados for agent in model.schedule.agents]
    estado = [agent.estado for agent in model.schedule.agents]
    tiempo = [agent.tcontagio for agent in model.schedule.agents]
    cuenta = 0
    suma = 0
    res = 0
    for i in range(len(infectados)):
        if(estado[i]==2 or estado[i]==3 or estado[4] and tiempo[i]>=5):
            cuenta+=1
            suma+=infectados[i]
            res = (0 if cuenta == 0 else suma/cuenta)
    return res

def recuento_zonas (model):
    estado = [agent.estado for agent in model.schedule.agents]
    zonas = [agent.zona for agent in model.schedule.agents]
    nuevos = [agent.nuevo_infectado for agent in model.schedule.agents]
    detectados = [agent.detectado for agent in model.schedule.agents]
    l_zonas = unique(zonas)
    l_estados = [1,2,3,4,5]
    a = {}
    for i in l_zonas:
        l = []
        for z in l_estados:
            suma = 0
            suma_nuevos = 0
            suma_detectados = 0
            for j in range(len(zonas)):
                if (zonas[j] == i and estado[j]==z):
                    suma +=1
                    suma_nuevos+= nuevos[j]
                    suma_detectados+= detectados[j]
            l.append(suma)
            l.append(suma_nuevos)
            l.append(suma_detectados)
        a[i]=l
    return a

