#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from statsmodels.stats.proportion import proportion_confint

# ### Single Lab Tests Per Month

data_grouped = data.groupby(['Month', 'Lab', 'Result Type'])['MRN'].nunique().reset_index()

table = pd.pivot_table(data_grouped, values='MRN', index=['Month', 'Lab'], columns=['Result Type'], fill_value=0).reset_index()
table['total'] = table['abnormal'] + table['normal']
table['share'] = (table['abnormal'] / table['total'])


#https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html
# Statistical Science 16:101-133 suggests that Wilson or Jeffreys methods for small n and Agresti-Coull, Wilson, or Jeffreys, for larger n.
ci_low, ci_upp = proportion_confint(table['abnormal'], table['total'], alpha=0.05, method='wilson')
table['lower ci'] = ci_low
table['upper ci'] = ci_upp


# ### Single Lab Test Pre and Post Covid

table_summary = table.copy()

def get_period(row):
    if row['Month'] < '2020-04':
        return 'pre-covid'
    elif row['Month'] < '2020-06':
        return 'covid'
    else:
        return 'post-covid'

table_summary['period'] = table_summary.apply(get_period, axis = 1)

table_summary = table_summary.groupby(['Lab', 'period']).agg({'abnormal':'mean', 'total':'mean'}).reset_index()

table_summary['abnormal'] = table_summary['abnormal'].round(2)
table_summary['total'] = table_summary['total'].round(2)

table_summary = pd.pivot_table(table_summary, values=['abnormal', 'total'], index=['Lab'], columns=['period'], fill_value=0).reset_index()
table_summary.columns = ['%s%s' % (a, ': %s' % b if b else '') for a, b in table_summary.columns]

table_summary['pre-covid ratio'] = (table_summary['abnormal: pre-covid'] / table_summary['total: pre-covid']).round(2)

table_summary['covid ratio'] = (table_summary['abnormal: covid'] / table_summary['total: covid']).round(2)

table_summary['post-covid ratio'] = (table_summary['abnormal: post-covid'] / table_summary['total: post-covid']).round(2)

# ### Create Figure For a Single Test

lab_test = 'Platelet'

table = pd.read_excel('table_1_single_tests_by_month_v2.xlsx')

figdf = table[table['Lab'] == lab_test].sort_values('Month').reset_index(drop = True)

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Bar(x=figdf['Month'], y=figdf['abnormal'], name="Number of Patients with Abnormal Result", marker=dict(color="#add8e6")),
    secondary_y=False, row=1, col=1
)

fig.add_trace( 
    go.Scatter(x=figdf['Month'], y=figdf['share'], name="Share of Patients with Abnormal Result", line=dict(color="#000000", width=3)),
    secondary_y=True, row=1, col=1 
)

# Add figure title
fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    title_text= lab_test,
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

# Set y-axes titles
fig.update_yaxes(title_text="<b>Number</b> of Patients with Abnormal Result", secondary_y=False)
fig.update_yaxes(title_text="<b>Share</b> of Patients with Abnormal Result", secondary_y=True)
fig.update_yaxes(tickformat="%", secondary_y=True)

fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.3,
    xanchor="center",
    x=0.2
))

fig.show()
