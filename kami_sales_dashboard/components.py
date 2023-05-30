#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, dcc, html
from dash.exceptions import PreventUpdate
from numerize import numerize

from constants import (
    filter_cols,
    sale_nops,
    starting_year,
    trans_cols,
)
from dataframe import (
    get_opt_lists_from_df,
    get_salesperson_opt_list,
    get_value_by_id,
)


def date_picker(id, min_date, max_date, title):
    return html.Div(
        [
            html.Legend(title, style={'font-size': '120%'}),
            dcc.DatePickerRange(
                id=f'date-picker-{id}',
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                start_date=date(starting_year, datetime.now().month, 1),
                end_date=datetime.now(),
            ),
        ]
    )


def single_select(opt_list, id, title):
    return html.Div(
        [
            html.Legend(title, style={'font-size': '120%'}),
            dcc.Dropdown(
                options=opt_list,
                value=opt_list[0].get('value'),
                id=f'select-{id}',
                className='dbc',
                multi=True,
            ),
        ],
        className='my-2',
    )


def single_selects_from_df(df, cols):
    opt_lists = get_opt_lists_from_df(df, cols)
    return [
        single_select(opt_list, id, trans_cols[id])
        for id, opt_list in zip(opt_lists.keys(), opt_lists.values())
    ]


def brands_graph(orders_df):
    df = (
        orders_df.groupby(['cod_marca', 'desc_marca'])['valor_nota']
        .sum()
        .reset_index()
    )

    figure = go.Figure()
    figure.add_trace(
        go.Pie(
            labels=df['desc_marca'],
            values=df['valor_nota'],
            hole=0.3,
            textinfo='none',
        ),
    )

    return figure


def monthly_sales_graph(orders_df):
    orders_df = orders_df.sort_values(
        by=['ano', 'mes'], ascending=[True, True]
    )
    orders_df['ano_mes'] = (
        orders_df['ano'].astype(str) + '/' + orders_df['mes'].astype(str)
    )
    orders_df = orders_df.loc[orders_df['nop'].isin(sale_nops)]
    df = orders_df.groupby(['ano_mes'])['valor_nota'].sum().reset_index()
    figure = go.Figure(
        go.Scatter(
            x=df['ano_mes'], y=df['valor_nota'], mode='lines', fill='tonexty'
        )
    )
    median = round(df['valor_nota'].mean(), 2)
    if not df['ano_mes'].empty:
        figure.add_shape(
            type='line',
            x0=min(df['ano_mes']),
            y0=median,
            x1=max(df['ano_mes']),
            y1=median,
            line_color='red',
            line_dash='dot',
        )
        figure.add_annotation(
            text=f'Média:{numerize.numerize(median)}',
            xref='paper',
            yref='paper',
            font=dict(size=25, color='red'),
            align='center',
            bgcolor='rgba(255,0,0,0.2)',
            x=0.05,
            y=0.75,
            showarrow=False,
        )
    return figure


def top_salesperson_indicator(orders_df):

    sellers_list = get_salesperson_opt_list(orders_df)

    df = orders_df.groupby(['cod_colaborador', 'nome_colaborador'])[
        'valor_nota'
    ].sum()
    df.sort_values(ascending=False, inplace=True)
    df = df.reset_index()
    figure = go.Figure()
    figure.add_trace(
        go.Indicator(
            mode='number+delta',
            title={
                'text': f"<span style='font-size:100%'>{get_value_by_id(sellers_list, df['cod_colaborador'].iloc[0])}</span><br><span style='font-size:70%'>Em vendas em relação a média</span><br>"
            },
            value=df['valor_nota'].iloc[0],
            number={'prefix': 'R$'},
            delta={
                'relative': True,
                'valueformat': '.1%',
                'reference': df['valor_nota'].mean(),
            },
        )
    )
    return figure


def top_brand_indicator(orders_df):
    df = orders_df.groupby(['cod_marca', 'desc_marca'])['valor_nota'].sum()
    df.sort_values(ascending=False, inplace=True)
    df = df.reset_index()
    figure = go.Figure()
    figure.add_trace(
        go.Indicator(
            mode='number+delta',
            title={
                'text': f"<span style='font-size:100%'>{df['desc_marca'].iloc[0]}</span><br><span style='font-size:70%'>Em vendas em relação a média</span><br>"
            },
            value=df['valor_nota'].iloc[0],
            number={'prefix': 'R$'},
            delta={
                'relative': True,
                'valueformat': '.1%',
                'reference': df['valor_nota'].mean(),
            },
        )
    )
    return figure


