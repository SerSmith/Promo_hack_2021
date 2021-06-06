import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import datetime
from collections import defaultdict
import os


DATA_PATH = '/home/azureuser/hack/data'
OFFERS_FILE = '20210521_offers.csv'
CHECKS_FILE = '20210518_checks.csv'
HIERARHY_FILE = '20210518_hierarchy.csv'
UPLIFT_FILE = '20210518_uplift.csv'

offers = pd.read_csv(os.path.join(DATA_PATH, OFFERS_FILE))
#     checks_df = pd.read_csv(os.path.join(DATA_PATH, CHECKS_FILE))
hierarchy = pd.read_csv(os.path.join(DATA_PATH, HIERARHY_FILE))
uplift = pd.read_csv(os.path.join(DATA_PATH, UPLIFT_FILE))

type_weights = {"Billboards":  1.520158,
                "Biweekly":  3.404728,
                "Facades":  1.336898,
                "Seasonal":  1.777826}

sku_weights = defaultdict(lambda: 4)

dict_sku = offers.merge(uplift, on='Offer_ID').groupby('sku').agg({'UpLift': 'mean'}).to_dict()['UpLift']

sku_weights.update(dict_sku)

week_from_start_weights = defaultdict(lambda: 1)
week_from_start_weights[1] = 1
week_from_start_weights[2] = 0.8
week_from_start_weights[3] = 0.6
week_from_start_weights[4] = 0.4
week_from_start_weights[5] = 0.2

# Входные данные
WEEK_START = 0
WEEK_FINISH = 13

LOOK_BACK = range(0, 5)



def cartesian_df(dfs):
    out = dfs[0]
    for df in dfs:
        df['key'] = 1
  
    for df in dfs[1:]:
        out = out.merge(df, how='left', on='key')
  
    return out.drop('key', axis=1)

def week_cycle(promo_flag, sku, week, type_, back_step):
    if (week + back_step < WEEK_START) or (week + back_step >= WEEK_FINISH):
        return 0
    else:
        return promo_flag[sku, week + back_step, type_]


def get_candidate_SKU(offers, quant, quantity_new_SKU):
    known_SKUs = offers.loc[offers['train_test_group'] == 'train',  ['sku']].drop_duplicates()

    known_SKUs['weight'] = known_SKUs['sku'].map(sku_weights)
    
    return known_SKUs.sort_values('weight', ascending = False).head(quant)['sku']

def get_optimization_results(model):
    df_start = pd.DataFrame().from_dict(model.promo_start.extract_values(), orient='index', columns=['promo_flag_start']).reset_index()
    df_end = pd.DataFrame().from_dict(model.promo_end.extract_values(), orient='index', columns=['promo_flag_end']).reset_index()
    res = df_start.merge(df_end)
    return res

# def calculate_promo_effect(offers, skus_to_predict):
def calculate_added_money_week_sku_type(model, sku, week, type_):
    return sum([type_weights[type_] * sku_weights[sku] * week_from_start_weights[t] * (week_cycle(model.promo_start, sku, week, type_, -t) - week_cycle(model.promo_end, sku, week, type_, -t)) for t in LOOK_BACK])

# def calculate_added_money_week(model, week):
#     return sum([calculate_added_money_week_sku_type[sku, week, type_] for sku in SKUS for type_ in TYPES])

def is_promo(model, s, w, t):
    return sum([(model.promo_start[s, w_inner, t] - model.promo_end[s, w_inner, t]) for w_inner in range(WEEK_START, w + 1)])



def calculate_schedule(max_simult_promo, max_promo_for_period, quant_billboards):

