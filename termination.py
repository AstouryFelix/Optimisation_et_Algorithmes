import gurobipy as gp
from gurobipy import GRB
from functools import partial
import time

class CallbackData:
    def __init__(self):
        self.last_gap_change_time = -GRB.INFINITY
        self.last_gap = GRB.INFINITY


def callback(model, where, *, cbdata):

    # Récuperer le temps et la valeur du premier résultat
    if where != GRB.Callback.MIP:
        return
    
    if model.cbGet(GRB.Callback.MIP_SOLCNT) == 0:
        return

    time  = model.cbGet(GRB.Callback.RUNTIME)    # Elapsed solver runtime (seconds).
    best  = model.cbGet(GRB.Callback.MIP_OBJBST) # Current best objective.
    bound = model.cbGet(GRB.Callback.MIP_OBJBND) # Current best objective bound.
    gap   = (bound - best) / best
    if gap < cbdata.last_gap - epsilon_to_compare_gap :
        print("Meilleur résultat significatif de trouvé : ")
        print(f"gap = {gap} %,\t temps = {time} seconds")
        cbdata.last_gap_change_time = time
        cbdata.last_gap = gap
        return
    
    if time - cbdata.last_gap_change_time > max_time_between_gap_updates :
        model.terminate()
    # Use model.terminate() to end the search when required...
    # ...


with gp.Env() as env, gp.read("data/mkp.mps.bz2") as model:
    # Global variables used in the callback function
    max_time_between_gap_updates = 15
    epsilon_to_compare_gap = 1e-4

    # Initialize data passed to the callback function
    callback_data = CallbackData()
    print("\n===============================================")
    print(f"max_time_between_gap_updates       : {max_time_between_gap_updates}")
    print(f"epsilon_to_compare_gap             : {epsilon_to_compare_gap}")
    print(f"callback_data.last_gap             : {callback_data.last_gap}")
    print(f"callback_data.last_gap_change_time : {callback_data.last_gap_change_time}")
    print("=============================================\n")

    callback_func = partial(callback, cbdata=callback_data)

    model.optimize(callback_func)