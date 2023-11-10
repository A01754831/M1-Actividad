# Importar los módulos necesarios
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa import Agent, Model, time, space, DataCollector
import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd

# Definir la clase para las celdas sucias
class DirtyCell(Agent):
# Constructor
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)

    def step(self):
        pass

# Definir la clase para los agentes limpiadores
class CleanerAgent(Agent):
    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
# Método para el movimiento de los agentes
    def movement(self):
        possible_positions = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,
            include_center=False
        )

        n_position = self.random.choice(possible_positions)
        self.model.grid.move_agent(self, n_position)

# Método para limpiar las celdas sucias
    def clean(self, dirtyCell):
        self.model.grid.remove_agent(dirtyCell)
        self.model.schedule.remove(dirtyCell)
        self.model.nDirtycells -= 1
    
    # Método para verificar si la celda está sucia
    def is_dirty(self,cellmates):
        for cellmate in cellmates:
            if isinstance(cellmate, DirtyCell):
                return cellmate
            
        return None
    
    # Método principal para el comportamiento de los agentes limpiadores en cada paso
    def step(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        
        dirtyCell = self.is_dirty(cellmates)

        if dirtyCell:
            self.clean(dirtyCell)
        else:
            self.movement()
            self.model.totalAgentMovements += 1

# Definir el modelo
class CleanerModel(Model):
    def __init__(self, M, N, nAgents, pCells, timeSteps) -> None:
        self.totalAgentMovements = 0
        self.M = M
        self.N = N
        self.grid = space.MultiGrid(self.M, self.N, True)
        self.nAgents = nAgents
        self.pCells = pCells
        self.pCleanCells = 1 - self.pCells
        self.timeSteps = timeSteps
        self.datacollector = DataCollector(model_reporters={'AgentMovements': 'totalAgentMovements','pCleanCells':'pCleanCells'})

        self.schedule = time.RandomActivation(self)

        self.nDirtycells = int(self.M * self.N * self.pCells)
        self.running = self.nDirtycells > 0

        for i in range(self.nDirtycells):
            dirtyCellPlaced = False

            while not dirtyCellPlaced:
                x = self.random.randrange(self.M)  
                y = self.random.randrange(self.N)  
                if self.grid.is_cell_empty((x, y)):
                    dirtyCellPlaced = True

            cell = DirtyCell(i, self)
            self.schedule.add(cell)
            self.grid.place_agent(cell, (x, y))

        for i in range(self.nAgents):
            agent = CleanerAgent(i+self.nDirtycells, self)
            self.schedule.add(agent)
            self.grid.place_agent(agent, (self.M - 1, self.M - 1))
# Método para un paso en la simulación
    def step(self):
        self.pCleanCells = ((self.N * self.M) - self.nDirtycells) / (self.N * self.M)
        self.running = self.nDirtycells > 0
        self.datacollector.collect(self)
        self.schedule.step()

# Función para definir la apariencia de los agentes en la visualización
def agent_portrayal(agent):
    portrayal = {
        "Filled": "true",
        "Layer": 0,
        "Color": "white",
        "w": 1,
        "h": 1
    }

    if isinstance(agent, DirtyCell):
        portrayal["Shape"] = "circle"  
        portrayal["Color"] = "green"
        portrayal["r"] = 0.7    

    elif isinstance(agent, CleanerAgent):
        portrayal["Shape"] = "rect"  
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1

    return portrayal
# Crear la cuadrícula de visualización
m = 25  # Número de filas
n = 25  # Número de columnas
grid = CanvasGrid(agent_portrayal, m, n, 500, 500)

# Configurar el servidor para la visualización
server = ModularServer(CleanerModel,
                       [grid],
                       "M1. Cleaner Model",
                       {"M": m, "N": n, 
                        "nAgents": 10, "pCells": 0.2, 
                        "timeSteps": 100})
server.port = 8521  # Puerto predeterminado

# Iniciar el servidor de visualización
server.launch()