#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from statsmodels.stats.proportion import proportion_confint
from itertools import combinations

# remove patients for which we do not have any covid info
data = data[data['MRN'].isin(pcr['MRN'])]
data['COVIDFound'] = data['MRN'].isin(positive['MRN'])

lab_names = data['Lab'].unique()
l1 = list(combinations(lab_names, 1))
l2 = list(combinations(lab_names, 2))
l3 = list(combinations(lab_names, 3))
l4 = list(combinations(lab_names, 4))
l5 = list(combinations(lab_names, 5))
patterns = l1 + l2 + l3 + l4 + l5

df = data[data['Lab'].isin(lab_names)]
ct = pd.crosstab(df['MRN'], df['Lab'])
cp = ct[(ct.T != 0).all()].reset_index()['MRN']
vc = data[data['MRN'].isin(cp)].reset_index()

appended_data = []
for lab_names in tqdm(patterns):
    df = data[data['Lab'].isin(lab_names)]
    ct = pd.crosstab(df['MRN'], df['Lab'])
    cp = ct[(ct.T != 0).all()].reset_index()['MRN']
    vc = data[data['MRN'].isin(cp)].reset_index()
    appended_data.append(
        {
            'Combo': ', '.join(lab_names),
            'Size of Double Tested Population': len(vc['MRN'].unique()),
            'COVID Negative Patients Tested for Combo': len(vc[vc['COVIDFound'] == False]['MRN'].unique()),
            'COVID Positive Patients Tested for Combo': len(vc[vc['COVIDFound'] == True]['MRN'].unique()),
        })
combinations_total = pd.DataFrame(appended_data).reset_index(drop = True)


abnormal = data[data['Result Type'] == 'abnormal']

df = abnormal[abnormal['Lab'].isin(lab_names)]
ct = pd.crosstab(df['MRN'], df['Lab'])
cp = ct[(ct.T != 0).all()].reset_index()['MRN']
vc = abnormal[abnormal['MRN'].isin(cp)].reset_index()

appended_data = []
abnormal = data[data['Result Type'] == 'abnormal']
for lab_names in tqdm(patterns):
    df = abnormal[abnormal['Lab'].isin(lab_names)]
    ct = pd.crosstab(df['MRN'], df['Lab'])
    cp = ct[(ct.T != 0).all()].reset_index()['MRN']
    vc = abnormal[abnormal['MRN'].isin(cp)].reset_index()
    appended_data.append(
        {
            'Combo': ', '.join(lab_names),
            'Size of Abnormal Double Tested Population': len(vc['MRN'].unique()),
            'COVID Negative Patients Abnormal for Combo': len(vc[vc['COVIDFound'] == False]['MRN'].unique()),
            'COVID Positive Patients Abnormal for Combo': len(vc[vc['COVIDFound'] == True]['MRN'].unique()),
        })
combinations_abnormal = pd.DataFrame(appended_data).reset_index(drop = True)

combinations = combinations_total.merge(combinations_abnormal, on = 'Combo', how = 'left')

combinations['Combo Size'] = combinations['Combo'].str.count(',').apply(lambda x: x + 1)

combinations['Within double-tested population, of all people who had abnormal for all blood tessts in Combo, how many also had COVID positive'] = (combinations['COVID Positive Patients Abnormal for Combo'] / (combinations['COVID Positive Patients Abnormal for Combo'] + combinations['COVID Negative Patients Abnormal for Combo'])).round(2)

combinations['Within double-tested population, of all people who had Covid Positive, how many had abnormal for all blood tessts in Combo positive'] = (combinations['COVID Positive Patients Abnormal for Combo'] / (combinations['COVID Positive Patients Tested for Combo'])).round(2)

denom = (combinations['COVID Positive Patients Abnormal for Combo'] + combinations['COVID Negative Patients Abnormal for Combo'])

#https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html
# Statistical Science 16:101-133 suggests that Wilson or Jeffreys methods for small n and Agresti-Coull, Wilson, or Jeffreys, for larger n.
ci_low, ci_upp = proportion_confint(combinations['COVID Positive Patients Abnormal for Combo'], denom, alpha=0.05, method='wilson')
combinations['Lower CI 1'] = ci_low.round(2)
combinations['Upper CI 1'] = ci_upp.round(2)

#https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html
# Statistical Science 16:101-133 suggests that Wilson or Jeffreys methods for small n and Agresti-Coull, Wilson, or Jeffreys, for larger n.
ci_low, ci_upp = proportion_confint(combinations['COVID Positive Patients Abnormal for Combo'], combinations['COVID Positive Patients Tested for Combo'], alpha=0.05, method='wilson')
combinations['Lower CI 2'] = ci_low.round(2)
combinations['Upper CI 2'] = ci_upp.round(2)

cols = ['Combo',
        'Combo Size',
        'Size of Double Tested Population',
        'Size of Abnormal Double Tested Population',
        'COVID Negative Patients Tested for Combo', 
        'COVID Positive Patients Tested for Combo', 
        'COVID Negative Patients Abnormal for Combo', 
        'COVID Positive Patients Abnormal for Combo', 
        'Within double-tested population, of all people who had abnormal for all blood tessts in Combo, how many also had COVID positive', 
        'Lower CI 1', 'Upper CI 1', 
        'Within double-tested population, of all people who had Covid Positive, how many had abnormal for all blood tessts in Combo positive', 
        'Lower CI 2', 'Upper CI 2'
       ]

combinations = combinations[cols]
