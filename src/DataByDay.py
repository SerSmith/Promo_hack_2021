import pandas as pd
import os

DATA_PATH = '/home/azureuser/hack/data'
OFFERS_FILE = '20210521_offers.csv'
CHECKS_FILE = '20210518_checks.csv'

def create_data_by_day(checks_df, offers_df):
    
    offers_df

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

    # Оставляем только строчку с ближайшей состоявшейся промоакцией
    data_by_day['days_from_start'] = (data_by_day['day'] - data_by_day['start_date']).dt.days

    future_promo_sku_df = data_by_day.groupby('sku').agg({'days_from_start': 'max'}).reset_index()
    future_promo_sku = future_promo_sku_df.loc[future_promo_sku_df['days_from_start'] <= 0, 'sku'].unique()

    data_by_day = data_by_day[(data_by_day['days_from_start'] >= 0) | (data_by_day['days_from_start'].isna()) | (data_by_day['sku'].isin(future_promo_sku)) ]
    data_by_day = data_by_day.sort_values(by='days_from_start', ascending=False, na_position='last').groupby(['sku', 'day']).head(1)
    
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