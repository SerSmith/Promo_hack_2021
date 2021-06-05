DATA_PATH = '/home/azureuser/hack/data'
OFFERS_FILE = '20210521_offers.csv'
CHECKS_FILE = '20210518_checks.csv'

def create_data_by_day():
    # загрузка данных
    offers_df = pd.read_csv(os.path.join(DATA_PATH, OFFERS_FILE))
    checks_df = pd.read_csv(os.path.join(DATA_PATH, CHECKS_FILE))
    
    # оставляем только нужные фичи
    checks_df_rejected = checks_df[['day', 'sku', 'supplier_price', 'selling_price', 'num_sales']].copy()
    
    # переводим дату в формат datetime
    for col in ['start_date', 'end_date']:
        offers_df[col] = pd.to_datetime(offers_df[col], format='%Y%m%d')
        
    # считаем продолжительность промоакции
    offers_df.loc[:, 'promo_duration'] = offers_df['end_date'] - offers_df['start_date']
    
    # определяем начало пред-promo периода
    offers_df.loc[:, 'prior_to promo_start'] = offers_df['start_date'] - offers_df['promo_duration']
    
    # делаем аггрегацию данных о продажах sku по дням
    checks_df_rejected_agg = checks_df_rejected.groupby(['day', 'sku']).sum()
    checks_df_rejected_agg = checks_df_rejected_agg.reset_index()
    
    
    # сливаем аггрегированные по чекам с данными офферов
    data_by_day = checks_df_rejected_agg.join(offers_df.set_index('sku'), on='sku')
    data_by_day['day'] = pd.to_datetime(data_by_day['day'], format='%Y%m%d')
    
    # маркируем промо (1) и предпромо (-1) периоды
    promo_condition = (
        (data_by_day['day'] >= data_by_day['start_date'])
        &
        (data_by_day['day'] <= data_by_day['end_date'])
    )

    prior_to_promo_condition = (
        (data_by_day['day'] >= data_by_day['prior_to promo_start'])
        &
        (data_by_day['day'] < data_by_day['start_date'])
    )
    data_by_day.loc[:, 'is_promo'] = 0
    data_by_day.loc[promo_condition, 'is_promo'] = 1
    data_by_day.loc[prior_to_promo_condition, 'is_promo'] = -1
    
    return data_by_day