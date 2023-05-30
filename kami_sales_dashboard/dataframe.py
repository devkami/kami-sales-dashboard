#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime as dt
from datetime import timedelta as td
from os import getenv, system
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from kami_logging import benchmark_with, logging_with
from numpy import dtype
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from constants import (
    columns_names_head,
    companies,
    float_cols,
    int_cols,
    months_ptbr,
    months_ptbr_abbr,
    sale_nops,
    starting_year,
    str_to_int_cols,
    subsidized_nops,
    template_cols,
    trans_cols,
    trousseau_nops,
)

db_connector_logger = logging.getLogger('db_connector_logger')


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def get_vw_kami_bi_df_from_csv(csv_file) -> pd.DataFrame:
    df = pd.read_csv(csv_file, delimiter=';')
    return df


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def get_vw_kami_bi_df_from_mysql() -> pd.DataFrame:
    load_dotenv()
    connection_url = URL.create(
        'mysql+pymysql',
        username=getenv('DB_USER'),
        password=getenv('DB_USER_PASSWORD'),
        host=getenv('DB_HOST'),
        database='db_uc_kami',
    )
    sqlEngine = create_engine(connection_url, pool_recycle=3600)
    sqlEngine.connect()
    vw_kami_bi = pd.read_sql_query(
        f"select * from vw_kami_bi as vkb where vkb.ano >= {starting_year}", sqlEngine
    )
    return pd.DataFrame(vw_kami_bi)


def clean_number_col(df, number_col):
    if dtype(df[number_col]) not in ['int64', 'float64']:
        return df[number_col].str.extract(pat='(\d+)', expand=False)


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def group_by_orders(df, order_cols) -> pd.DataFrame:
    return df.drop_duplicates(subset=order_cols)


def clean_strtoint_col(df, number_col) -> pd.Series:
    clean_col = df[number_col]
    if dtype(df[number_col]) not in ['int64', 'float64']:
        clean_col = df[number_col].str.extract(pat='(\d+)', expand=False)
    return clean_col


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def convert_number_cols(df) -> pd.DataFrame:
    df[str_to_int_cols] = (
        df[str_to_int_cols]
        .replace(regex=[r'\D+'], value='')
        .apply(pd.to_numeric)
        .fillna(0)
        .astype(int)
    )
    df[int_cols] = df[int_cols].fillna(0).astype(int)
    df[float_cols] = (
        df[float_cols].replace(',', '.', regex=True).fillna(0).astype(float)
    )
    df['cep'] = df['cep'].str.extract(pat='(\d+)', expand=False)
    return df


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def clean_orders_df(orders_df) -> pd.DataFrame:
    return convert_number_cols(orders_df, int_cols, float_cols)


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def build_orders_df(df) -> pd.DataFrame:
    return group_by_orders(convert_number_cols(df), order_cols=['cod_pedido'])


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def filter_orders_by_nops(orders_df, nops) -> pd.DataFrame:
    return orders_df.loc[orders_df.nop.isin(nops)]


def flat_and_tag_motnh_and_year_cols(df, tag='') -> pd.DataFrame:
    tag = f'_{tag}' if tag else tag
    df.columns = df.columns.map(
        lambda x: f'{months_ptbr_abbr.get(x[1])}_{x[0]}{tag}'
    )
    return df


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def calculate_col_by_costumer(orders_df, col, operation) -> pd.DataFrame:
    orders_df = build_orders_df(orders_df)
    return orders_df.pivot_table(
        index=['cod_cliente', 'nome_cliente'],
        columns=['ano', 'mes'],
        values=col,
        aggfunc=operation,
        fill_value=0,
    )


def count_col_by_costumer(orders_df, col) -> pd.DataFrame:
    return calculate_col_by_costumer(orders_df, col, 'count')


def sum_col_by_costumer(orders_df, col) -> pd.DataFrame:
    return calculate_col_by_costumer(orders_df, col, 'sum')


def count_sales_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        count_col_by_costumer(
            filter_orders_by_nops(orders_df, sale_nops), col='cod_pedido'
        ),
        tag='vendas',
    )


