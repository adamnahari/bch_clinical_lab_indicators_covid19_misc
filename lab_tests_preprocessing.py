#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

from datetime import timedelta


# ### Define Care Periods

# if two tests were taken by the same person less then 6 days apart, combine them into the same group
visit_time = 6 # days
test_groups = []

for mrn, mrn_df in tqdm(labs_clean.groupby('MRN')):
    refrence_labs = mrn_df.copy()
    for index, row in mrn_df.iterrows(): 
        date = row['Lab Event End Dt Tm']
        date_limit = date + timedelta(days=visit_time)
        mask = (refrence_labs['Lab Event End Dt Tm'] >= date) & (refrence_labs['Lab Event End Dt Tm'] < date_limit)
        other_tests = refrence_labs.loc[mask]
        
        first = other_tests['Lab Event End Dt Tm'].min()
        last = other_tests['Lab Event End Dt Tm'].max()

        test_groups.append(
            {
                'MRN': mrn,
                'Date of First Test': first,
                'Date of Last Test': last,
            }
        )

test_groups = pd.DataFrame(test_groups)

test_groups_final = test_groups.copy()
test_groups_final = test_groups_final.drop_duplicates().sort_values('Date of First Test').reset_index(drop = True)

consolidated = []
for mrn, mrn_df in tqdm(test_groups_final.groupby(['MRN'])):
    df = mrn_df.reset_index(drop = True)
    first = df['Date of First Test'][0]
    last = df['Date of Last Test'][0]
    for index, row in df.iterrows():
        # extend period if new start date is before old end date AND new end date is after old end date 
        if (row['Date of First Test'] <= last) & (row['Date of Last Test'] > last):
            last = row['Date of Last Test']
        # start new period if new start date is after is after old end date
        elif (row['Date of First Test'] > last):            
            consolidated.append(
                {
                    'MRN': mrn,
                    'Date of First Test': first,
                    'Date of Last Test': last,
                }
            )
            first = row['Date of First Test']
            last = row['Date of Last Test']
    # if reached the end, add last period    
    consolidated.append(
        {
            'MRN': mrn,
            'Date of First Test': first,
            'Date of Last Test': last,
        }
    )
    
consolidated = pd.DataFrame(consolidated)
consolidated = consolidated.reset_index(drop = True)
consolidated['ID'] =  consolidated['MRN'] + ":" + consolidated.index.astype(str)


# ### Match Each Test with its Corsoponding Care Period

labs_care_periods = []
for mrn, mrn_df in tqdm(labs_clean.groupby('MRN')):
    potential_care_period = consolidated[consolidated['MRN'] == mrn]
    for index, row in mrn_df.iterrows():
        time = row['Lab Event End Dt Tm']
        mask = (time >= potential_care_period['Date of First Test']) & (time <= potential_care_period['Date of Last Test'])
        care_period = potential_care_period.loc[mask]
        labs_care_periods.append(
            {
                'MRN': mrn,
                'Gender': row['Gender'],
                'Age': row['Age At Visit In Days'],
                'Lab': row['Lab Event'],
                'Result': row['Lab Result Val'],
                'Date': row['Lab Event End Dt Tm'],
                'Care Period': care_period['ID'].iloc[0]
            }
        )

labs_care_periods = pd.DataFrame(labs_care_periods)


# ### Identify Max / Min Lab Result Per Patient Per Period

labs_care_periods['Month'] = pd.to_datetime(labs_care_periods['Date']).dt.to_period('M')

max_tests = ['WBC',  
             'Neutrophil Automated', 
             'Creatinine', 
             'BUN', 
             'Alkaline Phosphatase', 
             'Bilirubin, Total', 
             'Bilirubin, Direct', 
             'AST (Aspartate Aminotransferase)', 
             'ALT', 
             'GGTP (Gamma Glutamyl Transpeptidase)', 
             'C-Reactive Protein', 
             'Ferritin', 
             'ESR (Erythrocyte Sedimentation Rate)', 
             'PCT', 
             'Fibrinogen', 
             'INR', 
             'B-Type Natriuretic Peptide', 
             'LDH (Lactate Dehydrogenase)', 
             'Troponin T', 
             'Troponin-I', 
             'D-Dimer', 
             'IL2', 'IL2 Rec', 'IL2 Receptor', 'IL12', 'IL8', 'IL10', 'IL13', 'IL4', 'IL6', 'IL5', 
             'TNF']

