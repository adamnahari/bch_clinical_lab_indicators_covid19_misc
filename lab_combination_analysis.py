#!/usr/bin/env python
# coding: utf-8

import pandas as pd


# ### Combinations Pre and Post Covid

def get_period(row):
    if row['Month'] < '2020-04':
        return 'pre-covid'
    elif row['Month'] < '2020-06':
        return 'covid'
    else:
        return 'post-covid'

combinations_summary['Period'] = combinations_summary.apply(get_period, axis = 1)

combinations_summary = combinations_summary.groupby(['Combo', 'Period']).agg({'Patients with Abnormal Combo':'mean', 'Patients Tested for Combo':'mean'}).reset_index()

combinations_summary = pd.pivot_table(combinations_summary, values=['Patients with Abnormal Combo', 'Patients Tested for Combo'], index=['Combo'], columns=['Period'], fill_value=0).reset_index()
combinations_summary.columns = ['%s%s' % (a, ': %s' % b if b else '') for a, b in combinations_summary.columns]

combinations_summary['Combo Size'] = combinations_summary['Combo'].str.count(',').apply(lambda x: x + 1)

cols = ['Combo', 'Combo Size', 'Patients Tested for Combo: pre-covid', 'Patients Tested for Combo: covid', 'Patients Tested for Combo: post-covid', 'Patients with Abnormal Combo: pre-covid', 'Patients with Abnormal Combo: covid', 'Patients with Abnormal Combo: post-covid']
combinations_summary = combinations_summary[cols]

combinations_summary['Pre-covid Ratio'] = (combinations_summary['Patients with Abnormal Combo: pre-covid'] / combinations_summary['Patients Tested for Combo: pre-covid']).round(2)
combinations_summary['Covid Ratio'] = (combinations_summary['Patients with Abnormal Combo: covid'] / combinations_summary['Patients Tested for Combo: covid']).round(2)
combinations_summary['Post-covid Ratio'] = (combinations_summary['Patients with Abnormal Combo: post-covid'] / combinations_summary['Patients Tested for Combo: post-covid']).round(2)

# ### Manual Exploration of All Combinations