def count_sales_by_costumer_and_period(
    orders_df, start_date, end_date, freq
) -> pd.Series:
    count_sales_df = count_sales_by_costumer(orders_df)
    period = pd.period_range(
        start=start_date,
        end=end_date,
        freq=freq,
    )
    period_cols = [
        f'{months_ptbr_abbr[p.month]}_{p.year}_vendas'
        for p in period
        if f'{months_ptbr_abbr[p.month]}_{p.year}_vendas'
        in count_sales_df.columns
    ]
    return count_sales_df[period_cols].sum(axis=1)


def sum_net_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        sum_col_by_costumer(
            orders_df=filter_orders_by_nops(orders_df, sale_nops),
            col='valor_nota',
        ),
        tag='liquido',
    )


def sum_gross_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        sum_col_by_costumer(
            orders_df=filter_orders_by_nops(orders_df, sale_nops),
            col='total_bruto',
        ),
        tag='bruto',
    )


def sum_trousseau_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        sum_col_by_costumer(
            filter_orders_by_nops(orders_df, trousseau_nops), col='valor_nota'
        ),
        tag='enxoval',
    )


def sum_subsidized_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        sum_col_by_costumer(
            filter_orders_by_nops(orders_df, subsidized_nops), col='valor_nota'
        ),
        tag='bonificado',
    )


def sum_discount_by_costumer(orders_df) -> pd.DataFrame:
    return flat_and_tag_motnh_and_year_cols(
        sum_col_by_costumer(
            filter_orders_by_nops(orders_df, sale_nops), 'desconto_pedido'
        ),
        tag='desconto',
    )


def sum_sales_by_costumer_and_period(
    orders_df, start_date, end_date, freq
) -> pd.DataFrame:
    period = pd.period_range(
        start=start_date,
        end=end_date,
        freq=freq,
    )
    period_cols = [
        f'{months_ptbr_abbr[p.month]}_{p.year}_liquido'
        for p in period
        if f'{months_ptbr_abbr[p.month]}_{p.year}_liquido' in orders_df.columns
    ]
    return orders_df[period_cols].sum(axis=1)


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def build_master_df(df) -> pd.DataFrame:
    master_df = pd.DataFrame()
    head_df = group_by_orders(df, order_cols=['cod_cliente'])[
        columns_names_head
    ]
    index_cols = ['cod_cliente']
    trousseau_df = sum_trousseau_by_costumer(df)
    subsidized_df = sum_subsidized_by_costumer(df)
    discount_df = sum_discount_by_costumer(df)
    net_df = sum_net_by_costumer(df)
    gross_df = sum_gross_by_costumer(df)
    amount_sales_df = count_sales_by_costumer(df)
    end_date = f'{dt.now().year}-{dt.now().month - 1}'

    net_df['qtd_total_compras'] = count_sales_by_costumer_and_period(
        df,
        start_date=starting_year,
        end_date=dt.now().strftime('%Y-%m'),
        freq='M',
    )
    start_date = dt.now() - td(days=180)
    net_df['qtd_compras_semestre'] = count_sales_by_costumer_and_period(
        df,
        start_date=start_date.strftime('%Y-%m'),
        end_date=end_date,
        freq='M',
    )
    net_df['total_compras_semestre'] = sum_sales_by_costumer_and_period(
        net_df,
        start_date=start_date.strftime('%Y-%m'),
        end_date=end_date,
        freq='M',
    )
    start_date = dt.now() - td(days=90)
    net_df['total_compras_trimestre'] = sum_sales_by_costumer_and_period(
        net_df,
        start_date=start_date.strftime('%Y-%m'),
        end_date=end_date,
        freq='M',
    )
    start_date = dt.now() - td(days=60)
    net_df['total_compras_bimestre'] = sum_sales_by_costumer_and_period(
        net_df,
        start_date=start_date.strftime('%Y-%m'),
        end_date=end_date,
        freq='M',
    )
    df_list = [
        net_df,
        discount_df,
        gross_df,
        subsidized_df,
        trousseau_df,
        amount_sales_df,
    ]
    dfs = [df for df in df_list if not df.empty]

    if len(dfs) > 0:
        master_kpis_df = pd.concat(dfs, ignore_index=False, axis=1)
        master_df = head_df.merge(
            master_kpis_df.reset_index(), on=index_cols, how='outer'
        )

    return master_df


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def get_template_df(df) -> pd.DataFrame:
    return df[template_cols]


