import numpy as np
import gurobipy as gp
from gurobipy import GRB
from gurobipy import tupledict

def generate_knapsack(num_items):
    # Fix seed value
    rng = np.random.default_rng(seed=0)
    # Item values, weights
    values = rng.uniform(low=1, high=25, size=num_items)
    weights = rng.uniform(low=5, high=100, size=num_items)
    # Knapsack capacity
    capacity = 0.7 * weights.sum()

    return values, weights, capacity


def solve_knapsack_model(values, weights, capacity):
    num_items = len(values)
    # Turn values and weights numpy arrays to dict
    # ...

    index, values, weights = gp.multidict({i : (values[i] , weights[i]) for i in range(num_items)})

    with gp.Env() as env, gp.Model(name="knapsack", env=env) as model:
        x = model.addVars(index, vtype = GRB.BINARY, name="x") 

        model.setObjective(x.prod(values), GRB.MAXIMIZE)
        
        model.addConstr(x.prod(weights) <= capacity, name="capacity")

        model.optimize()
        if model.status == GRB.OPTIMAL:
            chosen = [i for i in index if x[i].X > 0.5]
            total_value = model.ObjVal
            total_weight = sum(weights[i] for i in chosen)
            print(f"Optimal value = {total_value:.2f}")
            print(f"Total weight  = {total_weight:.2f} / Capacity {capacity:.2f}")
            print(f"Items chosen (first 10): {chosen[:10]}")

data = generate_knapsack(10000)
solve_knapsack_model(*data)