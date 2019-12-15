'''
Este programa implementa los métodos Esquina Noroeste, Multiplicadores Modi (Distribucion Modificada) y Cruce del Arroyo (Salto de Piedra en Piedra)

Como tal los metodos antes mencionados pertenecen a la materia Investigacion de Operaciones

    Aplicacion de los metodos
-El metodo Esquina Noroeste sirve para obtener la solución inicial

-El metodo Modi sirve para conocer la celda a partir de la cual se hara la optimizacion solo y nada mas en
la solucion inicial, se podria decir que es una especie de metodo unitario de verificacion

-El metodo Cruce del Arroyo sirve para encontrar las rutas de cada celda y optimizar una solucion inicial
'''

from functools import reduce
import heapq
import copy
import collections

class CellDataContainer:
    PIECE_WAYS = {'UP': 'up', 'DOWN': 'down', 'LEFT' : 'left', 'RIGHT': 'right'}

    def __init__(self, cell_content, cell_weight):
        self.cell_weight = cell_weight
        self.cell_content = cell_content
        self.valid_ways = []
        self.path = []
        self.path_cost = 0

    #se reescribe el metodo para poder usar una pila de prioridad en esta clase
    def __lt__(self, other):
        return self.cell_content < other.cell_content

class PathCostHeapElement:
    def __init__(self, coords, path_cost):
        self.coords = coords
        self.path_cost = path_cost

    def __lt__(self, other):
        return self.path_cost < other.path_cost

