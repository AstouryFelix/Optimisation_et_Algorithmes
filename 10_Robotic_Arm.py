import math
import gurobipy as gp
from gurobipy import GRB, nlfunc as nl
import matplotlib.pyplot as plt

# ============================= Explications ============================= #
# A planar robot arm with two revolute joints has link lengths L1 and L2. 
# The base is fixed at the origin. Joint angles are θ1 (shoulder) and θ2 (elbow, relative to link 1). 
# The end-effector position (x,y) is:
# x = L1 * cos(Theta1) + L2 * cos(Theta1 + Theta2)
# y = L1 * sin(Theta1) + L2 * sin(Theta1 + Theta2)

# We want the end-effector to reach a target point (x∗,y∗) while respecting joint limits and avoiding
# a circular obstacle (e.g., a post) of radius r centered at (xo,yo).
# We approximate collision avoidance by keeping the midpoint of the first link outside the obstacle.

# ============================= Fonctions ============================= #
def draw_arm(ax, L1, L2, th1, th2, xo, yo, r, x_star, y_star, title):
    x1 = L1*math.cos(th1); y1 = L1*math.sin(th1)
    x2 = x1 + L2*math.cos(th1 + th2); y2 = y1 + L2*math.sin(th1 + th2)

    ax.plot([0, x1], [0, y1], linewidth=3)
    ax.plot([x1, x2], [y1, y2], linewidth=3)
    ax.scatter([0, x1, x2], [0, y1, y2], s=40)

    # obstacle
    t = [i*2*math.pi/300 for i in range(301)]
    cx = [xo + r*math.cos(tt) for tt in t]
    cy = [yo + r*math.sin(tt) for tt in t]
    ax.plot(cx, cy, linewidth=2)

    # target
    ax.scatter([x_star], [y_star], marker='x', s=80)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-0.5, L1+L2+0.2)
    ax.set_ylim(-0.5, L1+L2+0.2)
    ax.grid(True, linestyle=':')
    ax.set_title(title)

def show_results():
    sol = None

    if m.Status == GRB.OPTIMAL:
        sol = {
            "theta1": theta1.X, "theta2": theta2.X,
            "x": x.X, "y": y.X, "xm": x.X, "ym": y.X,
            "obj": m.ObjVal,
        }
        print("Optimal objective:", m.ObjVal)
        print(sol)
    else:
        print("Optimization status:", m.Status)
    if sol is not None:
        fig, ax = plt.subplots(figsize=(6,6))
        draw_arm(ax, L1, L2, sol['theta1'], sol['theta2'], xo, yo, r, x_star, y_star,
                title=f"Robot Arm (nlfunc)\nobj={sol['obj']:.4g}")
        # Save as PNG instead of showing
        plt.savefig("images/robot-arm.png", dpi=100, bbox_inches="tight")
        plt.close(fig)
    else:
        print("No solution available to plot yet.")

# ============================= Parameters ============================= #
L1, L2 = 1.0, 0.8             # Lengths of the links
x_star, y_star = 1.20, 0.60   # Point to reach
xo, yo, r = 0.50, 0.00, 0.20  # Disk to avoid


# ============================= Joint limits ============================= #
theta1_min, theta1_max = -math.pi, math.pi
theta2_min, theta2_max = -0.75*math.pi, 0.75*math.pi


# ============================= Build model ============================= #
with gp.Env() as env, gp.Model(env=env) as m:

    # Decision variables (angles)
    theta1 = m.addVar(lb=theta1_min, ub=theta1_max, name="theta1"                )
    theta2 = m.addVar(lb=theta2_min, ub=theta2_max, name="theta2"                )
    x      = m.addVar(lb=0,                         name="x"                     )
    y      = m.addVar(lb=0,                         name="y"                     )
    mx     = m.addVar(lb=0,                         name="mx"                    )
    my     = m.addVar(lb=0,                         name="my"                    )
    R      = m.addVar(lb=r,                         name="R"                     )
    dist   = m.addVar(lb=0,                         name="distance from (x0, y0)")

    m.setObjective(dist, GRB.MINIMIZE)

    m.addConstr( x    == L1*nl.cos(theta1) + L2*nl.cos(theta1 + theta2),                        name = "position of x"                              )
    m.addConstr( y    == L1*nl.sin(theta1) + L2*nl.sin(theta1 + theta2),                        name = "position of y"                              )
    m.addConstr( mx   == L1*nl.cos(theta1)/2,                                                   name = "x positionn of the middle of the arm"       )
    m.addConstr( my   == L1*nl.sin(theta1)/2,                                                   name = "x positionn of the middle of the arm"       )
    m.addConstr( dist == nl.sqrt( (x - x_star) * (x - x_star) + (y - y_star) * (y - y_star) ),  name = "Minimize the distance to objective position")
    m.addConstr( R    == nl.sqrt( (mx - xo) * (mx - xo) + (my - yo) * (my - yo) ),              name = "x and y outside of the cone"                )

    m.optimize()
    show_results()