def average_ticket_indicator(orders_df):
    average_ticket = (
        orders_df['valor_nota'].sum() / orders_df['cod_pedido'].count()
    )
    figure = go.Figure()
    figure.add_trace(
        go.Indicator(
            mode='number',
            title={
                'text': f"<span style='font-size:100%'>Total de Vendas / QTD de Pedidos</span><br><span style='font-size:70%'>Em R$</span><br>"
            },
            value=average_ticket,
            number={'prefix': 'R$'},
        )
    )
    return figure


def daily_sales_graph(orders_df):
    orders_df = orders_df.sort_values(by=['dt_faturamento'], ascending=[True])
    df = (
        orders_df.groupby(['dt_faturamento'])['valor_nota'].sum().reset_index()
    )

    figure = go.Figure(
        go.Scatter(
            x=df['dt_faturamento'],
            y=df['valor_nota'],
            mode='lines',
            fill='tonexty',
        )
    )
    median = round(df['valor_nota'].mean(), 2)
    if not df['dt_faturamento'].empty:
        figure.add_shape(
            type='line',
            x0=min(df['dt_faturamento']),
            y0=median,
            x1=max(df['dt_faturamento']),
            y1=median,
            line_color='red',
            line_dash='dot',
        )
        figure.add_annotation(
            text=f'Média:{numerize.numerize(median)}',
            xref='paper',
            yref='paper',
            font=dict(size=25, color='red'),
            align='center',
            bgcolor='rgba(255,0,0,0.2)',
            x=0.05,
            y=0.75,
            showarrow=False,
        )
    return figure


def get_filters(df):
    return single_selects_from_df(
        df,
        filter_cols,
    )


filters_name = [
    filter_id
    for filter_id, filter_name in zip(trans_cols.keys(), trans_cols.values())
    if filter_name in filter_cols
]


def create_input_filters():
    return [
        Input(f'select-{filter_id}', 'value')
        for filter_id, filter_name in zip(
            trans_cols.keys(), trans_cols.values()
        )
        if filter_name in filter_cols
    ]


def get_filter_mask(df, col, selected_itens):
    return (
        df[col].isin(df[col].unique())
        if not selected_itens or selected_itens == [0]
        else df[col].isin(selected_itens)
    )


def monthly_salesperson_graph(orders_df):
    df = (
        orders_df.groupby(
            ['dt_faturamento', 'cod_colaborador', 'nome_colaborador']
        )['valor_nota']
        .sum()
        .reset_index()
    )
    df_group = (
        orders_df.groupby('dt_faturamento')['valor_nota'].sum().reset_index()
    )

    figure = px.line(
        df, x='dt_faturamento', y='valor_nota', color='nome_colaborador'
    )
    figure.add_trace(
        go.Scatter(
            x=df_group['dt_faturamento'],
            y=df_group['valor_nota'],
            mode='lines+markers',
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.2)',
            name='Total Geral',
        )
    )

    return figure


def top_five_salesperson_graph(orders_df):
    df_salesperson = (
        orders_df.groupby(['cod_colaborador', 'nome_colaborador'])[
            'valor_nota'
        ]
        .sum()
        .head(5)
        .reset_index()
    )
    df_salesperson = df_salesperson
    figure = go.Figure(
        go.Bar(
            x=df_salesperson['nome_colaborador'],
            y=df_salesperson['valor_nota'],
            textposition='auto',
        )
    )
    return figure


def filter_orders_df(orders_df, filters):
    if not filters['start_date'] or not filters['end_date']:
        raise PreventUpdate
    else:
        mask = get_filter_mask(
            orders_df, 'empresa_nota_fiscal', filters['company']
        )
        df_filtered = orders_df.loc[mask]
        mask = get_filter_mask(orders_df, 'ramo_atividade', filters['branch'])
        df_filtered = df_filtered.loc[mask]
        mask = get_filter_mask(orders_df, 'uf', filters['uf'])
        df_filtered = df_filtered.loc[mask]
        mask = get_filter_mask(
            orders_df, 'cod_colaborador', filters['salesperson']
        )
        df_filtered = df_filtered.loc[mask]
        df_filtered = df_filtered.dropna(subset=['dt_faturamento'])
        df_filtered['dt_faturamento'] = pd.to_datetime(
            df_filtered['dt_faturamento'], dayfirst=True
        )
        df_filtered = df_filtered.loc[
            df_filtered['dt_faturamento'].between(
                pd.to_datetime(filters['start_date']),
                pd.to_datetime(filters['end_date']),
            )
        ]
    return df_filtered


def total_sales_indicator(orders_df):
    figure = go.Figure()
    figure.add_trace(
        go.Indicator(
            mode='number',
            title={
                'text': f"<span style='font-size:100%'>Total de Vendas para o Período</span><br><span style='font-size:70%'>Em R$</span><br>"
            },
            value=orders_df['valor_nota'].sum(),
            number={'prefix': 'R$'},
        )
    )
    return figure