min_tests = ['RBC', 
             'Absolute Lymphocyte Count Automated', 
             'Absolute Eosinophil Count Automated',
             'Hemoglobin', 
             'Hematocrit', 
             'Platelet', 
             'Monocyte Automated', 
             'Basophil Automated', 
             'Albumin', 
             'Albumin:']

labs_final = []
for group, group_df in tqdm(labs_care_periods.groupby(['MRN', 'Care Period', 'Lab'])): #
    if group_df['Lab'].iloc[0] in max_tests:
        i = group_df['Result'].idxmax()
    elif group_df['Lab'].iloc[0] in min_tests:
        i = group_df['Result'].idxmin()
    row = group_df.loc[i]

    labs_final.append(
        {
            'MRN': row['MRN'],
            'Gender': row['Gender'],
            'Age': row['Age'],
            'Lab': row['Lab'],
            'Result': row['Result'],
            'Date': row['Date'],
            'Month': row['Month'],
            'Care Period': row['Care Period'],
        })

labs_final = pd.DataFrame(labs_final).reset_index(drop = True)


# ### Mark Labs as either Normal or Abnormal

def get_result_type(row):
    # RBC less than 3.8
    if row['Lab'] == 'RBC':
        if row['Result'] < 3.8:  
            return 'abnormal'
        else:
            return 'normal'

    # Absolute Lymphocyte Count Automated 
    # Lymphocytopenia defined as absolute lymphocyte count of less than 1.5 × 10^9 cells/L 
    # in patients 8 months of age or older and of less than 4.5 × 10^9 cells/L in patients 
    # younger than 8 months of age.
    elif row['Lab'] == 'Absolute Lymphocyte Count Automated':
        # older than 8 months
        if row['Age'] > 242:
            if row['Result'] < 1.5:  
                return 'abnormal'
            else:
                return 'normal'
        else:
            if row['Result'] < 4.5:  
                return 'abnormal'
            else:
                return 'normal'

    # Absolute Eosinophil Count Automated 
    # Eosinopenia defined as absolute eosinophil count of less than 0.02 × 10^9 cells/L)
    elif row['Lab'] == 'Absolute Eosinophil Count Automated':
        if row['Result'] < 0.02:  
            return 'abnormal'
        else:
            return 'normal'

    # Hemoglobin less than 9 g/dL
    elif row['Lab'] == 'Hemoglobin':
        if row['Result'] < 9:  
            return 'abnormal'
        else:
            return 'normal'
    
    # Hematocrit less than 30
    elif row['Lab'] == 'Hematocrit':
        if row['Result'] < 30:  
            return 'abnormal'
        else:
            return 'normal'

    # Platelet less than 150,000 mm^3
    elif row['Lab'] == 'Platelet':
        if row['Result'] < 150:  
            return 'abnormal'
        else:
            return 'normal'

    # Albumin less than or equel to 3 g/dl
    elif row['Lab'] == 'Albumin':
        if row['Result'] <= 3:  
            return 'abnormal'
        else:
            return 'normal'

    # Monocyte Automated less than 2
    elif row['Lab'] == 'Monocyte Automated':
        if row['Result'] < 2:  
            return 'abnormal'
        else:
            return 'normal'

    # Basophil Automated less than 0.21
    elif row['Lab'] == 'Basophil Automated':
        if row['Result'] < 0.21:  
            return 'abnormal'
        else:
            return 'normal'
        
    # Neutrophil Automated more than 77
    elif row['Lab'] == 'Neutrophil Automated':
        if row['Result'] > 77:  
            return 'abnormal'
        else:
            return 'normal'

    # D-Dimer more than 3
    elif row['Lab'] == 'D-Dimer':
        if row['Result'] > 3:  
            return 'abnormal'
        else:
            return 'normal'
        
    # Fibrinogen more than 400
    elif row['Lab'] == 'Fibrinogen':
        if row['Result'] > 400:  
            return 'abnormal'
        else:
            return 'normal'

    # INR more than 1.1
    elif row['Lab'] == 'INR':
        if row['Result'] > 1.1:  
            return 'abnormal'
        else:
            return 'normal'

    # C-Reactive Protein more than or equal to 3
    elif row['Lab'] == 'C-Reactive Protein':
        if row['Result'] >= 3:  
            return 'abnormal'
        else:
            return 'normal'

    # Ferritin more than 500
    elif row['Lab'] == 'Ferritin':
        if row['Result'] > 500:  
            return 'abnormal'
        else:
            return 'normal'

    # ESR more than or equal to 40
    elif row['Lab'] == 'ESR (Erythrocyte Sedimentation Rate)':
        if row['Result'] >=40:  
            return 'abnormal'
        else:
            return 'normal'
        
    # BNP more than 400
    elif row['Lab'] == 'B-Type Natriuretic Peptide':
        if row['Result'] > 400:  
            return 'abnormal'
        else:
            return 'normal'

    # ALT more than or equal to 40
    elif row['Lab'] == 'ALT':
        if row['Result'] >=40:  
            return 'abnormal'
        else:
            return 'normal'

    # Creatinine more than 0.59
    elif row['Lab'] == 'Creatinine':
        if row['Result'] > 0.59:  
            return 'abnormal'
        else:
            return 'normal'

    # AST more than 50
    elif row['Lab'] == 'AST (Aspartate Aminotransferase)':
        if row['Result'] > 50:  
            return 'abnormal'
        else:
            return 'normal'

    # PCT more than 50 ng/mL
    elif row['Lab'] == 'PCT':
        if row['Result'] > 50:  
            return 'abnormal'
        else:
            return 'normal'

    # LDH more than 500 
    elif row['Lab'] == 'LDH (Lactate Dehydrogenase)':
        if row['Result'] > 500:  
            return 'abnormal'
        else:
            return 'normal'

    # WBC more than 20 
    elif row['Lab'] == 'WBC':
        if row['Result'] > 20:  
            return 'abnormal'
        else:
            return 'normal'

    # Bilirubin, Total more than 1 
    elif row['Lab'] == 'Bilirubin, Total':
        if row['Result'] > 1:  
            return 'abnormal'
        else:
            return 'normal'

    # Bilirubin, Direct more than 0.4
    elif row['Lab'] == 'Bilirubin, Direct':
        if row['Result'] > 0.4:  
            return 'abnormal'
        else:
            return 'normal'

    # BUN more than 18
    elif row['Lab'] == 'BUN':
        if row['Result'] > 18:  
            return 'abnormal'
        else:
            return 'normal'
        
    # GGTP more than 51
    elif row['Lab'] == 'GGTP (Gamma Glutamyl Transpeptidase)':
        if row['Result'] > 51:  
            return 'abnormal'
        else:
            return 'normal'

    # Troponin T more than 0.1
    elif row['Lab'] == 'Troponin T':
        if row['Result'] > 0.1:  
            return 'abnormal'
        else:
            return 'normal'
        
    # Troponin I more than 0.04
    elif row['Lab'] == 'Troponin-I':
        if row['Result'] > 0.04:  
            return 'abnormal'
        else:
            return 'normal'

    # TNF more than 22 
    elif row['Lab'] == 'TNF':
        if row['Result'] > 22:  
            return 'abnormal'
        else:
            return 'normal'

    # IL2 Receptor more than 858.2
    elif row['Lab'] == 'IL2 Receptor':
        if row['Result'] > 858.2:  
            return 'abnormal'
        else:
            return 'normal'
        
    # IL2 more than 9
    elif row['Lab'] == 'IL2':
        if row['Result'] > 9:  
            return 'abnormal'
        else:
            return 'normal'

    # IL4 more than 3
    elif row['Lab'] == 'IL4':
        if row['Result'] > 3:  
            return 'abnormal'
        else:
            return 'normal'

    # IL6 more than 9 
    elif row['Lab'] == 'IL6':
        if row['Result'] > 9:  
            return 'abnormal'
        else:
            return 'normal'
        
    # IL8 more than 116 
    elif row['Lab'] == 'IL8':
        if row['Result'] > 116:  
            return 'abnormal'
        else:
            return 'normal'

    # IL10 more than 9.2 
    elif row['Lab'] == 'IL10':
        if row['Result'] > 9.2:  
            return 'abnormal'
        else:
            return 'normal'

    else:
        return "Undetermined"

labs_final['Result Type'] = labs_final.progress_apply(get_result_type, axis = 1)
