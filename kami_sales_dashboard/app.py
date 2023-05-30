#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime

import dash
import dash_bootstrap_components as dbc
import pkg_resources
from dash import Input, Output, State, dcc, html
from dash_bootstrap_templates import ThemeSwitchAIO

from components import (
    average_ticket_indicator,
    brands_graph,
    daily_sales_graph,
    date_picker,
    filter_orders_df,
    get_filters,
    monthly_sales_graph,
    monthly_salesperson_graph,
    top_five_salesperson_graph,
    top_salesperson_indicator,
    total_sales_indicator,
)
from constants import current_day, current_month, current_year, sale_nops
from dataframe import get_vw_kami_bi_df_from_csv, build_orders_df

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app_version = pkg_resources.get_distribution('my-package-name').version
app_logger = logging.getLogger('kami-sales-dashboard')
app_logger.info('Get BI from database')
products_df = get_vw_kami_bi_df_from_csv('kami_sales_dashboard/data/out/kami_bi.csv')
orders_df = build_orders_df(products_df)
sales_orders_df = orders_df.loc[orders_df['nop'].isin(sale_nops)]

# Style ->
config_graph = {'displayModeBar': True, 'showTips': True}
config_indicator = {'displayModeBar': False, 'showTips': False}
tab_card = {'height': '100%'}
main_config = {
    'hovermode': 'x unified',
    'legend': {
        'yanchor': 'top',
        'y': 0.9,
        'xanchor': 'left',
        'x': 0.1,
        'title': {'text': None},
        'font': {'color': 'white'},
        'bgcolor': 'rgba(0,0,0,0.5)',
    },
    'margin': {'l': 10, 'r': 10, 't': 10, 'b': 10},
}
template_ligth = 'spacelab'
template_dark = 'slate'
url_theme1 = dbc.themes.SPACELAB
url_theme2 = dbc.themes.SLATE

# Layout ->

menu_head = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col([html.Legend('KAMI CO')], sm=8),
                        dbc.Col(
                            [
                                html.I(
                                    className='fa fa-chart-line',
                                    style={'font-size': '250%'},
                                )
                            ],
                            sm=4,
                            align='center',
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                ThemeSwitchAIO(
                                    aio_id='theme',
                                    themes=[url_theme1, url_theme2],
                                ),
                                html.Legend('Sales Analytics'),
                            ]
                        )
                    ],
                    style={'margin-top': '5px'},
                ),
            ]
        )
    ]
)

sidebar = html.Div(
    [
        dbc.Button(
            html.I(className='fa fa-bars', style={'font-size': '150%'}),
            id='open-sidebar',
            n_clicks=0,
        ),
        dbc.Offcanvas(
            [
                menu_head,
                html.Hr(),
                html.Center(
                    html.Legend(
                        'Filtros',
                        style={'font-size': '150%', 'align': 'center'},
                    )
                ),
                date_picker(
                    'geral',
                    date(min(products_df['ano'].unique()), 1, 1),
                    date(current_year, current_month, current_day),
                    'Período',
                ),
            ]
            + get_filters(products_df)
            + [
                html.Hr(),
                html.Center(
                    [
                        dbc.Row(
                            [
                                dbc.Button(
                                    'Intranet',
                                    href='https://intranet.kamico.com.br/',
                                    target='_blank',
                                ),
                            ],
                            style={'margin-top': '5px'},
                        ),
                    ]
                ),
            ],
            id='sidebar',
            is_open=False,
        ),
    ],
    className='my-3',
)

first_row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.Center('Vendas Diárias')),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='graph1',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=12,
                )
            ],
            className='g-2 my-auto',
            style={'margin-top': '7px'},
        )
    ]
)

second_row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.Center('Vendas Mensais')),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='graph2',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=7,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Center('Participação por Marca')
                                ),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='graph3',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=5,
                ),
            ],
            className='g-2 my-auto',
            style={'margin-top': '7px'},
        )
    ]
)