class Board:
    #variable usada para evitar circuitos infinitos
    aux_path = 0

    visited_cells = {}

    def __init__(self, offers, demands, costs):
        self.offers = offers
        self.demands = demands
        self.costs = costs

        '''
            f: numero de filas
            c: numero de columnas
            
            son variables usadas para determinar si la nueva solucion calculada con el metodo Cruce del Arroyo no esta degenerada
        '''
        self.f = len(self.offers)
        self.c = len(self.demands)

        self.row_limit = len(self.costs) - 1
        self.column_limit = len(self.costs[0]) - 1

        self.configuration = {}
        self.empty_cells = {}
        self.full_table = {}
        self.z = 0
        self.modi_data = {}

        #se obtiene la oferta total y la demanda total
        offer_counting = reduce(lambda a, b: a+b, self.offers)
        demand_counting = reduce(lambda a, b: a+b, self.demands)

        #si la oferta es menor que la demanda se agrega una nueva fila
        if offer_counting < demand_counting:
            fictional_client = demand_counting - offer_counting
            self.offers.append(fictional_client)
            offer_counting += fictional_client

            #se agrega la nueva fila
            self.costs.append([])
            for i in range(0, len(self.costs[0])):
                self.costs[len(self.costs)-1].append(0)

        #si la oferta es mayor que la demanda se agrega una nueva columna
        if offer_counting > demand_counting:
            fictional_source = offer_counting - demand_counting
            self.demands.append(fictional_source)
            demand_counting += fictional_source

            #se agrega la nueva columna
            for row in range(0, len(self.costs)):
                self.costs[row].append(0)

        #se calculan las piezas de piedra
        j = 0
        for i in range(0, len(self.offers)):
            while j < len(self.demands):

                '''
                ESTE SEGMENTO SE REMOVIO PARA PODER ESCALONAR LA TABLA ESQUINA NOROESTE EN ALGUNOS CASOS
                
                #solo se continua con la siguiente demanda si la actual es cero
                if demands[j] == 0:
                    j+=1
                    continue
                '''

                if self.demands[j] < self.offers[i]:
                    self.configuration.update({(i, j): CellDataContainer(self.demands[j], self.costs[i][j])})
                else:
                    self.configuration.update({(i, j): CellDataContainer(self.offers[i], self.costs[i][j])})

                #se realiza la resta natural para calcular el nuevo valor de la oferta
                new_offer = self.offers[i] - self.demands[j]
                if new_offer < 0:
                    new_offer =0

                #se realiza la resta natural para calcular el nuevo valor de la demanda
                new_demand = self.demands[j] - self.offers[i]
                if new_demand < 0:
                    new_demand = 0

                #se asignan las restas naturales
                self.offers[i] = new_offer
                self.demands[j] = new_demand

                #si la oferta es cero se continua con la siguiente oferta
                if self.offers[i] == 0:
                    break

                j+=1

        #se genera la tabla esquina noroeste
        for i in range(len(self.costs)):
            for j in range(len(self.costs[i])):
                if self.configuration.get((i, j)) != None:
                    self.full_table.update({(i,j):self.configuration.get((i,j))})
                else:
                    self.empty_cells.update({(i, j):CellDataContainer(None, costs[i][j])})
                    self.full_table.update({(i,j):self.empty_cells.get((i, j))})

        #se calcula el valor de z de la solucion inicial
        self.z = self.calculate_z(self.configuration)

        #se imprime la tabla esquina noroeste y el valor z
        self.print_array_table(self.costs, "Tabla de Costos")
        self.print_north_west_corner_solution(self.configuration, self.z)

        #se definen los caminos validos de cada celda y se construyen los circuitos
        self.set_valid_ways(self.full_table)
        self.set_path_on_cell(self.empty_cells, self.full_table)

        is_optimum = self.is_optimum(self.empty_cells, self.full_table)

        print("*************************************")
        print("Es la Solucion Optima?", is_optimum)
        print("*************************************")

        if is_optimum == False:
            print("Dado que la solucion inicial no es optima")
            #se hacen los calculos del metodo modi
            self.modi_data = self.modi_method(self.configuration, self.costs)

            #se imprimen los calculos del metodo modi
            #self.print_modi_method_solution(self.modi_data)

            '''
            NECESITA ARREGLO
            
            first_verification = self.modi_first_verification(self.empty_cells, self.full_table, self.modi_data)
            empty_cells_min_cost_coords = first_verification['empty_cells_min_cost_coords']
            min_content_on_path = first_verification['min_content_on_path']
            '''

            #se optimiza la tabla esquina noroeste con el metodo del arroyo
            self.optimize(self.empty_cells, self.full_table)

    #imprime un array de dos dimensiones
    def print_array_table(self, array_table, label=""):
        print(label)
        for row in array_table:
            print(row)
        print("*************************************")

    #imprime el diccionario esquina noroeste
    def print_north_west_corner_dict(self, north_west_corner_dict, label=""):
        print(label)
        items = list(north_west_corner_dict.items())
        for e in items:
            print(e[0], e[1].cell_content, e[1].cell_weight)
        print("*************************************")

    #calcula el valor de z
    def calculate_z(self, north_west_corner_dict):
        z = 0
        for element in north_west_corner_dict.items():
            z += element[1].cell_content * element[1].cell_weight
        return z

    #imprime el diccionario esquina noroeste con su respectivo valor z
    def print_north_west_corner_solution(self, north_west_corner_dict, z, label ="Tabla Esquina Noroeste"):
        print("*************************************")
        self.print_north_west_corner_dict(north_west_corner_dict, label)
        print("Variable z:", z)

    #regresa un objeto modi con los multiplicadores de fila y columna
    def get_modi_multipliers(self, north_west_corner_dict):
        modi_top_row = []
        modi_top_row.append(0) #En algunos libros se utiliza analogamente el 10 para iniciar el pivoteo
        modi_left_column = []
        previous_row = list(north_west_corner_dict.keys())[0] # se obtiene la fila del primer elemento

        #se calculan los vectores modi
        '''
        NOTA: El metodo de pivoteo se hizo asignandole el cero a la fila superior, por lo que estos resultados difieren con
        aquellos ejemplo que inicial el pivoteo asignandole el cero a columna
        '''

        for element in north_west_corner_dict.items():
            #si el elemento es el primero en su fila el acumulador se agrega a la columna izquierda
            if element[0][0] != previous_row:
                #print("Posicion del Primer Elemento de la fila", element[0])
                modi_left_column.append(element[1].cell_weight - modi_top_row[len(modi_top_row)-1])

                previous_row = element[0][0]

            else:
                #print("Elemento cualquiera", element[0])
                modi_top_row.append(element[1].cell_weight - modi_left_column[len(modi_left_column)-1])

        return {'modi_top_row': modi_top_row, 'modi_left_column': modi_left_column}

    #calcula la tabla z en funcion de un diccionario esquina noroeste y sus multplicadores modi
    def calculate_z_table(self, north_west_corner_dict, modi_top_row, modi_left_column):
        z_table = []
        for i in range(0, len(modi_left_column)):
            z_table.append([])
            for j in range(0, len(modi_top_row)):
                if north_west_corner_dict.get((i, j)) != None:
                    z_table[i].append(north_west_corner_dict.get((i, j)).cell_content)
                else:
                    z_table[i].append(modi_left_column[i] + modi_top_row[j])
        return z_table

    #calcula la tabla c - z la cual se usa para obtener el costo mas pequeño de todas las celdas fuera de ruta
    def calculate_c_minus_z_dict_table(self, costs, z_table):
        c_minus_z_dict_table = {}
        for i in range(0, len(costs)):
            for j in range(0, len(costs[i])):
                c_minus_z_dict_table.update({(i, j): costs[i][j] - z_table[i][j]})
        return c_minus_z_dict_table

    '''
    obtiene el menor elemento de un arreglo de dos dimensiones
    , fue descartado en etapas de desarrollo tempranas
    
    def get_min_value(self, table):
        min_values = []
        for i in range(0, len(table)):
            min_value = min(table[i])
            min_values.append(min_value)

        return min(min_values)
    '''

    #obtiene la menor celda de la tabla
    def get_c_minus_z_dict_table_minor_element(self, c_minus_z_dict_table):
        #diccionario donde se almacenan valores distintos de cero
        modi_data_filtered = {}

        #se obtienen los items de la tabla c - z
        for e in c_minus_z_dict_table.items():
            if e[1] != 0:
                modi_data_filtered.update({e[0]: e[1]})

        #se obtiene el menor de los elementos del diccionario filtrado
        min_value_key = min(modi_data_filtered, key=modi_data_filtered.get)

        return (min_value_key, c_minus_z_dict_table.get(min_value_key))

    #metodo de distribucion modificada modi
    def modi_method(self, north_west_corner_dict, costs):
        #se calculan los multiplicadores del metodo modi en función de la solucion propuesta
        modi_multipliers = self.get_modi_multipliers(north_west_corner_dict)

        #se asigna cada multiplicador a una variable distinta
        modi_top_row = modi_multipliers.get('modi_top_row')
        modi_left_column = modi_multipliers.get('modi_left_column')

        #se calcula la tabla z
        z_table = self.calculate_z_table(north_west_corner_dict, modi_top_row, modi_left_column)

        #se calcula la tabla c - z la cual se usa para obtener el costo mas pequeño de todas las celdas fuera de ruta
        c_minus_z_dict_table = self.calculate_c_minus_z_dict_table(costs, z_table)

        c_minus_z_dict_table_minor_element = self.get_c_minus_z_dict_table_minor_element(c_minus_z_dict_table)

        #se regresa un objeto con todos los datos del metodo Modi
        return {
            'modi_top_row': modi_top_row
            , 'modi_left_column': modi_left_column
            , 'z_table': z_table
            , 'c_minus_z_dict_table': c_minus_z_dict_table
            , 'c_minus_z_dict_table_minor_element' : c_minus_z_dict_table_minor_element
        }

    def print_c_minus_z_dict_table(self, dict_table, modi_top_row, label=""):
        print(label)
        for e in dict_table.items():
            '''
            si la columna es igual a la longitud de la fila superior modi
            imprime el elemento y da un salto de linea
            '''
            if e[0][1] == len(modi_top_row) - 1:
                print(e)
            else:
                print(e, end=' ')
        print("*************************************")

    def print_modi_method_solution(self, modi_data):
        print("Fila Modi:", modi_data['modi_top_row'])
        print("Columna Modi:", modi_data['modi_left_column'])
        self.print_array_table(modi_data['z_table'], "Tabla z")
        self.print_c_minus_z_dict_table(modi_data['c_minus_z_dict_table'], modi_data['modi_top_row'], "Tabla c - z")

    #Obtiene los movimientos validos de una pieza
    '''
        Ejemplo con tres dimensiones

        dimension 3

        f = fila
        c = columna

        f c

        0 0 abajo o derecha

        0 1 abajo o derecha o izquierda

        0 2 abajo o izquierda

        1 0 arriba o abajo o derecha

        1 1 arriba o abajo o derecha o izquierda

        1 2 arriba o abajo o izquierda

        2 0 arriba o derecha

        2 1 arriba o derecha o izquierda

        2 2 arriba o izquierda


        abajo: 00 01 02 10 11 12

        derecha: 00 01 10 11 20 21

        arriba: 10 11 12 20 21 22

        izquierda: 01 02 11 12 21 22


        if f < (dimension-1):
	        movimientos_validos.push(abajo)
        if c < (dimension-1):
	        movimientos_validos.push(derecha)
        if f > 0:
	        movimientos_validos.push(arriba)
        if c > 0:
	        movimientos_validos.push(izquierda)
    '''
    def set_valid_ways(self, full_table):
        for e in full_table.items():
            row = e[0][0]
            column = e[0][1]

            if row < self.row_limit:
                e[1].valid_ways.append(CellDataContainer.PIECE_WAYS.get('DOWN'))
            if row > 0:
                e[1].valid_ways.append(CellDataContainer.PIECE_WAYS.get('UP'))
            if column < self.column_limit:
                e[1].valid_ways.append(CellDataContainer.PIECE_WAYS.get('RIGHT'))
            if column > 0:
                e[1].valid_ways.append(CellDataContainer.PIECE_WAYS.get('LEFT'))

    #permite obtener conocer la direccion o trayectoria de donde se viene
    def get_oposite_way(self, way):
        if way == CellDataContainer.PIECE_WAYS.get('RIGHT'):
            return CellDataContainer.PIECE_WAYS.get('LEFT')
        elif way == CellDataContainer.PIECE_WAYS.get('LEFT'):
            return CellDataContainer.PIECE_WAYS.get('RIGHT')
        elif way == CellDataContainer.PIECE_WAYS.get('UP'):
            return CellDataContainer.PIECE_WAYS.get('DOWN')
        elif way == CellDataContainer.PIECE_WAYS.get('DOWN'):
            return CellDataContainer.PIECE_WAYS.get('UP')

    #metodo recursivo que permite visitar los posibles caminos de una pieza
    def visit_way(self, table, previous_cell_coords, way, path):
        #se obtienen las coordenadas de la celda anterior
        row = previous_cell_coords[0]
        column = previous_cell_coords[1]

        #se recalcula la posicion cartesiana en funcion de la trayectoria del camino
        if way == CellDataContainer.PIECE_WAYS.get('RIGHT'):
            column += 1
        elif way == CellDataContainer.PIECE_WAYS.get('LEFT'):
            column -= 1
        elif way == CellDataContainer.PIECE_WAYS.get('UP'):
            row -= 1
        elif way == CellDataContainer.PIECE_WAYS.get('DOWN'):
            row += 1

        #se obtiene la pieza hijo en funcion de la posicion antes recalculada
        current_cell_coords = (row, column)
        current_cell = copy.deepcopy(table.get(current_cell_coords))

        #Guarda las coordenadas actuales cuando su celda previa es la raiz
        if previous_cell_coords == path[0]:
            Board.aux_path = current_cell_coords

        #Esta linea permite que no se cree un circuito infinito
        if current_cell_coords == Board.aux_path:
            if previous_cell_coords != path[0] and current_cell.cell_content != None:
                return "DONE"

        #condicion que evita visitar casillas inexistentes
        if current_cell != None:
            #si se llega a la celda inicial se cierra el circuito
            if current_cell_coords == path[0]:
                return "DONE"

            if way == 'down' and row < self.row_limit:
                while row < self.row_limit and current_cell.cell_content == None:
                    row += 1
                    current_cell_coords = (row, column)
                    current_cell = copy.deepcopy(table.get(current_cell_coords))

                    #si se llega a la celda inicial se cierra el circuito
                    if current_cell_coords == path[0]:
                        return "DONE"

                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                    #permite que un circuito no se cicle en cualquiera de sus tramos

                    visited_cell = Board.visited_cells.get(current_cell_coords)

                    if visited_cell != None:
                        #current_visited = visited_cell[0]
                        previous_visited = visited_cell[1]

                        if previous_visited != previous_cell_coords:
                            print("The previous is different")

                            return
                    else:
                        #ENHANCENMENT
                        Board.visited_cells.update({current_cell_coords: (current_cell_coords, previous_cell_coords)})

                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                #si la celda tiene contenido se visita
                if current_cell.cell_content != None:
                    result = self.visit_way(table, current_cell_coords, way, path)

                    if result == "DONE":
                        #se agregan las coordenadas a la ruta si se llego a la meta
                        path.append(current_cell_coords)
                        return "DONE"
                else:
                    return "NO WAY"

            if way == 'up' and row > 0:
                while row > 0 and current_cell.cell_content == None:
                    row -= 1
                    current_cell_coords = (row, column)
                    current_cell = copy.deepcopy(table.get(current_cell_coords))

                    #si se llega a la celda inicial se cierra el circuito
                    if current_cell_coords == path[0]:
                        return "DONE"


                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                    #permite que un circuito no se cicle en cualquiera de sus tramos

                    visited_cell = Board.visited_cells.get(current_cell_coords)

                    if visited_cell != None:
                        #current_visited = visited_cell[0]
                        previous_visited = visited_cell[1]

                        if previous_visited != previous_cell_coords:
                            print("The previous is different")

                            return
                    else:
                        #ENHANCENMENT
                        Board.visited_cells.update({current_cell_coords: (current_cell_coords, previous_cell_coords)})

                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                #si la celda tiene contenido se visita
                if current_cell.cell_content != None:
                    result = self.visit_way(table, current_cell_coords, way, path)

                    if result == "DONE":
                        #se agregan las coordenadas a la ruta si se llego a la meta
                        path.append(current_cell_coords)
                        return "DONE"
                else:
                    return "NO WAY"

            if way == 'right' and column < self.column_limit:
                while column < self.column_limit and current_cell.cell_content == None:
                    column += 1
                    current_cell_coords = (row, column)
                    current_cell = copy.deepcopy(table.get(current_cell_coords))

                    #si se llega a la celda inicial se cierra el circuito
                    if current_cell_coords == path[0]:
                        return "DONE"


                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                    #permite que un circuito no se cicle en cualquiera de sus tramos

                    visited_cell = Board.visited_cells.get(current_cell_coords)

                    if visited_cell != None:
                        #current_visited = visited_cell[0]
                        previous_visited = visited_cell[1]

                        if previous_visited != previous_cell_coords:
                            print("The previous is different")

                            return
                    else:
                        #ENHANCENMENT
                        Board.visited_cells.update({current_cell_coords: (current_cell_coords, previous_cell_coords)})

                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                #si la celda tiene contenido se visita
                if current_cell.cell_content != None:
                    result = self.visit_way(table, current_cell_coords, way, path)

                    if result == "DONE":
                        #se agregan las coordenadas a la ruta si se llego a la meta
                        path.append(current_cell_coords)
                        return "DONE"
                else:
                    return "NO WAY"

            if way == 'left' and column > 0:
                while column > 0 and current_cell.cell_content == None:
                    column -= 1
                    current_cell_coords = (row, column)
                    current_cell = copy.deepcopy(table.get(current_cell_coords))

                    #si se llega a la celda inicial se cierra el circuito
                    if current_cell_coords == path[0]:
                        return "DONE"


                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                    #permite que un circuito no se cicle en cualquiera de sus tramos

                    visited_cell = Board.visited_cells.get(current_cell_coords)

                    if visited_cell != None:
                        #current_visited = visited_cell[0]
                        previous_visited = visited_cell[1]

                        if previous_visited != previous_cell_coords:
                            print("The previous is different")

                            return
                    else:
                        #ENHANCENMENT
                        Board.visited_cells.update({current_cell_coords: (current_cell_coords, previous_cell_coords)})

                    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

                #si la celda tiene contenido se visita
                if current_cell.cell_content != None:
                    result = self.visit_way(table, current_cell_coords, way, path)

                    if result == "DONE":
                        #se agregan las coordenadas a la ruta si se llego a la meta
                        path.append(current_cell_coords)
                        return "DONE"
                else:
                    return "NO WAY"

            #si el contenido de la celda es nulo se indica que ya no hay mas camino
            if current_cell.cell_content == None:
                return "NO WAY"


            #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

            #permite que un circuito no se cicle en cualquiera de sus tramos

            visited_cell = Board.visited_cells.get(current_cell_coords)

            if visited_cell != None:
                #current_visited = visited_cell[0]
                previous_visited = visited_cell[1]

                if previous_visited != previous_cell_coords:
                    print("The previous is different")

                    return "DONE"
            else:
                #si la celda no ha sido visitada se agrega al diccionario de celdas visitadas
                Board.visited_cells.update({current_cell_coords: (current_cell_coords, previous_cell_coords)})

            #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

            #se obtienen los caminos validos de la celda
            nxt_valid_ways = current_cell.valid_ways

            #se obtiene el camino previo en funcion de la trayectoria
            previous_way = self.get_oposite_way(way)

            if previous_way in nxt_valid_ways:
                #se elimina el camino previo para no recorrer regresarse
                nxt_valid_ways.remove(previous_way)

            #se visitan los caminos validos
            for way in nxt_valid_ways:

                #se obtiene el resultado de la busqueda del camino
                result = self.visit_way(table, current_cell_coords, way, path)

                if result == "DONE":
                    #se agregan las coordenadas a la ruta si se llego a la meta
                    path.append(current_cell_coords)
                    return "DONE"

            return "ALL POSIBILITIES VISITED"

    #elimina nodos intermedios del circuito
    def clean_circuit(self, cell_data_container):
        i = 0
        while i < len(cell_data_container.path)-1:
            if cell_data_container.path[i][0] == cell_data_container.path[i+1][0]\
                    and cell_data_container.path[i][0] == cell_data_container.path[i - 1][0]:

                cell_data_container.path.pop(i)

                #se resta uno para no saltar ningun elemento
                i -= 1
            i += 1

    #define un circuito en cada pieza vacia
    def set_path_on_cell(self, empty_cells, table):
        #se recorre cada celda vacia
        for cell in empty_cells.items():

            #se obtienen las coordenadas de la celda actual
            current_cell_coords = cell[0]

            #se obtiene el contenedor de datos de la celda actual
            current_cell_data_container = cell[1]

            #se agregan las propias coordenadas a la ruta de la celda
            current_cell_data_container.path.append(current_cell_coords)

            #se obtienen los caminos validos de la celda actual
            valid_ways = current_cell_data_container.valid_ways

            print("*********************")
            print("inicial cell", current_cell_coords)

            #se visitan los caminos validos
            for way in valid_ways:

                Board.aux_path = 0
                Board.visited_cells = {}

                status = self.visit_way(table, current_cell_coords, way, current_cell_data_container.path)
                print("*********************")
                print("status", status)
                print("circuito obtenido:", current_cell_data_container.path)

                #se termina el recorrido una vez que se encuentre un circuito
                if status == "DONE":
                    self.clean_circuit(current_cell_data_container)
                    print("circuito limpiado:", current_cell_data_container.path)
                    break

    '''
    permite establecer si la solucion es la optima, en funcion
    de que ninguna ruta de las celdas vacias sea menor a cero
    '''
    def is_optimum(self, empty_cells, full_table):
        for item in empty_cells.items():
            coords_counter = 0
            path_cost = 0
            for coords in item[1].path:
                cell_data_container = full_table.get(coords)

                if coords_counter == 0:
                    path_cost += cell_data_container.cell_weight
                    coords_counter += 1
                    continue

                if coords_counter % 2 == 0:
                    path_cost += cell_data_container.cell_weight

                if coords_counter % 2 == 1:
                    path_cost -= cell_data_container.cell_weight

                coords_counter += 1

            item[1].path_cost = path_cost

        for item in empty_cells.items():
            if item[1].path_cost < 0:
                return False

        #si ningun costo de la ruta es negativo entonces la solucion es la optima
        return True

    '''
    si el problema esta degenerado es decir si f+c-1 <= n(celdas) [numero de celdas]
            se agrega los valores epsilon en la tabla esquina noroeste
            
            donde poner los valores epsilon?
                se lee cada elemento la configuracion esquina noroeste para determinar si el siguiente elemento
                esta en la misma fila o en la misma columna
                
                si no esta en la misma fila o en la misma columna
                    se inserta un epsilon una columna antes o despues del segundo elemento comparado
                    
                el epsilon se define como ancla y en los siguientes elementos se preguntara
                si cada nuevo elemento esta en la misma fila o en la misma columna, si no estan en la misma fila o en la misma columna
                    se inserta un epsilon una fila antes o despues del elemento comparado
                    
                como se puede observar con cada ancla se turna entre agregar el epsilon una fila anteso despues, o columna anteso despues
                
                ojo: el elemento se agrega antes o despues en funcion de quien esta en una fila mayor
    '''
    def add_epsilon_values(self, north_west_corner_dict, empty_cells, epsilon_required):
        print("cantidad de valores epsilon necesarios para equilibrar:", epsilon_required)

        north_west_corner_list = list(north_west_corner_dict)
        pivot_found = False
        pivot_coords = None
        new_coords = []
        e = 0
        i = 0

        if epsilon_required > 0:
            while i < len(north_west_corner_list) and pivot_found != True:
                #se define como limite una cantidad menor a la longitud del arreglo para no explorar un indice inexistente
                if i < len(north_west_corner_list) - 1:
                    if north_west_corner_list[i][0] == north_west_corner_list[i+1][0]\
                            or north_west_corner_list[i][1] == north_west_corner_list[i+1][1]:
                        #print(north_west_corner_list[i], "es compatible con", north_west_corner_list[i+1])
                        print("*************************************")
                    else:
                        #print(north_west_corner_list[i], "no es compatible con", north_west_corner_list[i+1])

                        pivot_found = True
                        pivot_coords = (north_west_corner_list[i][0] + 1, north_west_corner_list[i][1])
                        new_coords.append(pivot_coords)
                        e += 1
                i += 1
            #print("Coordenadas del pivote", pivot_coords)

        #se crean nuevos elementos a partir del pivote
        while e < epsilon_required or i < len(north_west_corner_list):
            pivot_row = pivot_coords[0]

            if pivot_row != north_west_corner_list[i][0]:
                new_element_coords = (north_west_corner_list[i-1][0], north_west_corner_list[i][1])
                new_coords.append(new_element_coords)
                #print("Nuevas coordenadas", new_element_coords)

            i += 1
            e += 1

        print("Nuevos elementos a crear", new_coords)

        '''
        se intercambian agregan los elementos nuevos al diccionario esquina noroeste
        y se eliminan del diccionario de celdas vacias
        '''
        for coords in new_coords:
            new_element = copy.deepcopy(empty_cells.get(coords))
            new_element.cell_content = 0
            north_west_corner_dict.update({coords: new_element})
            empty_cells.pop((coords))

        #se ordena el diccionario esquina noroeste
        north_west_corner_dict = collections.OrderedDict(sorted(north_west_corner_dict.items()))

        full_table = {}
        #recrear la tabla completa
        for i in range(len(self.costs)):
            for j in range(len(self.costs[i])):
                north_west_corner_el = north_west_corner_dict.get((i,j))
                empty_cells_el = empty_cells.get((i,j))

                if north_west_corner_el != None:
                    full_table.update({(i,j): north_west_corner_el})
                elif empty_cells_el != None:
                    full_table.update({(i,j): empty_cells_el})

        return full_table

    def refresh_data_from_full_table(self, full_table):
        new_north_west_corner_dict = {}
        new_empty_cells = {}
        for cell in full_table.items():
            if cell[1].cell_content != None:
                new_north_west_corner_dict.update({cell[0]: cell[1]})
            else:
                new_empty_cells.update({cell[0]: cell[1]})

        return {
            'new_north_west_corner_dict': new_north_west_corner_dict
            , 'new_empty_cells' : new_empty_cells
        }

    #metodo usado para limpiar la ruta de cada pieza
    def clean_path_on_cell(self, full_table):
        for item in full_table.items():
            item[1].path = []

    def get_min_empty_cell_path_cost(self, empty_cells):
        min_empty_cell_path_cost_pq = []
        heapq.heapify(min_empty_cell_path_cost_pq)

        for item in empty_cells.items():
            path_cost_element = PathCostHeapElement(item[0], item[1].path_cost)
            heapq.heappush(min_empty_cell_path_cost_pq, path_cost_element)

        return heapq.heappop(min_empty_cell_path_cost_pq)

    def modi_first_verification(self, empty_cells, full_table, modi_data):
        c_minus_z_dict_table_minor_element_coords = modi_data['c_minus_z_dict_table_minor_element'][0]
        cell_data_container = empty_cells.get(c_minus_z_dict_table_minor_element_coords)
        cell_data_container_path = cell_data_container.path

        #pila de prioridad usada para obtener la celda con el contenido mas pequeño
        cells_heapq = []
        heapq.heapify(cells_heapq)

        for coords in cell_data_container_path:
            if coords == c_minus_z_dict_table_minor_element_coords:
                #se salta a la celda inicial
                continue
            else:
                heapq.heappush(cells_heapq, full_table.get(coords))

        return {
            'empty_cells_min_cost_coords' : c_minus_z_dict_table_minor_element_coords
            , 'min_content_on_path' : heapq.heappop(cells_heapq).cell_content
        }

    def optimize(self, empty_cells, full_table):
        minor_empty_cell = self.get_min_empty_cell_path_cost(empty_cells)

        print("La celda vacia con menor costo de ruta es: ", minor_empty_cell.coords)

        cell_data_container = empty_cells.get(minor_empty_cell.coords)
        cell_data_container_path = cell_data_container.path

        #pila de prioridad que almacena los nodos negativos de la ruta
        negative_cells = []
        heapq.heapify(negative_cells)

        for i in range(len(cell_data_container_path)):
            current_cell = full_table.get(cell_data_container_path[i])

            if i == 0:
                continue

            #si el indice es impar el elemento de la ruta es negativo
            if i % 2 == 1:
                #print("AGREGAR CELDA")
                heapq.heappush(negative_cells, current_cell)

        #celda negativo con menor contenido
        min_negative_content = heapq.heappop(negative_cells).cell_content

        #se polarizan cada uno de los elementos, asignandole un polo negativo o positivo dependiendo de su posicion
        for i in range(len(cell_data_container_path)):
            current_cell = full_table.get(cell_data_container_path[i])

            #se omite el primer elemento de la ruta
            if i == 0:
                current_cell.cell_content = min_negative_content
                continue

            #si el indice es par
            if i % 2 == 0:
                current_cell.cell_content += min_negative_content

            #si el indice es impar
            elif i % 2 == 1:
                current_cell.cell_content -= min_negative_content

                if current_cell.cell_content == 0:
                    current_cell.cell_content = None

        #se redefine la configuracion y se recalcula z
        new_data = self.refresh_data_from_full_table(full_table)
        configuration = new_data['new_north_west_corner_dict']
        empty_cells = new_data['new_empty_cells']
        z = self.calculate_z(configuration)

        #salida por terminal
        self.print_north_west_corner_solution(configuration, z, "Nueva Tabla Esquina Noroeste")

        #se estima si la solucion se ha degenerado
        if (self.f + self.c - 1) <= len(configuration):
            print("Solucion Equilibrada")
        else:
            print("Solucion Degenerada")

            epsilon_required = (self.f + self.c - 1) - len(configuration)

            #se agregan los valores epsilon para equilibrar la solucion
            full_table = self.add_epsilon_values(configuration, empty_cells, epsilon_required)

        #se limpian las rutas de cada celda (no se requiere redefinir los movimientos validos de cada pieza)
        self.clean_path_on_cell(full_table)

        #se definen las rutas de cada celda
        self.set_path_on_cell(empty_cells, full_table)

        #se determina si la solucion es optima
        is_optimum = self.is_optimum(empty_cells, full_table)

        print("*************************************")
        print("Es la Solucion Optima?", is_optimum)
        print("*************************************")

        if is_optimum == False:
            print("Dado que la solucion inicial no es optima")
            print("*************************************")
            self.optimize(empty_cells, full_table)

