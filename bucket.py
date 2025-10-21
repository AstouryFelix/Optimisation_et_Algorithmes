import math
import gurobipy as gp
from gurobipy import GRB , nlfunc


with gp.Env() as env, gp.Model(name="portfolio", env=env) as model:
    """
    Variables
        bottom radius r ≥ 0
        top radius    R ≥ 0
        height        h ≥ 0

    Objectif :
        Maximise the volume of the bucket
        Has the top smaller than the botton

    Bottom disk have a volume of : V = πh(R2+Rr+r2)/3

    Bottom area:
        A_bot=πr2.
    Lateral area:
        A_lat=π(R+r)*√[(R−r)2+h2]
    Material constraint:
        A_bot+A_lat=1.
    """
    r = model.addVar(lb = 0, ub = 1, vtype = GRB.CONTINUOUS, name="r") 
    R = model.addVar(lb = 0, ub = 1, vtype = GRB.CONTINUOUS, name="R") 
    h = model.addVar(lb = 0, ub = 1, vtype = GRB.CONTINUOUS, name="h")

    # V = math.pi * h * (R**2 + R*r + r**2) / 3
    # model.setObjective(V, GRB.MAXIMIZE)
    
    # A_bot = math.pi * R**2
    # A_lat = math.pi * (R + r) * nlfunc.sqrt((R - r)**2 + h**2)
    # model.addConstr(A_bot + A_lat == 1)

    # ============== Avec la correction ============== #
    V = model.addVar(lb = 0,         vtype = GRB.CONTINUOUS, name="V") 
    S = model.addVar(lb = 1, ub = 1, vtype = GRB.CONTINUOUS, name="S")

    model.setObjective(V, GRB.MAXIMIZE)

    model.addConstr( math.pi * h * (R**2 + R*r + r**2) / 3 == V )
    A_bot = math.pi * R**2
    A_lat = math.pi * (R + r) * nlfunc.sqrt((R - r)**2 + h**2)
    model.addConstr( A_bot + A_lat == S)

    model.optimize()

    if model.status == GRB.OPTIMAL :
        total_value = model.ObjVal
        print("===================================")
        print(f"Optimal value \t= {total_value:.2f}")
        print(f"Rayon du haut \t= {R.X:.2f}") 
        print(f"Rayon du bas \t = {r.X:.2f}")
        print(f"Hauteur \t = {h.X:.2f}") 
        print("===================================")


