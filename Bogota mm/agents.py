from mesa import Agent
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import numpy as np
import random
import math

CAMAS_DISPONIBLES=47
UCIS_DISPONIBLES=14

class personas(Agent):
        """Inicialización de los atributos del agente
        Sexo: hombre o mujer
        Edad: se asigna de acuerdo con la distribución de la edad de la localidad a la que pertenece el agente.
        Mododetransporte: publico o privado
        Síntomas?: true si es sintomático, false dlc
        Estado: Tipo de contagio que toma los siguientes valores: no contagiado [1], contagio leve asintomático o sintomático[2], 
        contagio grave [3], contagio crítico [4], recuperado [5]
        TiempoRecuperacion: Tiempo de recuperación del paciente (días)
        TiempoContagiado: tiempo que lleva contagiado el agente
        Posición inicial: posición inicial del agente
        Posición final: posición final del agente
        zona: zona a la que pertenece
        """
    
        def __init__(self, n_id, modelo,poblacion,m, n_estado, t_contagio, densidad, acumedad,sexo, edades, transporte, Casillas_zona, acummovilidad, movilidad, dias_cuarentena,long_paso,porcentaje_en_cuarentena):
            super().__init__(n_id,modelo)
            
            #Se definen los parámetros de la infección
            self.estado = n_estado
            #Calcula los contactos en los diferentes movimientos que hace el agente
            self.contactos_trabajo = 0
            self.contactos_transporte = 0
            self.contactos_casa = 0
            self.hogar = 0
            
            #Guarda los ids de los agentes (o el mismo agente) a lo largo de los contactos desde que es contagioso
            self.lista_contactos_trabajo = []
            self.lista_contactos_transporte = []
            self.lista_contactos_casa = []
            
            #Parámetros de la infección en el agente
            self.infectados = 0
            self.trecuperacion = 100 #tiempo de recuperación
            self.tcontagio = t_contagio #parámetro del tiempo de contagio
            
            #Parámetros para la activación de la cuarentena
            self.cuarentena = 0 #parámetro de la cuarentena. 1 hay cuarentena, 0 no hay cuarentena
            self.cuarentena_permanente = 0
            self.tcuarentena = 0 #tiempo en cuarentena
            self.dias_cuarentena = dias_cuarentena
            self.revisar_muerte = 1
            self.porcentaje_en_cuarentena=porcentaje_en_cuarentena
            self.en_cama = 0 #parámetro que guarda si la gente se encuentra hospitalizado. 1-s1, 0-no
            self.en_uci = 0 #parámetro que guarda si la gente se encuentra en uci. 1-s1, 0-no
            self.procesado = 0 #parámetro que guarda si una persona estuvo en el proceso hospitalario para no aplicar el proceso de muerte
            self.thospitalizado = 0 #tiempo en hospitaización
            self.tuci = 0 #tiempo en uci

            #Parámetros para la verificación de la curva de reportados
            self.testeado = 0 #parámetro para verificar que alguien está en proceso de testing
            self.detectado = 0 #parámetro para verificar que el test detecto el virus en el agente
            self.tiempo_test = 0
            self.intervencion = 0 #dicotómica para saber si la persona es objeto de una intervención
            self.detectado_intervencion = 0 #parámetro para contabilizar las detecciones por la intervención
            self.para_contact = 0 #parámetro que va a verificar en los testeados en hospital si fueron objeto de contact_tracing

            #Parámetros de la movilidad en la grilla
            self.m = m
            self.long_paso = long_paso
            self.poblacion = poblacion
            
            #Guarda los nuevos casos de infectados
            self.nuevo_infectado = 0

            #Se asigna la zona de acuerdo a la densidad poblacional
            self.set_zona(densidad)

            #Se asigna el sexo: 1 - hombre, 2 - mujer
            self.set_sexo(sexo)
                             
            #Se asigna la edad
            self.set_edad(acumedad, edades)
            
            #Ahora, dependiendo de la zona y edad se asigna el transporte: #1 - público, 2 - privado
            self.set_transporte(transporte, edades)
            
            #Se define si es asintomático o no #1 - sintomático (20%) , 2 - asintomático (80%)
            self.set_sintomas()
            
            #Se define la posición inicial, actual y final de acuerdo a la zona
            self.posin = random.choice(Casillas_zona[str(self.zona)])
            self.pos = self.posin

            self.model.grid._place_agent(self.pos,self)

            self.set_posf(acummovilidad, movilidad, Casillas_zona)
            
            
        def set_zona(self, densidad): #método que asigna la zona para los agentes
            numdens = random.random()
            acumzonas = []
            #Crea la acumulada
            for fila in range(len(densidad["localidad"])):
                if fila == 0:
                    acumzonas.append(densidad["densidad"][fila])
                else:
                    suma=densidad["densidad"][fila]+ acumzonas[fila-1]
                    acumzonas.append(suma)
            #Asigna la zona    
            for i in range(len(acumzonas)):
                if i == 0:
                    if numdens<acumzonas[i]:
                        self.zona = densidad["localidad"][i]
                elif i == len(acumzonas)-1:
                    if numdens>= acumzonas[i-1] and numdens<=1.0:
                        self.zona = densidad["localidad"][i]
                else:
                    if numdens>= acumzonas[i-1] and numdens<acumzonas[i]:
                        self.zona = densidad["localidad"][i]
            

        def set_posf(self, acummovilidad, movilidad, Casillas_zona): #Método que asigna la posición final y su zona
            numpos = random.random()
            lista = list(movilidad.columns[1:])
            probabilidades = acummovilidad[self.zona]
            for i in range(len(probabilidades)):
                if i == 0:
                    if numpos<probabilidades[i]:
                        self.zona_destino = lista[i]
                        self.posf = random.choice(Casillas_zona[str(self.zona_destino)])
                        break
                else:
                    if numpos<probabilidades[i] and numpos>=probabilidades[i-1]:
                        self.zona_destino = lista[i]
                        self.posf = random.choice(Casillas_zona[str(self.zona_destino)])
                        break
            
        # "Método para asignar el tipo de sintomas"
        def set_sintomas(self): #Método que asigna la probabilidad de ser sintomático y asintomático
            numsint = random.random() 
            if numsint <= 0.3:
                self.sintomas = 1 #caso sintomático
            else:
                self.sintomas = 2 #caso asintomático
    
        # "Método para asignar el tipo de transporte dependiendo de la edad"
        def set_transporte(self, transporte, edades): #Método que asigna el modo de transporte
            #Primero la zona
            numtrans = random.random()
            for fila in range(len(edades["localidad"])):
                #Si el agente pertenece a la zona validada entonces se revisa la edad
                if self.zona == edades["localidad"][fila]: 
                    if self.edad >= 0 and self.edad <= 4: #Entre 0 y 4 años
                        if numtrans <= transporte["pub-0-4"][fila]:
                            self.modtrans = 1
                        else:
                            self.modtrans = 2
                    if self.edad > 4 and self.edad <= 19: #Entre 5 y 19
                        if numtrans <= transporte["pub-5-19"][fila]:
                            self.modtrans = 1
                        else:
                            self.modtrans = 2
                            
                    if self.edad > 19 and self.edad <= 39: #Entre 20 y 39
                        if numtrans <= transporte["pub-20-39"][fila]:
                            self.modtrans = 1
                        else:
                            self.modtrans = 2
                                                        
                    if self.edad > 39 and self.edad <= 59: #Entre 40 y 59
                        if numtrans <= transporte["pub-40-59"][fila]:
                            self.modtrans = 1
                        else:
                            self.modtrans = 2
                                                                                    
                    if self.edad > 59: #Más de 60
                        if numtrans <= transporte["pub->60"][0]:
                            self.modtrans = 1
                        else:
                            self.modtrans = 2
        
        # "Método para asignar la edad dependiendo de la zona"
        def set_edad(self, acumedad, edades): #Método que asigna la edad
            numedad = random.random()
            rangos = []
            lista = list(edades.columns[1:22])
            for i in range(len(lista)):
                n1 = 5*(i)
                n2 = 5*(i+1)-1
                l =[n1,n2]
                rangos.append(l)
            probabilidades = acumedad[self.zona]
            for i in range(len(probabilidades)):
                if i == 0:
                    if numedad<=probabilidades[i]:
                        self.edad = random.randint(rangos[i][0],rangos[i][1])
                        break
                elif i == len(probabilidades)-1:
                        self.edad = random.randint(rangos[i][0],rangos[i][1])
                        break
                else:
                    if numedad<=probabilidades[i] and numedad>probabilidades[i-1]:
                        self.edad = random.randint(rangos[i][0],rangos[i][1])
                        break
                        
        # "Método para asignar el sexo dependiendo de la zona"                
        def set_sexo(self,sexo):
            numsexo = random.random()
            for i in range(len(sexo["localidad"])):
                if self.zona == sexo["localidad"][i]:
                    if numsexo < sexo["hombres"][i]:
                        self.sexo = 1 #asigna hombre
                    else:
                        self.sexo = 2 #asigna mujer
            
        # "Método para eliminar a los agentes"
        def matar(self):
            #matar a los agentes. Pendiente de trabajo futuro es tener modelado la hospitalización
            try:
                if self.estado == 3 or self.estado == 4:
                    if self.procesado == 0 and self.revisar_muerte == 1: 
                        s1 = random.random()
                        if self.edad <= 9: #rango de edad de 0-9
                            if s1 < 0.00002:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        if self.edad > 9 and self.edad <= 19: #rango de edad de 10-19
                            if s1 < 0.00004:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 19 and self.edad <= 29: #rango de edad de 20-29
                            if s1 < 0.0003:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 29 and self.edad <= 39: #rango de edad de 30-39
                            if s1 < 0.0008:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 39 and self.edad <= 49: #rango de edad de 40-49
                            if s1 < 0.0015:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 49 and self.edad <= 59: #rango de edad de 50-59
                            if s1 < 0.006:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 59 and self.edad <= 69: #rango de edad de 60-69
                            if s1 < 0.022:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        elif self.edad > 69 and self.edad <= 79: #rango de edad de 70-79
                            if s1 < 0.051:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        else: #rango de edad de 6más de 80
                            if s1 < 0.093:
                                self.model.grid._remove_agent(self.pos,self)
                                self.model.schedule.remove(self)
                        self.revisar_muerte = 0
            except:
                print("Está intentando eliminar a alguien que ya no está, pero el programa seguirá corriendo.")
        
        def cambiar_estado(self):
            if self.estado == 2:
                if self.tcontagio == 13 and self.sintomas == 1: #cambia de leve a grave (hospitalización) o crítico (UCI)
                    s1 = random.random()
                    if self.edad <= 9: #rango de edad de 0-9
                        self.estado = (2 if s1 > 0.001 else 3)
                    if self.edad > 9 and self.edad <= 19: #rango de edad de 10-19
                        self.estado = (2 if s1 > 0.003 else 3)
                    elif self.edad > 19 and self.edad <= 29: #rango de edad de 20-29
                        self.estado = (2 if s1 > 0.012 else 3)
                    elif self.edad > 29 and self.edad <= 39: #rango de edad de 30-39
                        self.estado = (2 if s1 > 0.032 else 3)
                    elif self.edad > 39 and self.edad <= 49: #rango de edad de 40-49
                        self.estado = (2 if s1 > 0.049 else 3)
                    elif self.edad > 49 and self.edad <= 59: #rango de edad de 50-59
                        self.estado = (2 if s1 > 0.102 else 3)
                    elif self.edad > 59 and self.edad <= 69: #rango de edad de 60-69
                        self.estado = (2 if s1 > 0.166 else 3)
                    elif self.edad > 69 and self.edad <= 79: #rango de edad de 70-79
                        self.estado = (2 if s1 > 0.243 else 3)
                    else: #rango de edad de 6más de 80
                        self.estado = (2 if s1 > 0.273 else 3)
            if self.estado == 3:
                if self.tcontagio == 18 and self.sintomas == 1: #cambia de leve a grave (hospitalización) o crítico (UCI)
                    s2 = random.random()
                    if self.edad <= 9: #rango de edad de 0-9
                        self.estado = ( 3 if s2 > 0.05 else 4)
                    if self.edad > 9 and self.edad <= 19: #rango de edad de 10-19
                        self.estado = (3 if s2 > 0.05 else 4)
                    elif self.edad > 19 and self.edad <= 29: #rango de edad de 20-29
                        self.estado = (3 if s2 > 0.05 else 4)
                    elif self.edad > 29 and self.edad <= 39: #rango de edad de 30-39
                        self.estado = (3 if s2 > 0.05 else 4)
                    elif self.edad > 39 and self.edad <= 49: #rango de edad de 40-49
                        self.estado = (3 if s2 > 0.05 else 4)
                    elif self.edad > 49 and self.edad <= 59: #rango de edad de 50-59
                        self.estado = (3 if s2 > 0.122 else 4)
                    elif self.edad > 59 and self.edad <= 69: #rango de edad de 60-69
                        self.estado = (3 if s2 > 0.274 else 4)
                    elif self.edad > 69 and self.edad <= 79: #rango de edad de 70-79
                        self.estado = (3 if s2 > 0.432 else 4)
                    else: #rango de edad de 6más de 80
                        self.estado = (3 if s2 > 0.709 else 4)
            
            #recupera a los infectados
            if self.estado != 1 and self.estado != 5  and self.tcontagio == self.trecuperacion: 
                self.tcontagio = 0
                self.estado = 5

        def validacion_cuarentena (self,tiempo_cuarentena):
            #Validar continuación de la cuarentena  
            if self.tcuarentena >= tiempo_cuarentena and self.cuarentena == 1 and self.cuarentena_permanente == 0:
                self.cuarentena = 0
                self.tcuarentena = 0
            
            #Actualizar tiempo en cuarentena si la hay
            if self.cuarentena == 1:
                self.tcuarentena += 1
                
        def validacion_testing(self):
            #Revisar finalización del testing y actualización del resultado del test
            if self.testeado == 1 and self.tiempo_test > 2:
                if self.estado==2 or self.estado==3 or self.estado==4 or self.estado==5:
                    self.detectado = 1
                    self.testeado = 0
                    self.tiempo_test = 0
                    self.cuarentena = 1
                    self.dias_cuarentena += 14
                    self.detectado_intervencion = (1 if self.intervencion == 1 else 0)
                else:
                    self.detectado = 0
                    self.testeado = 0
                    self.tiempo_test = 0
                    self.detectado_intervencion = 0

            #Actualizar tiempo del test
            if self.testeado == 1 and self.detectado == 0:
                self.tiempo_test += 1
                
        # "Método actualización de estados"
        def actualizar_tiempos(self):
            if self.estado == 2:
                if self.trecuperacion == 100:
                    #print("cambio tiempo recuperación para agente con estado 2")
                    self.trecuperacion = 14

            #Lleva a cama a los que requieren hospitalización por 8 días
            if self.estado == 3:                    
                if self.trecuperacion == 100 or self.trecuperacion == 14:
                    #print("cambio tiempo recuperación para agente con estado 3")
                    self.trecuperacion = 22 + random.randint(1,20)

            #Lleva a cama a los que van a requerir uci
            if self.estado == 4:                    
                if self.trecuperacion == 100 or self.trecuperacion == 14:
                    #print("cambio tiempo recuperación para agente con estado 4")
                    self.trecuperacion = 36 + random.randint(1,6)
   
            #Actualizar tiempos de hospitalización y uci
            if self.en_cama == 1:
                self.thospitalizado +=1

            if self.en_uci == 1:
                self.tuci += 1

            #actualiza los tiempos de contagio
            if self.estado != 1 and self.estado != 5  and self.tcontagio < self.trecuperacion: 
                self.tcontagio += 1
            
        def testing (self):
            if self.estado == 3 or self.estado == 4:
                if self.testeado == 0 and self.detectado == 0:
                    self.testeado = 1
                    self.para_contact = 1

        def contact_tracing (self):
            self.testeado = 1
            self.intervencion = 1
       
        def recopilar_contactos(self,arreglo):
            contactos_casa = unique(self.lista_contactos_casa)
            if len(contactos_casa)>0:
                for i in contactos_casa:
                    if i.testeado==0 and i.detectado==0:
                        arreglo.append(i)
                self.para_contact = 0 
                
        def activar_zonificacion(self,zona,tiempo):
            if self.zona == zona:
                self.cuarentena = 1
                self.dias_cuarentena = tiempo
                    
        def step(self):
            self.contactos_trabajo = 0
            self.contactos_transporte = 0
            self.contactos_casa = 0
            m = self.m            
            vel_carro = 26.88*(1000/60)*(1/m)
            vel_tm = 27.06*(1000/60)*(1/m)
            vel_wk = 4.38*(1000/60)*(1/m)

            #Viaja en la zona de la casa
            n_posx =int( self.pos[0] + round(random.uniform(-5,5)))
            n_posy =int( self.pos[1] + round(random.uniform(-5,5)))
            
            cuadros = (abs(self.pos[0]-n_posx)+abs(self.pos[1]-n_posy))
            vel = vel_wk
            tviaje = cuadros *(1/vel)
            self.m_encasa(tviaje,self.long_paso,[n_posx,n_posy])
            
            #viaja al trabajo
            cuadros = (abs(self.pos[0]-self.posf[0])+abs(self.pos[1]-self.posf[1]))
            vel = (vel_carro if self.modtrans == 1 else vel_tm)
            tviaje = cuadros *(1/vel)
            self.mtrabajo(tviaje,self.long_paso)
            
            #viaja en zona
            n_posx =int( self.pos[0] + round(random.uniform(-5,5)))
            n_posy =int( self.pos[1] + round(random.uniform(-5,5)))
            
            cuadros = (abs(self.pos[0]-n_posx)+abs(self.pos[1]-n_posy))
            vel = vel_wk
            tviaje = cuadros *(1/vel)
            self.mzona(tviaje,self.long_paso,[n_posx,n_posy])
            
            #viaja de devuelta a casa
            cuadros = (abs(self.pos[0]-self.posin[0])+abs(self.pos[1]-self.posin[1]))
            vel = (vel_carro if self.modtrans == 1 else vel_tm)
            tviaje = cuadros *(1/vel)
            self.mcasa(tviaje,self.long_paso)
            
            #actualización
            self.nuevo_infectado = (1 if self.estado==2 and self.tcontagio == 0 else 0)
            self.cambiar_estado()
            self.validacion_testing()
            self.validacion_cuarentena(self.dias_cuarentena)
            self.testing()
            self.matar()
            self.actualizar_tiempos()
        
        #Método para dejar solo los valores únicos de una lista
        def unique(lista):
            unique_list = []
            for x in lista:
                if x not in unique_list:
                    unique_list.append(x)
            return unique_list
        
        #    "Organizar la cuarentena de un porcentaje de la población"
        def activar_cuarentena(self,activar_cuarentena,porcentaje_en_cuarentena,tiempo_en_cuarentena):
            if activar_cuarentena == True and tiempo_en_cuarentena>0 and self.cuarentena==0:
                r = random.random()
                if( self.edad > 18 and self.edad < 70):
                    if(r<porcentaje_en_cuarentena): #a un porcentaje de la población les restringe la movilidad
                        self.cuarentena = 1
                else:
                    #Se restringe la movilidad a los mayores de 70 y menos de 19 de manera indefinda
                    self.cuarentena_permanente = 1
                    self.cuarentena = 1
        
        #  "Construcción del método de infectar"
        def infectar(self,arreglo):
            if self.estado == 2 and self.tcontagio >= 5:
                agentes = self.model.grid.get_cell_list_contents([self.pos])
                if (len(agentes) > 1):
                    for i in range(len(agentes)):
                        agente = agentes[i]
                        if agente.estado == 1:
                            s = random.random()
                            if(self.sintomas == 1):
                                # caso de infección por sintomático
                                if (s <= 0.098):
                                    agente.estado = 2
                                    self.infectados +=1
                                    arreglo.append(agente)
                                    
                            else:
                                # caso de infección por asintomático
                                if (s <= 0.098 * 0.5):
                                    agente.estado = 2
                                    self.infectados +=1
                                    arreglo.append(agente)


        # "Construcción del método de mover en casa"
        def m_encasa(self, tiempo, intervalo,poszona):
            if self.estado != 3 and self.estado != 4 and self.cuarentena == 0 and self.cuarentena_permanente==0:
                count = 0
                dt = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                movs = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                mv1 = round(euc_dist(self.pos,poszona)/dt)
                #print("t: ",tiempo, " - inter: ",intervalo)
                while movs > 0 or self.pos != poszona:
                    n_pasos_req = abs(self.pos[0]-poszona[0])+abs(self.pos[1]-poszona[1])
                    mv2 = round(euc_dist(self.pos,poszona)/(movs))
                    #print("Pos: ",self.pos," - posf: ",poszona)
                    #print("Iteración: ", count," pasos_req: ",n_pasos_req)
                    #print("movs: ",movs)
                    if movs == 1:
                        paso = n_pasos_req
                        #print("paso_f: ",paso)
                        n_pos = moverxy([self.pos[0],self.pos[1]], [poszona[0],poszona[1]],paso)
                        agentes = self.model.grid.get_cell_list_contents([self.pos])
                        if (n_pos == self.pos):
                            contactos_casa = []
                            for i in agentes:
                                if self.hogar == i.hogar and self.unique_id!= i.unique_id:
                                    contacts_casa.append(i)
                            self.contactos_casa += (len(contactos_casa) if len(contactos_casa)> 0 else 0)
                            self.model.grid.move_agent(self,n_pos)
                            self.infectar(contactos_casa)
                            break       
                            
                        else:
                            self.contactos_casa += (len(agentes) if len(agentes)> 0 else 0)
                            self.model.grid.move_agent(self,n_pos)
                            self.infectar(self.lista_contactos_casa)
                            break
                    else:
                        paso =  (min(mv1,mv2) if (mv1!=0 and mv2!=0) else n_pasos_req)
                        if paso == 0:
                            break
                        else:
                            #print("paso_f: ",paso)
                            n_pos = moverxy([self.pos[0],self.pos[1]], [poszona[0],poszona[1]],paso)
                            agentes = self.model.grid.get_cell_list_contents([self.pos])
                            self.contactos_casa += (len(agentes) if len(agentes)> 0 else 0)
                            self.infectar(self.lista_contactos_casa)
                            count += 1
                            movs -= 1

        # "Construcción del método de mover en zona"
        def mzona(self, tiempo, intervalo,poszona):
            if self.estado != 3 and self.estado != 4 and self.cuarentena == 0 and self.cuarentena_permanente==0:
                count = 0
                dt = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                movs = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                mv1 = round(euc_dist(self.pos,poszona)/dt)
                #print("t: ",tiempo, " - inter: ",intervalo)
                while movs > 0 or self.pos != poszona:
                    n_pasos_req = abs(self.pos[0]-poszona[0])+abs(self.pos[1]-poszona[1])
                    mv2 = round(euc_dist(self.pos,poszona)/(movs))
                    #print("Pos: ",self.pos," - posf: ",poszona)
                    #print("Iteración: ", count," pasos_req: ",n_pasos_req)
                    #print("movs: ",movs)
                    if movs == 1:
                        paso = n_pasos_req
                        #print("paso_f: ",paso)
                        n_pos = moverxy([self.pos[0],self.pos[1]], [poszona[0],poszona[1]],paso)
                        agentes = self.model.grid.get_cell_list_contents([self.pos])
                        self.contactos_trabajo += (len(agentes) if len(agentes)> 0 else 0)
                        self.model.grid.move_agent(self,n_pos)
                        self.infectar(self.lista_contactos_trabajo)
                        break
                    else:
                        paso =  (min(mv1,mv2) if (mv1!=0 and mv2!=0) else n_pasos_req)
                        if paso == 0:
                            break
                        else:
                            #print("paso_f: ",paso)
                            n_pos = moverxy([self.pos[0],self.pos[1]], [poszona[0],poszona[1]],paso)
                            agentes = self.model.grid.get_cell_list_contents([self.pos])
                            self.contactos_trabajo += (len(agentes) if len(agentes)> 0 else 0)
                            self.infectar(self.lista_contactos_trabajo)
                            count += 1
                            movs -= 1
                            
        #Construcción del método de regresar a casa
        def mcasa(self, tiempo, intervalo):
            if self.estado != 3 and self.estado != 4 and self.cuarentena == 0 and self.cuarentena_permanente==0:
                count = 0
                dt = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                movs = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                mv1 = round(euc_dist(self.pos,self.posin)/dt)
                #print("t: ",tiempo, " - inter: ",intervalo)
                while movs > 0 or self.pos != self.posin:
                    n_pasos_req = abs(self.pos[0]-self.posin[0])+abs(self.pos[1]-self.posin[1])
                    mv2 = round(euc_dist(self.pos,self.posin)/(movs))
                    #print("Pos: ",self.pos,"- posin: ",self.posin," - posf: ",self.posf)
                    #print("Iteración: ", count," pasos_req: ",n_pasos_req)
                    #print("movs: ",movs)
                    if movs == 1:
                        paso = n_pasos_req
                        #print("paso_f: ",paso)
                        n_pos = moverxy([self.pos[0],self.pos[1]], [self.posin[0],self.posin[1]],paso)
                        agentes = self.model.grid.get_cell_list_contents([self.pos])
                        self.contactos_transporte += (len(agentes) if len(agentes)> 0 else 0)
                        self.model.grid.move_agent(self,n_pos)
                        if self.modtrans == 1:
                            self.infectar(self.lista_contactos_transporte)
                        break
                    else:
                        paso =  (min(mv1,mv2) if (mv1!=0 and mv2!=0) else n_pasos_req)
                        if paso == 0:
                            break
                        else:
                            #print("paso_f: ",paso)
                            n_pos = moverxy([self.pos[0],self.pos[1]], [self.posin[0],self.posin[1]],paso)
                            agentes = self.model.grid.get_cell_list_contents([self.pos])
                            self.contactos_transporte += (len(agentes) if len(agentes)> 0 else 0)
                            self.model.grid.move_agent(self,n_pos)
                            if self.modtrans == 1:
                                self.infectar(self.lista_contactos_transporte)
                            count += 1
                            movs -= 1
                            
        #Construcción del método de mover a trabajo
        def mtrabajo(self, tiempo, intervalo) : 
            #tiempo en minutos, intervalo es la longitud del paso en minutos
            if self.estado != 3 and self.estado != 4 and self.cuarentena == 0 and self.cuarentena_permanente==0:
                count = 0
                dt = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                movs = (1 if (tiempo// intervalo) == 0 else (tiempo// intervalo))
                mv1 = round(euc_dist(self.pos,self.posf)/dt)
                #print("t: ",tiempo, " - inter: ",intervalo)
                while movs > 0 or self.pos != self.posf:
                    n_pasos_req = abs(self.pos[0]-self.posf[0])+abs(self.pos[1]-self.posf[1])
                    mv2 = round(euc_dist(self.pos,self.posf)/(movs))
                    #print("Pos: ",self.pos,"- posin: ",self.posin," - posf: ",self.posf)
                    #print("Iteración: ", count," pasos_req: ",n_pasos_req)
                    #print("movs: ",movs)
                    if movs == 1:
                        paso = n_pasos_req
                        #print("paso_f: ",paso)
                        n_pos = moverxy([self.pos[0],self.pos[1]], [self.posf[0],self.posf[1]],paso)
                        agentes = self.model.grid.get_cell_list_contents([self.pos])
                        self.contactos_transporte += (len(agentes) if len(agentes)> 0 else 0)
                        self.model.grid.move_agent(self,n_pos)
                        if self.modtrans == 1:
                            self.infectar(self.lista_contactos_transporte)
                        break
                    else:
                        paso = (min(mv1,mv2) if (mv1!=0 and mv2!=0) else n_pasos_req)
                        if paso ==0:
                            break
                        else:
                            #print("paso_f: ",paso)
                            n_pos = moverxy([self.pos[0],self.pos[1]], [self.posf[0],self.posf[1]],paso)
                            agentes = self.model.grid.get_cell_list_contents([self.pos])
                            self.contactos_transporte += (len(agentes) if len(agentes)> 0 else 0)
                            self.model.grid.move_agent(self,n_pos)
                            if self.modtrans == 1:
                                self.infectar(self.lista_contactos_transporte)
                            count += 1
                            movs -= 1

def acum_trans(l1,lbase,ledad,lzona):
    #l1 es la base de nombres de las zonas
    #lbase es la base de datos para calcular la acumulada
    #ledad es el rango de edad en string. P.ej: "5-19"
    #lzona es la zona del agente
    matching = [s for s in lbase if ledad in s]
    l = []
    for t in range(len(l1)):
        if (l1[t]==lzona):
            for j in range(len(matching)):
                if(j==0):
                    l.append(lbase[matching[j]][t])
                else:
                    suma = lbase[matching[j]][t] + l[j-1]
                    l.append(suma)
    return l


def unique(lista):
    unique_list = []
    for x in lista:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

import math
def euc_dist(a,b): #Calcula la distancia eucliadiana entre dos puntos. a y b son dos tuplas con las posicioanes iniciales (a) y finnales(b)
    return math.sqrt(((a[0]-b[0])**2)+((a[1]-b[1])**2))

import numpy as np
def moverxy(posi,posf,paso): #Método para calcular la mejor ruta entre dos puntos
    dist = euc_dist(posi,posf) #calcula la distancia
    l = []
    count = -paso
    while count < paso + 1:
        l.append(count)
        count +=1
    dists = []
    coords = []
    #mira x
    for i in range(len(l)):
        for j in range(len(l)):
            suma = abs(l[i])+abs(l[j])
            if suma == paso:
                n_posx = int(posi[0]+l[i])
                n_posy = int(posi[1]+l[j])
                dist2 = euc_dist([n_posx,n_posy],posf)
                coords.append([n_posx,n_posy])
                dists.append(dist2)
    
    for i in range(len(l)):
        for j in range(len(l)):
            suma = abs(l[i])+abs(l[j])
            if suma == paso:
                n_posy = int(posi[1]+l[i])
                n_posx = int(posi[0]+l[j])
                dist2 = euc_dist([n_posx,n_posy],posf)
                coords.append([n_posx,n_posy])
                dists.append(dist2)
    index_min = np.argmin(dists)
    return tuple(coords[index_min])
