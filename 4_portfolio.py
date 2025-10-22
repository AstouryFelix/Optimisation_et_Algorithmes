import json
import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB

with open("data/portfolio-example.json", "r") as f:
    data = json.load(f)

n = data["num_assets"]
sigma = np.array(data["covariance"])
mu = np.array(data["expected_return"])
mu_0 = data["target_return"]
k = data["portfolio_max_size"]


with gp.Env() as env, gp.Model(name="portfolio", env=env) as model:
    # Name the modeling objects to retrieve them
    # ...
    x = model.addVars(n, ub = 1, lb = 0, vtype = GRB.CONTINUOUS, name="x") 
    y = model.addVars(n,                 vtype = GRB.BINARY    , name="y") 
    risk = gp.quicksum(x[i] * sigma[i,j] * x[j] for i in range(n) for j in range(n))

    model.setObjective(risk)

    expected_return = gp.quicksum(x[i] * mu[i] for i in range(n)) 
    model.addConstr(expected_return >= mu_0                          ,name="return")
    model.addConstr(x.sum()                                     == 1 ,name="fraction")
    model.addConstr(y.sum()                                     <= k ,name="number")
    model.addConstrs((x[i] <= y[i] for i in range(n))                ,name="is_used")

    model.optimize()

    # Write the solution into a DataFrame
    portfolio = [var.X for var in model.getVars() if "x" in var.VarName]
    risk = model.ObjVal
    expected_return = model.getRow(model.getConstrByName("return")).getValue()
    df = pd.DataFrame(
        data=portfolio + [risk, expected_return],
        index=[f"asset_{i}" for i in range(n)] + ["risk", "return"],
        columns=["Portfolio"],
    )
    print(df)