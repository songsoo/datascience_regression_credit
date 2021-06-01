import sklearn
from sklearn import preprocessing, __all__, linear_model
from sklearn.ensemble import BaggingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot as plt
import seaborn as sns

pd.set_option('display.max_columns',None)

credit = pd.read_csv(r"credit_record.csv")
application = pd.read_csv(r"application_record.csv")
#combine application_record.csv & credit_record.csv()
df = application.merge(credit,how='left',on='ID')
print("\n============combien two csv file===============")
print(df)#it must have na becuase application_record doesn't have a lot of ids in the credit_record.csv
df = df[df['STATUS'].notna()]

# make DAYS_BIRTH and DAYS_EMPLOYED be Non-negative value
df["DAYS_BIRTH"] = -df["DAYS_BIRTH"]
df["DAYS_EMPLOYED"] = -df["DAYS_EMPLOYED"]

print("\n============STATUS null column remove(ID that doesn't exist in application=======")
print(df)#ID overlapping between credit and application

#Remove duplicate IDs except the first one
df = df.drop_duplicates(['ID'],keep="first",ignore_index=True)
print("\n===============remove ID duplicate================")
print(df)

#Remove STATUS=='X' (it does't need to analysis) -> 타겟팅 바꾸면서 필요없어짐
"""
idx = df[df['STATUS']=='X'].index
df.drop(idx,inplace=True)
print("\n========remvoe 'STAUS=X'=============")
print(df)
"""

#FLAG_MOBIL romove reason
df_mobile = df[(df['FLAG_MOBIL']==1)]
mobile_ratio = len(df_mobile)/len(df)
print("\n==========Ratio of mobile phone holers===========")
print("Ratio of mobile phone holers : " , mobile_ratio,"\n")

#OCCUPATION remove reason
ocp_null = df['OCCUPATION_TYPE'].isnull().sum() #null값의 개수를 구하기
print("ocp_null : " , ocp_null)
ocp_len = len(df)
print("occupation_type percentage : ", ocp_null/ocp_len,"\n")

#Remove two columns -> FLAG_MOBIL/OCCUPATION_TYPE(모두 동일한 값이라서, 0.3%의 null값이 있어)
df.drop(['FLAG_MOBIL' , 'OCCUPATION_TYPE'], axis=1, inplace=True)
print("\n========column list(after remove two columns=============")
print(df.columns.tolist())


#STATUS를 라벨링 ->
df.at[df['STATUS']=='X', 'STATUS']=0
df.at[df['STATUS']=='C', 'STATUS']=1
df.at[df['STATUS']=='0', 'STATUS']=2
df.at[df['STATUS']=='1', 'STATUS']=3
df.at[df['STATUS']=='2', 'STATUS']=4
df.at[df['STATUS']=='3', 'STATUS']=5
df.at[df['STATUS']=='4', 'STATUS']=6
df.at[df['STATUS']=='5', 'STATUS']=7
print("\n========STATUS 재분류=============")
print(df['STATUS'])


#bfill 로 채우기 na값 채우기
df.fillna(method='bfill',inplace=True)

#categorical feature
#NAME_HOUSING_TYPE/ CODE_GENDER/ FLAG_OWN_CAR
#/NAME_INCOME_TYPE/NAME_FAMILY_STATUS/NAME_EDUCATION_TYPE
#STATUS <- 이미 라벨링

#label encoding
from sklearn import preprocessing
le = preprocessing.LabelEncoder()

df['CODE_GENDER']=le.fit_transform(df['CODE_GENDER'])
df['FLAG_OWN_CAR']=le.fit_transform(df['FLAG_OWN_CAR'])
df['FLAG_OWN_REALTY']=le.fit_transform(df['FLAG_OWN_REALTY'])


#onehot encoding
from sklearn import preprocessing
le = preprocessing.OneHotEncoder()

def labelEncode(df, name):
    encoder = preprocessing.LabelEncoder()
    encoder.fit(df[name])
    labels = encoder.transform(df[name])
    df.loc[:, name] = labels

def onehotEncode(df,name):
    le = preprocessing.OneHotEncoder(handle_unknown='ignore')
    enc = df[[name]]
    enc = le.fit_transform(enc).toarray()
    enc_df = pd.DataFrame(enc, columns=le.categories_[0])
    df.loc[:, le.categories_[0]] = enc_df