third_row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Center('Vendas Mensais Por Vendedor')
                                ),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='graph4',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=7,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Center('Ranking de Vendas')
                                ),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='graph5',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=5,
                ),
            ],
            className='g-2 my-auto',
            style={'margin-top': '7px'},
        )
    ]
)

forth_row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.Center('Líder de Vendas')),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='kpi1',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=4,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.Center('Ticket Médio')),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='kpi2',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=4,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.Center('Total de Vendas')),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(
                                            id='kpi3',
                                            className='dbc',
                                            config=config_graph,
                                        )
                                    ]
                                ),
                            ],
                            style=tab_card,
                        )
                    ],
                    sm=12,
                    lg=4,
                ),
            ],
            className='g-2 my-auto',
            style={'margin-top': '7px'},
        )
    ]
)

footer_row = html.Footer(
    [
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.A(
                                            html.I(className='fa fa-question'),
                                            href='https://intranet.kamico.com.br/abrirchamado',
                                            target='_blank',
                                        )
                                    ],
                                    width='auto',
                                ),
                                dbc.Col(
                                    [
                                        html.A(
                                            html.I(className='fa fa-phone'),
                                            href='https://wha.me/5511916654692',
                                            target='_blank',
                                        )
                                    ],
                                    width='auto',
                                ),
                                dbc.Col(
                                    [
                                        html.A(
                                            html.I(className='fa fa-envelope'),
                                            href='mailto:dev@kamico.com.br?subject=Ajuda Com Dashboard',
                                            target='_blank',
                                        )
                                    ],
                                    width='auto',
                                ),
                            ],
                            justify='start',
                        )
                    ],
                    sm=12,
                    md=4,
                    lg=4,
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.P(
                                            [
                                                f"version: {app_version} - ",
                                                f'@ {datetime.now().year} Copyright: ',
                                                html.A(
                                                    'KAMI CO.',
                                                    href='https://intranet.kamico.com.br',
                                                    target='_blank',
                                                ),
                                                'IT Team. - developed by',
                                                html.A(
                                                    '@maicondmenezes',
                                                    href='https://github.com/maicondmenezes',
                                                    target='_blank',
                                                ),
                                            ]
                                        )
                                    ],
                                    width='auto',
                                ),
                            ],
                            justify='end',
                        ),
                    ],
                    sm=12,
                    md=4,
                    lg=8,
                ),
            ],
            className='g-2 my-auto',
            style={'margin-top': '7px'},
        ),
    ]
)
app.layout = dbc.Container(
    [sidebar, first_row, second_row, third_row, forth_row, footer_row],
    fluid=True,
    style={'height': '100vh'},
)


@app.callback(
    Output('sidebar', 'is_open'),
    Input('open-sidebar', 'n_clicks'),
    [State('sidebar', 'is_open')],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    Output('graph1', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def graph1(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = daily_sales_graph(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('graph2', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def graph2(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = monthly_sales_graph(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('graph3', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def graph3(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = brands_graph(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('graph4', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def graph4(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = monthly_salesperson_graph(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('graph5', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def graph5(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = top_five_salesperson_graph(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('kpi1', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def kpi1(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = top_salesperson_indicator(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('kpi2', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def kpi2(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = average_ticket_indicator(df_filtered)
    figure.update_layout(template=template)

    return figure


@app.callback(
    Output('kpi3', 'figure'),
    Input('select-salesperson', 'value'),
    Input('select-uf', 'value'),
    Input('select-branch', 'value'),
    Input('select-company', 'value'),
    Input('date-picker-geral', 'start_date'),
    Input('date-picker-geral', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch('theme'), 'value'),
)
def kpi3(salesperson, uf, branch, company, start_date, end_date, toggle):
    filters = {
        'salesperson': salesperson,
        'uf': uf,
        'branch': branch,
        'company': company,
        'start_date': start_date,
        'end_date': end_date,
    }
    df_filtered = filter_orders_df(sales_orders_df, filters)
    template = template_ligth if toggle else template_dark
    figure = total_sales_indicator(df_filtered)
    figure.update_layout(template=template)

    return figure


if __name__ == '__main__':
    app.run_server(debug=True, port=8005)
