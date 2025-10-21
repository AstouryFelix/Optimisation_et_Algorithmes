import json
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path

# ----- Load data from JSON -----
with open("data/lot_sizing_data.json", "r") as f:
    data = json.load(f)

name = data["name"]
H    = int(data["H"])                               # h  : number of periods t
d    = [float(val) for val in data["demand"]]       # dt : Demand in period t 
c    = [float(val) for val in data["var_cost"]]     # ct : Variable production cost (€/unit) 
f    = [float(val) for val in data["setup_cost"]]   # ft : Fixed setup cost (€/setup) 
h    = [float(val) for val in data["hold_cost"]]    # ht : Holding cost (€/unit carried to t+1 ) 
Qmin = float(data["Qmin"])                          # Qmin : Minimum batch size if producing 
Qmax = float(data["Qmax"])                          # Qmax : Maximum production capacity 
I0   = float(data["I0"])                            # I0 : Initial inventory


# Basic validation
assert len(d) == H and len(c) == H and len(f) == H and len(h) == H
assert 0 <= Qmin <= Qmax

# ----- Build model -----
with gp.Env() as env, gp.Model(name, env=env) as model:

    x = model.addVars(H, lb = 0, vtype = GRB.CONTINUOUS, name="x") # xt : Production quantity in period t
    y = model.addVars(H,         vtype = GRB.BINARY    , name="y") # yt : Binary variable indicating whether production occurs in period t
    i = model.addVars(H, lb = 0, vtype = GRB.CONTINUOUS, name="i") # It : End-of-period inventory after meeting demand dt

    model.setObjective(gp.quicksum(c[t]*x[t] + f[t]*y[t] + h[t]*i[t] for t in range(H)))
    
    
    for t in range(H) :
        if t == 0 :
            model.addConstr(I0 + x[0] - d[0] == i[0])
        else : 
            model.addConstr(i[t-1] + x[t] - d[t] == i[t])
        model.addConstr(x[t] <= Qmax * y[t] ) 
        model.addConstr(x[t] >= Qmin * y[t] ) 

    # Optimize
    model.optimize()

    if model.SolCount:
        assert model.ObjVal == 1198.5
        print(f"Total cost = {model.ObjVal:.2f}")
        for t in range(H):
            print(f"t={t:2d}: y={int(y[t].X)} x={x[t].X:.1f} I={i[t].X:.1f}")