import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt

bet = pd.read_csv('jjb_move_0305.csv')
price_mat = pd.read_csv('jjb_price_0305.csv',index_col='Date',parse_dates=True)

### data cleansing
price_mat.dropna(axis=0,inplace=True)
price_mat.sort_index(ascending=True,inplace=True)



def get_pnl(ticker, bet,price_mat):
    i = ticker
    ## PNL matrix
    raw_data = {'entry_amount': 0,
                'entry_price': 0,
                'current_price': 0,
                'position_value': 0,
                'exit_price':0,
                'cash': 0}

    if isinstance(bet.set_index('Ticker').loc[i],pd.Series):
        by_ticker = bet.set_index('Ticker').loc[i]
        date = by_ticker['Date']
        date = [dt.datetime.strptime(date,"%Y-%m-%d")]
        amount = [by_ticker['Amount']]
        price = [by_ticker['Price']]
        exit = [by_ticker['Exit']]
        max_len = 1

    else:
        by_ticker = bet.set_index('Ticker').loc[i]
        by_ticker.sort_values('Date',inplace=True)
        date = by_ticker['Date'].values
        date = [dt.datetime.strptime(x,'%Y-%m-%d') for x in date]
        amount = by_ticker['Amount'].values
        price = by_ticker['Price'].values
        exit = by_ticker['Exit'].values

        max_len = len(date)
        print(by_ticker)

    pnl_mat = pd.DataFrame(raw_data,index=price_mat.index)

    last_cash = 0
    last_position = 0
    last_entry_amount = 0
    last_exit_price = 0

    for j in pnl_mat.index:
        for k in range(0,max_len):
            if j >= date[k]:
                ## entry amount
                last_entry_amount = pnl_mat['entry_amount'].loc[j]
                pnl_mat['entry_amount'].loc[j] = last_entry_amount + amount[k]

                ## entry price
                if k == 0:
                    last_entry_price = price[k]
                    pnl_mat.loc[j,'entry_price'] = last_entry_price
                elif exit[k] != 'x':
                    last_entry_price = (price[k]*amount[k]+last_entry_price*last_entry_amount)/(amount[k]+last_entry_amount)
                    pnl_mat.loc[j, 'entry_price'] = last_entry_price
                elif exit[k] == 'x':
                    pnl_mat['entry_price'].loc[j] = last_entry_price


                if pnl_mat['entry_amount'].loc[j] == 0 :
                   last_entry_price = 0

                ## current price
                pnl_mat['current_price'].loc[j] = price_mat[i].loc[j]

                ## position value
                pnl_mat['position_value'].loc[j] = pnl_mat['entry_amount'].loc[j] *pnl_mat['current_price'].loc[j]/pnl_mat['entry_price'].loc[j]

                ## exit price
                if exit[k] == 'x':
                    pnl_mat['exit_price'].loc[j] = price[k]


        ## Cash
        buy_sell = pnl_mat.loc[j,'entry_amount'] - last_position
        if buy_sell != 0 and last_exit_price == pnl_mat.loc[j,'exit_price']: ## Buy
            last_cash = last_cash - buy_sell
            pnl_mat.loc[j,'cash'] = last_cash
            last_position = pnl_mat.loc[j,'entry_amount']
        elif buy_sell != 0 and last_exit_price != pnl_mat.loc[j,'exit_price']: ## Sell
            last_cash = last_cash - buy_sell*pnl_mat.loc[j,'exit_price']/pnl_mat.loc[j,'entry_price']
            pnl_mat.loc[j,'cash'] = last_cash
            last_exit_price = pnl_mat.loc[j,'exit_price']
            last_position = pnl_mat.loc[j, 'entry_amount']
        else :
            pnl_mat.loc[j,'cash'] = last_cash

    pnl_mat.to_csv('ex.csv')
    return pnl_mat['cash']+ pnl_mat['position_value']


cols = price_mat.columns

total_mat = ''

for i in cols:
    pnl = get_pnl(i,bet,price_mat)
    pnl = pd.DataFrame(pnl,columns=[i])
    if not isinstance(total_mat,pd.DataFrame):
        total_mat = pnl
        total_mat.columns = [i]
    else:
        total_mat = total_mat.merge(pnl,left_index=True,right_index=True)


total_mat['sum'] = total_mat.sum(axis=1)
total_mat.to_csv('jjb_return.csv')
total_mat['sum'].plot()
plt.show()
