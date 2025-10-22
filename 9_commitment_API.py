import gurobipy as gp
from gurobipy import GRB

# 24 Hour Load Forecast (MW)
load_forecast = [
     4,  4,  4,  4,  4,  4,   6,   6,
    12, 12, 12, 12, 12,  4,   4,   4,
     4, 16, 16, 16, 16,  6.5, 6.5, 6.5,
]

# solar energy forecast (MW)
solar_forecast = [
    0,   0,   0,   0,   0,   0,   0.5, 1.0,
    1.5, 2.0, 2.5, 3.5, 3.5, 2.5, 2.0, 1.5,
    1.0, 0.5, 0,   0,   0,   0,   0,   0,
]

# global number of time intervals
nTimeIntervals = len(load_forecast)

# thermal units
thermal_units = ["gen1", "gen2", "gen3"]

# thermal units' costs  (a + b*p + c*p^2), (startup and shutdown costs)
thermal_units_cost, a, b, c, sup_cost, sdn_cost = gp.multidict(
    {
        "gen1": [5.0, 0.5, 1.0, 2, 1],
        "gen2": [5.0, 0.5, 0.5, 2, 1],
        "gen3": [5.0, 3.0, 2.0, 2, 1],
    }
)

# thernal units operating limits
thermal_units_limits, pmin, pmax = gp.multidict(
    {"gen1": [1.5, 5.0], "gen2": [2.5, 10.0], "gen3": [1.0, 3.0]}
)

# thermal units dynamic data (initial commitment status)
thermal_units_dyn_data, init_status = gp.multidict(
    {"gen1": [0], "gen2": [0], "gen3": [0]}
)

# i = len(thermal_units)
# t = nTimeIntervals
pi_max = pmax       # Maximum Power for unit i (MW)
pi_min = pmin       # Minimum Power for unit i (MW)
αi = a              # Fixed Cost for unit i ($/h)
βi = b              # Linear Cost for unit i ($/MWh)
γi = c              # Quadratic Cost for unit i ($/MWh/MWh)
δi = sup_cost       # Start Up Cost for unit i ($)
ζi = sdn_cost       # Shutdown Cost for unit i ($)
Lt = load_forecast  # Load Forecast at time interval t (MW)
St = solar_forecast # Solar Energy Forecast at time interval t (MW)


def show_results():
    obj_val_s = model.ObjVal
    print(f" OverAll Cost = {round(obj_val_s, 2)}	")
    print("\n")
    print("%5s" % "time", end=" ")
    for t in range(nTimeIntervals):
        print("%4s" % t, end=" ")
    print("\n")

    # for g in thermal_units:
    for g in range(len(thermal_units)) :
        print("%5s" % g, end=" ")
        for t in range(nTimeIntervals):
            print("%4.1f" % thermal_units_out_power[(thermal_units[g], t)].X, end=" ")
        print("\n")

    print("%5s" % "Solar", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % solar_forecast[t], end=" ")
    print("\n")

    print("%5s" % "Load", end=" ")
    for t in range(nTimeIntervals):
        print("%4.1f" % load_forecast[t], end=" ")
    print("\n")


with gp.Env() as env, gp.Model(env=env) as model:

    # add variables for thermal units (power and statuses for commitment, startup and shutdown)

    # Output power for unit i at time interval t (MW )                                   pit
    thermal_units_out_power = model.addMVar(
        (thermal_units, nTimeIntervals), 
        vtype = GRB.CONTINUOUS,
        lb = 0,
        name="thermal_units_out_power"
    )

    # Startup Status for thermal unit i at time interval t (1: Start Up, 0: Otherwise)    vit
    thermal_units_startup_status = model.addMVar(
        (thermal_units, nTimeIntervals),
        vtype = GRB.BINARY,
        name="thermal_unit_startup_status",
    ) 

    # Shutdown Status for thermal unit i at time interval t (1: Shutdown, 0: Otherwise)   wit
    thermal_units_shutdown_status = model.addMVar(
        (thermal_units, nTimeIntervals),
        vtype = GRB.BINARY,
        name="thermal_unit_shutdown_status",
    ) 

    # Commitment Status for thermal unit i at time interval t (1: Online, 0: Otherwise))  uit
    thermal_units_comm_status = model.addMVar(
        (thermal_units, nTimeIntervals),
        vtype = GRB.BINARY,
        name="thermal_unit_comm_status"
    ) 

    # define objective function as an empty quadratic construct and add terms
    obj_fun_expr = gp.QuadExpr(0)
    for t in range(nTimeIntervals):
        for g in thermal_units:
            obj_fun_expr.add(γi[g] * thermal_units_out_power[(g,t)]**2   +
                             βi[g] * thermal_units_out_power[(g,t)]      +
                             αi[g] * thermal_units_comm_status[(g,t)]    +  
                             δi[g] * thermal_units_startup_status[(g,t)] +
                             ζi[g] * thermal_units_shutdown_status[(g,t)]) 
    model.setObjective(obj_fun_expr)

    # Power balance equations
    for t in range(nTimeIntervals):
        model.addConstr(
            gp.quicksum(thermal_units_out_power[(g,t)] for g in thermal_units) == Lt[t] - St[t] ,
            name="power_balance_" + str(t),
        )

    # Thermal units physical constraints, using indicator constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            model.addGenConstrIndicator(
                thermal_units_comm_status[(g, t)],  # binary indicator variable
                1,                                  # when status = 1
                thermal_units_out_power[(g, t)],    # left-hand side
                GRB.GREATER_EQUAL,                  # sense
                pi_min[g],                          # right-hand side
                name=f"min_power_{g}_{t}"
                # thermal_units_comm_status[(g,t)] * pi_min[g] <= thermal_units_out_power[(g,t)]
            )
            model.addGenConstrIndicator(
                thermal_units_comm_status[(g, t)],  # binary indicator variable
                1,                                  # when status = 1
                thermal_units_out_power[(g, t)],    # left-hand side
                GRB.LESS_EQUAL,                     # sense
                pi_max[g],                          # right-hand side
                name=f"max_power_{g}_{t}"
                # thermal_units_out_power[(g,t)] <= thermal_units_comm_status[(g,t)] * pi_max[g]
            )
            model.addGenConstrIndicator(
                thermal_units_comm_status[(g, t)],  # binary indicator variable
                0,                                  # when status = 1
                thermal_units_out_power[(g, t)],    # left-hand side
                GRB.EQUAL,                          # sense
                0,                                  # right-hand side
                name=f"max_power_{g}_{t}"
                # thermal_units_comm_status[(g,t)] * pi_min[g] <= thermal_units_comm_status[(g,t)] * pi_max[g]
            )

    # Thermal units logical constraints
    for t in range(nTimeIntervals):
        for g in thermal_units:
            if t == 0:
                model.addConstr(
                    thermal_units_comm_status[(g,t)] - init_status[g] == thermal_units_startup_status[(g,t)] - thermal_units_shutdown_status[(g,t)],
                    name="logical1_" + g + "_" + str(t),
                )
            else:
                model.addConstr(
                    thermal_units_comm_status[(g,t)] - thermal_units_comm_status[(g,t-1)] == thermal_units_startup_status[(g,t)] - thermal_units_shutdown_status[(g,t)],
                    name="logical1_" + g + "_" + str(t),
                )

            model.addConstr(
                thermal_units_startup_status[(g,t)] + thermal_units_shutdown_status[(g,t)] <= 1,
                name="logical2_" + g + "_" + str(t),
            )

    model.optimize()
    show_results()