#b = Board([15, 25, 5], [5, 15, 15, 10], [[10, 0, 20, 11], [12, 7, 9, 20], [0, 14, 16, 18]]) #prueba 1
#b = Board([70, 90, 115], [50, 60, 70, 95], [[17, 20, 13, 12], [15, 21, 26, 25], [15, 14, 15, 17]]) #prueba 2 +
#b = Board([120, 100, 80], [80, 140, 20], [[12, 14, 16], [14, 13, 19], [17, 15, 18]]) #prueba 3
#b = Board([35, 50, 40], [40, 20, 30, 30], [[8, 6, 10, 9], [9, 12, 13, 7], [14, 9, 16, 5]]) # prueba 4
#b = Board([25, 40, 50], [30, 35, 25], [[600, 700, 700], [320, 300, 350], [500, 480, 450]])#prueba 5 *
#b = Board([7200, 5300], [5500, 3500, 3500], [[12, 7, 10], [8, 11, 9]]) #prueba 6

'''
    References
http://book.pythontips.com/en/latest/map_filter.html: map(), filter(), reduce() en python
https://www.youtube.com/watch?v=RTO8yk6nZY4 : prueba 1
https://invdoperaciones.wordpress.com/metodo-del-cruce-del-arrollo/ : prueba 1 (alterna, tiene un error de calculo en la celda 0,0
https://www.gestiondeoperaciones.net/programacion_lineal/metodo-de-la-esquina-noroeste-algoritmo-de-transporte-en-programacion-lineal/
https://jorgesosasanchez.wordpress.com/unidad-2/2-1-problema-de-transporte-2/2-1-1-metodo-esquina-noroeste/ :
http://gc.initelabs.com/recursos/files/r157r/w13110w/MateNegocios_unidad%205.pdf: el metodo en conjunto se llama esquina noroeste modi
https://invdoperaciones.wordpress.com/metodo-mudi/ : prueba 2
https://www.youtube.com/watch?v=QYgP8pC0XTQ : prueba 2 (alterna)
https://www.youtube.com/watch?v=RsgdKkZRyj0 : prueba 3 (esta es una prueba engañosa, pero sirve para probar el enrutamiento con condiciones similares a la prueba 4)
https://www.youtube.com/watch?v=NvWmaP9FvAQ : prueba 4
https://www.youtube.com/watch?v=AiWlnfQ-Zoc : prueba 5
http://gc.initelabs.com/recursos/files/r157r/w13110w/MateNegocios_unidad%205.pdf : prueba 6
https://stackoverflow.com/questions/3282823/get-the-key-corresponding-to-the-minimum-value-within-a-dictionary : valor minimo de un diccionario
http://srexamen.com/systemofinequations : app para resolver desigualdades (descartado en etapas tempranas)
http://www.estadistica.net/INVESTIGACION/simplex.pdf : mas ejemplos
https://www.youtube.com/watch?v=y8KlKDelpZg : ejemplo metodo cruce de arroyo
https://www.youtube.com/watch?v=kWCwwR4zjEk: ejemplo sin usar
'''


'''
ERROR EN LA RUTA DE LA CELDA 0,4 DESPUES DE Z = 1015

'''