df = df.reset_index(drop=True)

# onehotEncode(df,'NAME_HOUSING_TYPE')
# onehotEncode(df,'NAME_INCOME_TYPE')
# onehotEncode(df,'NAME_FAMILY_STATUS')
# onehotEncode(df,'NAME_EDUCATION_TYPE')
labelEncode(df,'NAME_HOUSING_TYPE')
labelEncode(df,'NAME_INCOME_TYPE')
labelEncode(df,'NAME_FAMILY_STATUS')
labelEncode(df,'NAME_EDUCATION_TYPE')
df.drop(columns=['NAME_HOUSING_TYPE','NAME_INCOME_TYPE','NAME_FAMILY_STATUS','NAME_EDUCATION_TYPE'],inplace=True)




#feature scaling (categorical은 labeling 돼서 필요X)
#'AMT_INCOME_TOTAL','DAYS_BIRTH','DAYS_EMPLOYED' 세가지만

cols = {'DAYS_BIRTH','DAYS_EMPLOYED'}

scaler = preprocessing.StandardScaler()
scaled_Sd = scaler.fit_transform(df.loc[:,cols])
df_Sd = df
df_Sd.loc[:,cols] = scaled_Sd

print("\n========Standard Scaler for some numerical features=============")
print(df[['DAYS_BIRTH','DAYS_EMPLOYED']])

#outlier
#numericla features(those have outliers)
def outliers_iqr(df,name):
    q1 = df[name].quantile(0.25)
    q3 = df[name].quantile(0.75)
    iqr = q3 - q1
    search = df[(df[name]<(q1 - 1.5 * iqr))|(df[name]>(q3 + 1.5 * iqr))]
    df = df.drop(search.index,axis=0)
    return df

df = outliers_iqr(df,'AMT_INCOME_TOTAL')
df = outliers_iqr(df,'DAYS_BIRTH')
df = outliers_iqr(df,'DAYS_EMPLOYED')


# Correlation HeatMap
# removed non necessary Categorical data
dfc = df.drop(columns=["STATUS", "ID", "FLAG_PHONE"], inplace=False)
plt.figure(figsize=(13,13))
sns.heatmap(data=dfc.corr(), annot=True,
fmt = '.2f', linewidths=.5, cmap='Blues')
plt.show()

#Use ensemble learning to predict and evaluate (cv: KFold, GradientBoosting method)
#target: 'AMT_INCOME_TOTAL',
# target = df.columns.tolist()
# target.remove('AMT_INCOME_TOTAL')
# target.remove('ID')
# feature = {'AMT_INCOME_TOTAL'}
#
# FoldNum = 2
# x = pd.DataFrame(df.loc[:,target],columns=target)
# y = df[['AMT_INCOME_TOTAL']]
# x_train, x_test, y_train, y_test= train_test_split(x,y, test_size = 1/FoldNum, shuffle=True)
# x_train, x_valid, y_train, y_valid= train_test_split(x_train,y_train, test_size = 1/FoldNum, shuffle=True)
#
# param_grid = {'n_estimators':[100,200,300],'max_features':[1,4,7],'max_depth':[1,10,100,200],'criterion':["mse","friedman_mse"]}
# model = sklearn.ensemble.GradientBoostingRegressor(learning_rate=0.01,min_samples_split=3)
#
# kfold = KFold(FoldNum,shuffle=True,random_state=1)
# GBR_gscv = GridSearchCV(model, param_grid,cv=kfold,n_jobs=-1)
# GBR_gscv.fit(x_train,y_train.values.ravel())
#
# GBR_gscv.fit(x_valid,y_valid.values.ravel())
# print("\nValid Score: ",GBR_gscv.score(x_valid,y_valid))
#
# GBR_gscv.fit(x_test,y_test.values.ravel())
# ypred = GBR_gscv.predict(x_test)
# mse_GBR = mean_squared_error(y_test,ypred)
# print("Test Score: ",GBR_gscv.score(x_test,y_test))
# print("MSE on test set: {:.4f}".format(mse_GBR))
#
#
# y_predict = GBR_gscv.predict(x_test)
# compareY = pd.DataFrame(y_test)
# compareY['predict'] = y_predict.round()
# compareY['difference'] = abs(compareY['AMT_INCOME_TOTAL'] - compareY['predict'])
# print("\n",compareY)


