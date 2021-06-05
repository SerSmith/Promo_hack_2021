import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import datetime


def calculate_schedule(args):
    # # offers = pd.read_csv("data/Lenta hack/20210521_offers.csv")
    # hierarchy = pd.read_csv("data/Lenta hack/20210518_hierarchy.csv")
    # # uplift = pd.read_csv("data/Lenta hack/20210518_uplift.csv")
    # # checks = pd.read_csv("data/Lenta hack/20210518_checks.csv")


    # # Входные данные
    # WEEK_START = 0
    # WEEK_FINISH = datetime.date(2021, 3, 31).isocalendar().week

    # MAX_SIMULT_PROMO = 100
    # MAX_PROMO_FOR_PERIOD = 1

    # # Пути выводы
    # SOLVE_LOG = 'SOLVE_LOG.txt'
    # SOLNFILE = 'SOLNFILE.txt'

    # # Создание сущностей
    # WEEKS = range(WEEK_START, WEEK_FINISH)
    # SKUS = hierarchy['sku'].head(100).unique()

    # # Создание конкретной модели pyomo
    # model = pyo.ConcreteModel()

    # # Переменные
    # model.promo = pyo.Var(SKUS, WEEKS, within=pyo.Binary, initialize=0)

    # #Ограничения

    # # Одновременно не более MAX_SIMULT_PROMO акций
    # def con_max_simult_promo(model, week):
    #     return sum([model.promo[s, week] for s in SKUS]) <= MAX_SIMULT_PROMO

    # model.con_max_simult_promo = pyo.Constraint(WEEKS, rule=con_max_simult_promo)

    # # Одновременно не более MAX_SIMULT_PROMO акций
    # def con_max_promo_period(model, sku):
    #     return sum([model.promo[sku, w] for w in WEEKS]) <= MAX_PROMO_FOR_PERIOD

    # model.con_max_promo_period = pyo.Constraint(SKUS, rule=con_max_promo_period)

    # # Целевая
    # model.OBJ = pyo.Objective(expr=sum(model.promo[s, w] for w in WEEKS for s in SKUS), sense=pyo.maximize)

    # opt = SolverFactory('cbc', executable="/usr/local/bin/cbc")
    # opt.options['ratioGap'] = 0.03
    # opt.options['sec'] = 30

    # instance = model
    # print('started_solving')
    # results = opt.solve(instance, logfile=SOLVE_LOG, solnfile=SOLNFILE)
    
    data = pd.DataFrame({'SKU': ['123213123123', '4534252323', '412341324123'], 'WEEK': [0, 10, 20], 'promo_flag': [1, 1, 1]})
    return data
