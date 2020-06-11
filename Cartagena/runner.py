import json
import pickle
from model import ciudad
import pandas as pd
import os
import sys
#import city_grid
from mesa.batchrunner import BatchRunner

class Runner():
    def __init__(self, ruta_censo,ruta_movilidad, city, m, poblacion, area,porcentaje_agentes,infectados_iniciales,lpaso,
                dias_cuarentena,porcentaje_en_cuarentena, pruebas_disponibles,activacion_testing_aleatorio,activacion_contact_tracing,
                activación_cuarentena_acordeon,dia_inicio_acordeon,intervalo_acordeon, tiempo_zonificacion):
        
        #Recopilación matrices censo
        self.densidad = pd.read_excel(ruta_censo,sheet_name="densidad")
        self.edades = pd.read_excel(ruta_censo,sheet_name="edad")
        self.sexo = pd.read_excel(ruta_censo,sheet_name="sexo")
        #print(self.densidad.head())
        #print(self.edades.head())
        #print(self.sexo.head())
        #sys.exit()
        
        #Recopilación matrices movilidad
        self.transporte = pd.read_excel(ruta_movilidad,sheet_name="transporte")
        self.movilidad = pd.read_excel(ruta_movilidad,sheet_name="movilidad")
        #print("runs_well")

        #if not os.path.exists("Casillas_localidad_"+str(m)+".json"):
        #    print('Creando grida para m={}'.format(m))
        #    city_grid.create_grid(city=city, cell_size=m)
        with open("Casillas_localidad_"+str(m)+".json") as json_file:
            self.Casillas_zona = dict(json.load(json_file))

        for k, v in self.Casillas_zona.items():
            self.Casillas_zona[k] = list(map(tuple, v))

        with open('dim_grida_'+str(m)+'.pickle', 'rb') as h:
            self.Number_in_x, self.Number_in_y = pickle.load(h)

        dens = poblacion / area #densidad por km2
        dens = dens / 1000000 #densidad por m2
        dens = dens * (m**2)

        suma = 0
        for key in self.Casillas_zona.keys():
            suma += len(self.Casillas_zona[key])

        n_agentes = round(suma*dens*porcentaje_agentes)
        print("Población:",n_agentes)
        #sys.exit()   

        self.acumedad= self.calc_acumedad(self.edades)
        self.transpub = self.calc_transpub(self.transporte)
        self.acummovilidad = self.calc_acummovilidad(self.movilidad)


        self.model = ciudad(
            n_agentes,
            m,
            self.Number_in_x, 
            self.Number_in_y,
            infectados_iniciales,
            self.densidad, 
            self.acumedad, 
            self.sexo,
            self.edades, 
            self.transporte, 
            self.Casillas_zona, 
            self.acummovilidad,
            self.movilidad,
            dias_cuarentena,
            lpaso,
            porcentaje_en_cuarentena,
            pruebas_disponibles,
            activacion_testing_aleatorio,
            activacion_contact_tracing,
            activación_cuarentena_acordeon,
            dia_inicio_acordeon,
            intervalo_acordeon, 
            tiempo_zonificacion)

    def calc_acumedad(self, edades):
        datos = {}
        lista = list(edades.columns[1:22])
        for fila in range(len(edades["localidad"])):
            datos[edades["localidad"][fila]] = []
            for columna in range(len(lista)):
                if columna == 0:
                    datos[edades["localidad"][fila]].append(edades[lista[columna]][fila])
                else:
                    n = edades[lista[columna]][fila] + datos[edades["localidad"][fila]][columna-1]
                    datos[edades["localidad"][fila]].append(n)
        return datos
    
    def calc_acummovilidad(self, movilidad):
        datos = {}
        lista = list(movilidad.columns[1:22])
        print(lista)
        sys.exit()
        for fila in range(len(movilidad["localidad"])):
            datos[movilidad["localidad"][fila]] = []
            for columna in range(len(lista)):
                if columna == 0:
                    datos[movilidad["localidad"][fila]].append(movilidad[lista[columna]][fila])
                else:
                    n = movilidad[lista[columna]][fila] + datos[movilidad["localidad"][fila]][columna-1]
                    datos[movilidad["localidad"][fila]].append(n)
        return datos

    def calc_transpub(self, transporte):
        transpub={}
        for fila in range (len(transporte["localidad"])):
            transpub[transporte["localidad"][fila]]={}
            for i in range (1,6):
                transpub[transporte["localidad"][fila]][transporte.columns[i]]=[]
                transpub[transporte["localidad"][fila]][transporte.columns[i]].append(transporte[transporte.columns[i]][fila])
        return transpub
    
    def run(self,steps):
        for i in range(steps):
            print("empezando step {}".format(i))
            self.model.step()
            print("acabo step {}".format(i))
        return self.model.datacollector.get_model_vars_dataframe()