#     offers = pd.read_csv("data/Lenta hack/20210521_offers.csv")
#     hierarchy = pd.read_csv("data/Lenta hack/20210518_hierarchy.csv")
    # uplift = pd.read_csv("data/Lenta hack/20210518_uplift.csv")
    # checks = pd.read_csv("data/Lenta hack/20210518_checks.csv")


    MAX_SIMULT_PROMO = max_simult_promo
    MAX_PROMO_BY_ONE_SKU = 1
    MAX_PROMO_FOR_PERIOD = max_promo_for_period
    MAX_CONSISTENT_WEEKS = 3

    # Пути выводы
    SOLVE_LOG = 'SOLVE_LOG.txt'
    SOLNFILE = 'SOLNFILE.txt'

    # Создание сущностей
    WEEKS = range(WEEK_START, WEEK_FINISH)
    # SKUS = get_candidate_SKU(offers, 50, 10)
    SKUS = get_candidate_SKU(offers, 50, 10)
    TYPES = offers['Promo_type'].unique()

    

    # Создание конкретной модели pyomo
    model = pyo.ConcreteModel()

    # Переменные
    model.promo_start = pyo.Var(SKUS, WEEKS, TYPES, within=pyo.Binary, initialize=0)
    model.promo_end = pyo.Var(SKUS, WEEKS, TYPES, within=pyo.Binary, initialize=0)

    # Дополнительные сущности

    # Ограничения

    # Нельзя закончить промоакцию до ее начала
    def con_is_promo_left(model, sku, week, type_):
        return is_promo(model, sku, week, type_) >= 0

    model.con_is_promo_left = pyo.Constraint(SKUS, WEEKS, TYPES, rule=con_is_promo_left)

    def con_is_promo_right(model, sku, week, type_):
        return is_promo(model, sku, week, type_) <= 1
    model.con_is_promo_right = pyo.Constraint(SKUS, WEEKS, TYPES, rule=con_is_promo_right)
    print(MAX_SIMULT_PROMO)
    # Одновременно не более MAX_SIMULT_PROMO акций
    def con_max_simult_promo(model, week):
        return sum([is_promo(model, s, week, t) for s in SKUS for t in TYPES]) <= MAX_SIMULT_PROMO

    model.con_max_simult_promo = pyo.Constraint(WEEKS, rule=con_max_simult_promo)

    # За период может быть не больше определенного числа акций
    def con_max_promo_period(model, sku):
        return sum([model.promo_start[sku, w, t] for w in WEEKS for t in TYPES]) <= MAX_PROMO_FOR_PERIOD

    model.con_max_promo_period = pyo.Constraint(SKUS, rule=con_max_promo_period)

    # Ограничение на количество билбордов
    def con_max_billbords(model, week):
        t = 'Billboards'
        return sum([is_promo(model, s, week, t) for s in SKUS]) <= quant_billboards

    # Все что началось должно закончится
    def con_starts_eq_ends(model, s, t):
        return sum([model.promo_start[s, week, t] for week in WEEKS]) == sum([model.promo_end[s, week, t] for week in WEEKS])

    model.con_starts_eq_ends = pyo.Constraint(SKUS, TYPES, rule=con_starts_eq_ends)

    # Нельзя одновременно начать и закончить
    def con_cant_start_and_end_symul(model, s, w, t):
        return model.promo_start[s, w, t] <= 1 - model.promo_end[s, w, t]

    model.con_cant_start_and_end_symul = pyo.Constraint(SKUS, WEEKS, TYPES, rule=con_cant_start_and_end_symul)

    # Продолжительность промо не быолее MAX_CONSISTENT_WEEKS месяцев подряд
    def con_consistency(model, s, w, t):
        return model.promo_start[s, w, t] - sum([week_cycle(model.promo_end, s, w, t, forward_step) for forward_step in range(1, MAX_CONSISTENT_WEEKS )]) <= 0
    model.con_consistency = pyo.Constraint(SKUS, WEEKS, TYPES, rule=con_consistency)       

    # Продолжительность промо не быолее MAX_CONSISTENT_WEEKS месяцев подряд
    def con_max_promo_by_one_sku(model, s, w):
        return sum([is_promo(model, s, w, t) for t in TYPES]) <= MAX_PROMO_BY_ONE_SKU
    model.con_max_promo_by_one_sku = pyo.Constraint(SKUS, WEEKS, rule=con_max_promo_by_one_sku)       



    # Целевая
    model.OBJ = pyo.Objective(expr=sum(calculate_added_money_week_sku_type(model, s, w, t)  for w in WEEKS for s in SKUS for t in TYPES), sense=pyo.maximize)

    opt = SolverFactory('cbc', executable="/usr/bin/cbc")
    opt.options['ratioGap'] = 0.1
    opt.options['sec'] = 30

    instance = model
    print('started_solving')
    opt_log = opt.solve(instance, logfile=SOLVE_LOG, solnfile=SOLNFILE)

    schedule = get_optimization_results(model)
# schedule, opt_log
    return model,  opt_log, schedule

# model, opt_log, schedule = calculate_schedule(300, 2, 23)
# # schedule, opt_log = calculate_schedule(300, 2, 23)
# print('finished')
# print(sum(model.promo_end.extract_values().values()))
# print(sum(model.promo_start.extract_values().values()))