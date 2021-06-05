import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import datetime
from collections import defaultdict
from collections import defaultdict
 

type_weights = defaultdict(lambda: 1)
sku_weights = defaultdict(lambda: 1)
week_from_start_weights = defaultdict(lambda: 1)



# Входные данные
WEEK_START = 0
WEEK_FINISH = datetime.date(2021, 3, 31).isocalendar().week

LOOK_BACK = range(0, 5)

def week_cycle(model, sku, week, type_, back_step):
    if (week + back_step < WEEK_START) or (week + back_step > WEEK_FINISH):
        return 0
    else:
        return model.promo[sku, week + back_step, type_]

def func_calcualte_new_sku_uplift(sku):
    return pd.Series(1, index=sku.index)


def get_candidate_SKU(hierarchy, offers, quantity_new_SKU):
    known_SKUs = offers['sku'].drop_duplicates()
    # func_calcualte_new__uplift
    print(known_SKUs.shape)
    return known_SKUs


# def calculate_promo_effect(offers, skus_to_predict):
def calculate_added_money_week_sku_type(model, sku, week, type_):
    return sum([type_weights[type_] * sku_weights[sku] * week_from_start_weights[t] * week_cycle(model, sku, week, type_, -t) for t in LOOK_BACK])

# def calculate_added_money_week(model, week):
#     return sum([calculate_added_money_week_sku_type[sku, week, type_] for sku in SKUS for type_ in TYPES])

def get_optimization_results(model):
    df_decision = pd.DataFrame().from_dict(model.promo.extract_values(), orient='index', columns=['promo_flag']).reset_index()
    df_decision['SKU'], df_decision['WEEK'], df_decision['type'] = zip(*df_decision['index'])
    out = df_decision[['SKU', 'WEEK', 'promo_flag']]
    return out

def calculate_schedule(args):
    offers = pd.read_csv("data/Lenta hack/20210521_offers.csv")
    hierarchy = pd.read_csv("data/Lenta hack/20210518_hierarchy.csv")
    # uplift = pd.read_csv("data/Lenta hack/20210518_uplift.csv")
    # checks = pd.read_csv("data/Lenta hack/20210518_checks.csv")


    MAX_SIMULT_PROMO = 100
    MAX_PROMO_FOR_PERIOD = 1
    MAX_CONSISTENT_WEEKS_PROMO = 3

    # Пути выводы
    SOLVE_LOG = 'SOLVE_LOG.txt'
    SOLNFILE = 'SOLNFILE.txt'

    # Создание сущностей
    WEEKS = range(WEEK_START, WEEK_FINISH)
    SKUS = get_candidate_SKU(hierarchy, offers, 10)
    TYPES = offers['Promo_type'].unique()

    # Создание конкретной модели pyomo
    model = pyo.ConcreteModel()

    # Переменные
    model.promo = pyo.Var(SKUS, WEEKS, TYPES, within=pyo.Binary, initialize=0)

    # Дополнительные сущности

    def calculate_week_from_start(model, sku, week, type_):
        if week == WEEK_START:
            return 0
        else:
            return model.promo[sku , week-1, type]

    #Ограничения

    # Одновременно не более MAX_SIMULT_PROMO акций
    def con_max_simult_promo(model, week):
        return sum([model.promo[s, week, t] for s in SKUS for t in TYPES]) <= MAX_SIMULT_PROMO

    model.con_max_simult_promo = pyo.Constraint(WEEKS, rule=con_max_simult_promo)

    # # Одновременно не более MAX_SIMULT_PROMO акций
    # def con_max_promo_period(model, sku):
    #     return sum([model.promo[sku, w, t] for w in WEEKS for t in TYPES]) <= MAX_PROMO_FOR_PERIOD


    model.con_max_promo_period = pyo.Constraint(SKUS, rule=con_max_promo_period)

    # Целевая
    model.OBJ = pyo.Objective(expr=sum(calculate_added_money_week_sku_type(model, s, w, t)  for w in WEEKS for s in SKUS for t in TYPES), sense=pyo.maximize)

    opt = SolverFactory('cbc', executable="/usr/local/bin/cbc")
    opt.options['ratioGap'] = 0.03
    opt.options['sec'] = 30

    instance = model
    print('started_solving')
    opt_log = opt.solve(instance, logfile=SOLVE_LOG, solnfile=SOLNFILE)

    schedule = get_optimization_results(model)

    return schedule, opt_log

schedule, opt_log = calculate_schedule(None)

print(opt_log)