def combinations_per_month(data):
    
    combos = []
    
    for month, month_df in tqdm(data.groupby(data['Month'])):
        
        month_df = month_df.reset_index(drop=True)
        
        eos = month_df[month_df['Lab Test'] == 'Absolute Eosinophil Count Automated']
        lym = month_df[(month_df['Lab Test'] == 'Absolute Lymphocyte Count')]
        alb = month_df[month_df['Lab Test'] == 'Albumin']
        bas = month_df[month_df['Lab Test'] == 'Basophil Automated']
        esr = month_df[month_df['Lab Test'] == 'ESR (Erythrocyte Sedimentation Rate)']
        hmt = month_df[month_df['Lab Test'] == 'Hematocrit']
        hem = month_df[month_df['Lab Test'] == 'Hemoglobin']
        mon = month_df[month_df['Lab Test'] == 'Monocyte Automated']
        neu = month_df[month_df['Lab Test'] == 'Neutrophil Automated']
        plt = month_df[month_df['Lab Test'] == 'Platelet']
        rbc = month_df[month_df['Lab Test'] == 'RBC']
        wbc = month_df[month_df['Lab Test'] == 'WBC']
        alt = month_df[month_df['Lab Test'] == 'ALT']
        ast = month_df[month_df['Lab Test'] == 'AST (Aspartate Aminotransferase)']
        bilid = month_df[month_df['Lab Test'] == 'Bilirubin, Direct']
        bilit = month_df[month_df['Lab Test'] == 'Bilirubin, Total']
        bun = month_df[month_df['Lab Test'] == 'BUN']
        cre = month_df[month_df['Lab Test'] == 'Creatinine']
        crp = month_df[month_df['Lab Test'] == 'C-Reactive Protein']
        ggtp = month_df[month_df['Lab Test'] == 'GGTP (Gamma Glutamyl Transpeptidase)']
        fer = month_df[month_df['Lab Test'] == 'Ferritin']
        inr = month_df[month_df['Lab Test'] == 'INR']
        fib = month_df[month_df['Lab Test'] == 'Fibrinogen']
        ddm = month_df[month_df['Lab Test'] == 'D-Dimer']
        ldh = month_df[month_df['Lab Test'] == 'LDH (Lactate Dehydrogenase)']
        trpt = month_df[month_df['Lab Test'] == 'Troponin T']
        bnp = month_df[month_df['Lab Test'] == 'B-Type Natriuretic Peptide']
        il10 = month_df[month_df['Lab Test'] == 'IL10']
        il2 = month_df[month_df['Lab Test'] == 'IL2']
        il2r = month_df[month_df['Lab Test'] == 'IL2 Receptor']
        il4 = month_df[month_df['Lab Test'] == 'IL4']
        il6 = month_df[month_df['Lab Test'] == 'IL6']
        il8 = month_df[month_df['Lab Test'] == 'IL8']
        tnf = month_df[month_df['Lab Test'] == 'TNF']
        pct = month_df[month_df['Lab Test'] == 'PCT']
        trpi = month_df[month_df['Lab Test'] == 'Troponin-I']
        
        test_df = (eos, lym, alb, bas, esr, hmt, hem, mon, neu, plt, rbc, wbc, alt, ast, bilid, bilit, bun, cre, crp, ggtp, fer, inr, fib, ddm, ldh, trpt, bnp, il10, il2, il2r, il4, il6, il8, tnf, pct, trpi)
                
        # For each posible number of combinations
        for num_combo in range(1, len(test_df) + 1):
            
            # For a combination with this many elements, on this month
            for index, c in enumerate(combinations(test_df, num_combo)):

                # Populate first element of lists
                pt_tested = set(c[0]['MRN'])
                c0_abnoraml = c[0][c[0]['Result Type'] == 'abnormal']
                pt_tested_abnormal = set(c0_abnoraml['MRN'])
                test_lst = []

                # Add to lists
                for i in range(num_combo):
                    pt_tested = pt_tested & set(c[i]['MRN'])
                    pt_tested_abnormal = pt_tested_abnormal & set(c[i][c[i]['Result Type'] == 'abnormal']['MRN'])
                    test_lst = test_lst + list(c[i]['Lab Test'].unique())

                # for each possible combination
                combos.append(
                    {
                        'Number of Tests in Combination': num_combo,
                        'Test Combination': ', '.join(test_lst),
                        'Month': month,
                        'Number of Patients with Abnormal Combination': len(list(pt_tested_abnormal)),
                        'Number of Patients Tested for Combination': len(list(pt_tested)),
                    }
                )
        
    combos = pd.DataFrame(combos)
    return combos


# ### Create Figure For Multiple Tests

from plotly.subplots import make_subplots
import plotly.graph_objects as go

table = combinations_per_month

peakcovid = []
for combo, combo_df in tqdm(table.groupby('Combo')):
    try:
        maxmonthabnormal = combo_df[combo_df['Patients with Abnormal Combo'] == combo_df['Patients with Abnormal Combo'].max()]['Month'].iloc[0]
        maxmonthshare = combo_df[combo_df['Share'] == combo_df['Share'].max()]['Month'].iloc[0]
        if (((maxmonthabnormal == '2020-04') | (maxmonthabnormal == '2020-05')) & ((maxmonthshare == '2020-04') | (maxmonthshare == '2020-05'))):
            peakcovid.append(combo)
    except:
        pass

peakcovid_df = pd.DataFrame(peakcovid,columns=['Combo'])

combo = 'Absolute Eosinophil Count Automated, Ferritin' 
figdf = table[table['Combo'] == combo].sort_values('Month').reset_index(drop = True)

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Bar(x=figdf['Month'], y=figdf['Patients with Abnormal Combo'], name="Number of Patients with Abnormal Result", marker=dict(color="#add8e6")),
    secondary_y=False, row=1, col=1
)

fig.add_trace( 
    go.Scatter(x=figdf['Month'], y=figdf['Share'], name="Share of Patients with Abnormal Result", line=dict(color="#000000", width=3)),
    secondary_y=True, row=1, col=1 
)

# Add figure title
fig.update_layout(title_text= combo)

# Set x-axis title
fig.update_xaxes(title_text="Date")
#fig.update_xaxes(visible = False)

# Set y-axes titles
fig.update_yaxes(title_text="<b>Number</b> of Patients with Abnormal Result", secondary_y=False)
fig.update_yaxes(title_text="<b>Share</b> of Patients with Abnormal Result", secondary_y=True)
fig.update_yaxes(secondary_y=True, tickformat="%") #tickformat=",.1%"

fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.4,
    xanchor="center",
    x=0.2
))

fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
)

fig.show()
