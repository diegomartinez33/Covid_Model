import runner
import sys

city = 'cartagena'

print(city)
sys.exit()
#rutas datos
#ruta_datos_censo = "C:/Users/af.useche10/Dropbox (Uniandes)/COVID_19_MODEL/Datos/insumos_modeloabm/bogota/datos_censo_vf.xlsx"
#ruta_datos_movilidad = "C:/Users/af.useche10/Dropbox (Uniandes)/COVID_19_MODEL/Datos/insumos_modeloabm/bogota/datos_movilidad_vf.xlsx"
#rutas datos
ruta_datos_censo = "./datos_censo_vf_cartagena.xlsx"
ruta_datos_movilidad = "./datos_movilidad_vf_cartagena.xlsx"

#parámetros del modelo
m = 250 #tamaño de la grilla
infectados_iniciales = 0.999 #porcentaje de infectados iniciales
porcentaje_agentes = 0.1 #porcentaje de agentes con respecto a la estimación
longitud_de_paso = 15 #ventana de tiempo del movimiento de los agentes
dias_cuarentena = 70 #Días que durará la primera cuarentena
porcentaje_en_cuarentena = 0.86 #Porcentaje de restricción a la movilidad en la cuarentena
poblacion = 914552 #población de la ciudad
area = 610 #área de la ciudad
n_corridas = 150 #número de corridas del modelo

#Parámetros para la activactión de intervenciones
pruebas_disponibles = 220 #pruebas disponibles para realizar
activacion_testing_aleatorio = False #parámetro para activar la realización del testing aleatorio
activacion_contact_tracing = False #parámetro para activar la realización del contact tracing

activacion_cuarentena_acordeon = False #parámetro para activar la cuarentena por acordeon después de la cuarentena regular
dia_inicio_acordeon = 90 #Día de inicio de la cuarentena por acordeón
intervalo_acordeon = 14 #intervalo de reactivación de la cuarentena por acordeón

tiempo_zonificacion = 20 #duración de la cuarentena

#Inicializar un mundo
rn = runner.Runner(ruta_datos_censo,ruta_datos_movilidad, city, m, poblacion,area,porcentaje_agentes,infectados_iniciales,longitud_de_paso,dias_cuarentena,
                    porcentaje_en_cuarentena, pruebas_disponibles,activacion_testing_aleatorio,activacion_contact_tracing,
                   activacion_cuarentena_acordeon,dia_inicio_acordeon,intervalo_acordeon,tiempo_zonificacion)
#Ejecutar las corridas
data = rn.run(n_corridas)

#Rutina de impresión
modalidad = ("ta" if activacion_testing_aleatorio == True else ("ca" if activacion_contact_tracing == True else "gral"))
modalidad_cuarentena = ("smpl" if activacion_cuarentena_acordeon == False else "acdn")
data.to_csv('{}_{}_{}_pb.csv'.format(dias_cuarentena,modalidad_cuarentena,modalidad, pruebas_disponibles))
data.to_csv('pb.csv')
print("-------------------------------------")
print("Data saved\n")