def get_opt_list_from_cols(
    df_template, value_col, label_col, label_sort=True
) -> List[Dict]:
    sort_col = label_col if label_sort else value_col
    option_list = [{'value': 0, 'label': 'Todos'}]
    df_opt = (
        df_template[[label_col, value_col]]
        .drop_duplicates(subset=[value_col])
        .dropna()
        .sort_values(by=[sort_col])
    )
    opt_list = list(zip(*map(df_opt.get, df_opt)))
    option_list.extend(
        [{'value': value, 'label': label} for label, value in opt_list]
    )

    return option_list


def get_opt_list_from_col(df_template, col) -> List[Dict]:
    option_list = [{'value': 0, 'label': 'Todos'}]
    opt_list = (
        df_template[[col]]
        .drop_duplicates(subset=[col])
        .sort_values(by=[col])[col]
        .dropna()
        .unique()
    )
    option_list.extend([{'value': opt, 'label': opt} for opt in opt_list])

    return option_list


def get_month_opt_list(df_template) -> List[Dict]:
    df_template['mes_abbr'] = df_template['mes'].apply(
        lambda x: months_ptbr[x]
    )
    months_list = get_opt_list_from_cols(
        df_template, value_col='mes', label_col='mes_abbr', label_sort=False
    )
    return months_list


def get_year_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_col(df_template, 'ano')


def get_value_by_id(dict_list, key):
    for item in dict_list:
        if item['value'] == key:
            return item['label']
    return None


def get_salesperson_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_cols(
        df_template, value_col='cod_colaborador', label_col='nome_colaborador'
    )


def get_branch_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_col(df_template, 'ramo_atividade')


def get_uf_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_col(df_template, 'uf')


def get_city_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_col(df_template, 'cidade')


def get_district_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_col(df_template, 'bairro')


def get_status_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_cols(
        df_template, value_col='cod_situacao', label_col='desc_situacao'
    )


def get_sub_prod_group_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_cols(
        df_template,
        value_col='cod_grupo_produto',
        label_col='desc_grupo_produto',
    )


def get_prod_group_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_cols(
        df_template, value_col='cod_grupo_pai', label_col='desc_grupo_pai'
    )


def get_prod_band_opt_list(df_template) -> List[Dict]:
    return get_opt_list_from_cols(
        df_template, value_col='cod_marca', label_col='desc_marca'
    )


def get_company_opt_list(df_template) -> List[Dict]:
    df_template['nome_empresa'] = (
        df_template.loc[df_template['empresa_nota_fiscal'] > 0][
            'empresa_nota_fiscal'
        ]
        .dropna()
        .apply(lambda x: companies[x])
    )
    return get_opt_list_from_cols(
        df_template,
        value_col='empresa_nota_fiscal',
        label_col='nome_empresa',
        label_sort=False,
    )


def get_key_from_value(dictionary, value):
    keys = [key for key, val in dictionary.items() if val == value]
    if keys:
        return keys[0]
    return None


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def get_opt_lists_from_df(df, cols) -> Dict:
    opt_lists = {}
    df_template = get_template_df(df)
    all_lists = {
        'month': get_month_opt_list(df_template),
        'year': get_year_opt_list(df_template),
        'salesperson': get_salesperson_opt_list(df_template),
        'branch': get_branch_opt_list(df_template),
        'uf': get_uf_opt_list(df_template),
        'city': get_city_opt_list(df_template),
        'district': get_district_opt_list(df_template),
        'status': get_status_opt_list(df_template),
        'sub_prod_group': get_sub_prod_group_opt_list(df_template),
        'prod_group': get_prod_group_opt_list(df_template),
        'prod_band': get_prod_band_opt_list(df_template),
        'company': get_company_opt_list(df_template),
    }
    for col in cols:
        en_col = get_key_from_value(trans_cols, col)
        if en_col:
            opt_lists[en_col] = all_lists[en_col]
    return opt_lists


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def execute_query(sql_file, db_conn):
    db_connector_logger.info(f'execute {sql_file}')
    system(
        f"mysql -u {db_conn['local_user']} -p{db_conn['local_pass']} < {sql_file}"
    )


@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def get_bi_from_view():
    df = get_vw_kami_bi_df_from_mysql()
    df.to_csv('data/out/kami_bi.csv', sep=";")

@benchmark_with(db_connector_logger)
@logging_with(db_connector_logger)
def main():
    get_bi_from_view()


if __name__ == '__main__':
    main()
