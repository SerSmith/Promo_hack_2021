from datetime import datetime, timedelta
from random import choice

import pandas as pd
import numpy as np 
import streamlit as st

import plotly.figure_factory as ff
import plotly.graph_objects as go


from optimazer import calculate_schedule


def convert(xx, second_parameter):
    """Функция для пробразования датафрейма для диаграммы Гантта
    """
    df = xx.copy()
    df[["sku", "week", "promo_type"]] = df.apply(lambda x: x["index"], axis=1, result_type="expand")
    df.drop(columns=["index"], inplace=True)
    df = df.sort_values(by=["sku", "promo_type", "week"]) 
    df.to_csv("test_sku.csv")
    def get_start_end(x):
        ind = np.where(x == 1)[0]
        if len(ind) % 2 == 1:
            raise ValueError
            exit
        return [(ind[2*i] // 2, (ind[2*i+1] // 2) + 1) for i in range(len(ind) // 2)]
    

    final_dict = {}
    for sku, sku_group in df.groupby("sku"):
        final_dict[sku] = {}
        for promo_type, sku_group_promo in sku_group.groupby("promo_type"):
            flags = sku_group_promo[["promo_flag_start", "promo_flag_end"]].to_numpy().flatten()
            final_dict[sku][promo_type] = get_start_end(flags)
    after_proc = pd.DataFrame(columns={"sku", "format_type", "start", "end"})

    for sku in final_dict:
        for promo_type in final_dict[sku]:
            if len(final_dict[sku][promo_type]):
                for start, end in final_dict[sku][promo_type]:
                    ser = {
                        "sku": sku,
                        "format_type": promo_type,
                        "start": start,
                        "end": end
                    }
                    after_proc = after_proc.append(ser, ignore_index=True)

    df = after_proc
    df.to_csv("test_sku_v.csv", index=False)
    init_date = datetime.strptime("2020-01-01","%Y-%m-%d")
    df["Start"] = df["start"].apply(lambda x: init_date + timedelta(days=7*x))
    df["Finish"] = df["end"].apply(lambda x: init_date + timedelta(days=7*(x+1)))
    df = df \
        .rename(columns={"sku": "Task"}) \
        .drop(columns=["start", "end"])
    task_list = df.Task.unique().tolist()[:int(second_parameter)]
    return df.query("Task in @task_list")

def plot_profit(color):
    date = [
        '2020-01-01', '2020-01-07', '2020-01-14', '2020-01-28',
        '2020-02-01', '2020-02-07', '2020-02-14', '2020-02-28',
        '2020-03-07', '2020-03-07', '2020-03-14', '2020-03-28',
    ]

    money = [
        33, 50, 49, 70,
        66, 88, 75, 100,
        49, 80, 110, 130 
    ]

    fig = go.Figure(data=go.Scatter(x=date, y=money, line=dict(color=color)))

    fig.update_layout(
        title=dict(
            text="Дополнительная выручка",
            font=dict(size=24)
        ),
        width=1000,
        height=500
    )

    st.plotly_chart(fig)

#@st.cache(suppress_st_warning=True)
def gantt_chart(first_parameter, second_parameter):
    _, _, df = calculate_schedule(first_parameter, 1, 23)
    df = convert(df, second_parameter)

    fig = ff.create_gantt(
        df, 
        group_tasks=True, 
        colors={
            "Billboards": "#003c96", 
            'Facades' : "#FFB900",
            'Biweekly' : "#FF0000",
            'Seasonal': "#00FF00" 
        }, 
        index_col="format_type"
    )

    fig.update_layout(
        title=dict(
            text="Календарь промо",
            font=dict(size=24)
        ),
        width=1000,
        height=500
    )

    fig.update_xaxes(
        range=[df["Start"].min()-timedelta(days=3), df["Finish"].max()+timedelta(days=3)]
    )

    st.plotly_chart(fig)

def main():
    st.set_page_config(
        page_title="Lenta dashboard",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Title
    st.title('Основные метрики')

    # Filters
    st.sidebar.markdown('# Настройка параметров')
    st.sidebar.header('Модель 1')
    first_parameter_model_1 = st.sidebar.number_input("Количество одновременных промо: ", value=9, key="f1m1")
    second_parameter_model_1 = st.sidebar.number_input("Количество sku на графике: ", value=7, key="f2m1")
    button_1 = st.sidebar.button("Запуск модели 1") 
    st.sidebar.header('Модель 2')
    first_parameter_model_2 = st.sidebar.number_input("Количество одновременных промо: ", value=9, key="f1m2")
    second_parameter_model_2 = st.sidebar.number_input("Количество sku на графике: ", value=7, key="f2m2")
    button_2 = st.sidebar.button("Запуск модели 2")
    #if st.sidebar.button("Запуск"):

    st.write(f"""
        <br>
        <div style="font-size:19px">
        <table>
            <tr>
                <td> </td>
                <td> <b>Модель 1</b> </td>
                <td> <b>Модель 2</b> </td>
            </tr>
            <tr>
                <td> <b>Метрика 1</b> </td>
                <td> <i>{(first_parameter_model_1 + second_parameter_model_1) ** 2:.4f}</i> </td>
                <td> <i>{(first_parameter_model_2 + second_parameter_model_2) ** 2:.4f}</i> </td>
            </tr>
            <tr>
                <td> <b>Метрика 2</b> </td>
                <td> <i>{(first_parameter_model_1 - second_parameter_model_1) ** 2:.4f}</i> </td>
                <td> <i>{(first_parameter_model_2 - second_parameter_model_2) ** 2:.4f}</i> </td>
            </tr>
            <tr>
                <td> <b>Метрика 3</b> </td>
                <td> <i>{(first_parameter_model_1 * second_parameter_model_1) ** 2:.4f}</i> </td>
                <td> <i>{(first_parameter_model_2 * second_parameter_model_2) ** 2:.4f}</i> </td>
            </tr>
        </table>
        </div>
        <br>    
        """,
        unsafe_allow_html=True
    )

    st.header("Модель 1")
    st.write("""
    <style>
        .box {
            float: left;
            height: 20px;
            width: 20px;
            border: 1px solid black;
            clear: both;
        }

        .Billboards {
            background-color: #003c96;
        }

        .Facades {
            background-color: #FFB900;
        }

        .Biweekly {
            background-color: #FF0000;
        }
        .Seasonal {
            background-color: #00FF00;
        }

    </style>\
    <p class='box Billboards'><p/><p>Billboards</p>
    <br>
    <div><div class='box Facades'></div> Facades</div>
    <br>
    <div><div class='box Biweekly'></div> Biweekly</div>
    <br>
    <div><div class='box Seasonal'></div> Seasonal</div>
    """, unsafe_allow_html=True)
    gantt_chart(first_parameter_model_1, second_parameter_model_1)
    plot_profit("#003c96")
    st.header("Модель 2")
    gantt_chart(first_parameter_model_2, second_parameter_model_2)
    plot_profit("#FFB900")

if __name__ == "__main__":
    main()