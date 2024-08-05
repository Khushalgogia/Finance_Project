import pandas as pd
from nselib import (
    capital_market,
)  # Ensure this is correctly imported based on your setup
from datetime import datetime, timedelta
from pyxirr import xirr


def get_market_price(symbol, date):
    date_obj = datetime.strptime(date, "%d-%m-%Y")
    date_pd = pd.Timestamp(date_obj)

    df_price_volume = capital_market.price_volume_and_deliverable_position_data(
        symbol=symbol,
        from_date=date_pd.strftime("%d-%m-%Y"),
        to_date=(date_pd + pd.Timedelta(days=1)).strftime("%d-%m-%Y"),
    )

    if not df_price_volume.empty:
        closing_price = df_price_volume["ClosePrice"].iloc[0]
        return closing_price
    else:
        print(f"No data available for the given date range for {symbol}.")
        return None


def xirr_cal(stock_df, start_date, last_date):
    cumulative_quantity = 0
    cash_flows = []
    dates = []
    trans_types = []
    quantities_left = []
    stock_name = stock_df["NSE Code"].iloc[0]
    has_buy_transactions = False

    start_date_obj = datetime.strptime(start_date, "%d-%m-%Y")
    start_date_pd = pd.Timestamp(start_date_obj)

    last_date_obj = datetime.strptime(last_date, "%d-%m-%Y")
    last_date_pd = pd.Timestamp(last_date_obj)

    # Calculate the opening balance at start_date
    pre_start_transactions = stock_df[
        pd.to_datetime(stock_df["Date"], format="%d-%m-%Y") < start_date_pd
    ]
    for _, row in pre_start_transactions.iterrows():
        if row["Trans. Type"] == "Buy":
            cumulative_quantity += row["Quantity"]
        elif row["Trans. Type"] == "Sell":
            cumulative_quantity -= row["Quantity"]
        elif row["Trans. Type"] in [
            "Bonus",
            "*Split",
            "*DeMerger (New)",
            "*DeMerger",
            "*Merger",
            "*Merged",
        ]:
            cumulative_quantity += row["Quantity"]

    if cumulative_quantity > 0:
        start_date_market_price = get_market_price(
            stock_df["NSE Code"].iloc[0], start_date
        )
        if start_date_market_price is None:
            return pd.DataFrame(
                {
                    "Portfolio_Name": [stock_df["Portfolio_Name"].iloc[0]],
                    "Strategy_ID": [stock_df["Strategy_ID"].iloc[0]],
                    "NSE Code": [stock_df["NSE Code"].iloc[0]],
                    "XIRR": [None],
                }
            ), pd.DataFrame(
                {
                    "Stock": [],
                    "Date": [],
                    "Cash Flow": [],
                    "Trans. Type": [],
                    "Quantity Left": [],
                }
            )
        start_date_market_price = float(str(start_date_market_price).replace(",", ""))
        opening_balance = cumulative_quantity * start_date_market_price

        cash_flows.append(opening_balance)
        dates.append(start_date_pd)
        trans_types.append("Opening Balance")
        quantities_left.append(cumulative_quantity)

    # Process transactions from start_date to last_date
    for _, row in stock_df.iterrows():
        date_str = row["Date"]
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        if date_obj < start_date_obj or date_obj > last_date_obj:
            continue

        if row["Trans. Type"] == "Buy":
            cumulative_quantity += row["Quantity"]
            cash_flows.append(-float(row["Amount"]))
            has_buy_transactions = True
        elif row["Trans. Type"] == "Sell":
            cumulative_quantity -= row["Quantity"]
            cash_flows.append(float(row["Amount"]))
        elif row["Trans. Type"] == "Dividend Payout":
            cash_flows.append(float(row["Amount"]))
        elif row["Trans. Type"] in [
            "Bonus",
            "*Split",
            "*DeMerger (New)",
            "*DeMerger",
            "*Merger",
            "*Merged",
        ]:
            cumulative_quantity += row["Quantity"]

        dates.append(pd.Timestamp(date_obj))
        trans_types.append(row["Trans. Type"])
        quantities_left.append(cumulative_quantity)

    if not has_buy_transactions:
        return pd.DataFrame(
            {
                "Portfolio_Name": [stock_df["Portfolio_Name"].iloc[0]],
                "Strategy_ID": [stock_df["Strategy_ID"].iloc[0]],
                "NSE Code": [],
                "XIRR": [],
            }
        ), pd.DataFrame(
            {
                "Stock": [],
                "Date": [],
                "Cash Flow": [],
                "Trans. Type": [],
                "Quantity Left": [],
            }
        )

    if cumulative_quantity > 0:
        last_date_market_price = get_market_price(
            stock_df["NSE Code"].iloc[0], last_date
        )
        if last_date_market_price is None:
            return pd.DataFrame(
                {
                    "Portfolio_Name": [stock_df["Portfolio_Name"].iloc[0]],
                    "Strategy_ID": [stock_df["Strategy_ID"].iloc[0]],
                    "NSE Code": [stock_df["NSE Code"].iloc[0]],
                    "XIRR": [None],
                }
            ), pd.DataFrame(
                {
                    "Stock": [],
                    "Date": [],
                    "Cash Flow": [],
                    "Trans. Type": [],
                    "Quantity Left": [],
                }
            )
        last_date_market_price = float(str(last_date_market_price).replace(",", ""))
        remaining_value = cumulative_quantity * last_date_market_price

        cash_flows.append(remaining_value)
        dates.append(last_date_pd)
        trans_types.append("Market Price")
        quantities_left.append(cumulative_quantity)

    sorted_data = sorted(
        zip(dates, cash_flows, trans_types, quantities_left), key=lambda x: x[0]
    )
    sorted_dates, sorted_cash_flows, sorted_trans_types, sorted_quantities_left = zip(
        *sorted_data
    )

    xirr_value = xirr(sorted_dates, sorted_cash_flows)

    xirr_result_df = pd.DataFrame(
        {
            "Portfolio_Name": [stock_df["Portfolio_Name"].iloc[0]],
            "Strategy_ID": [stock_df["Strategy_ID"].iloc[0]],
            "NSE Code": [stock_df["NSE Code"].iloc[0]],
            "XIRR": [xirr_value],
        }
    )

    detailed_cash_flows_df = pd.DataFrame(
        {
            "Stock": [stock_name] * len(sorted_dates),
            "Date": sorted_dates,
            "Cash Flow": sorted_cash_flows,
            "Trans. Type": sorted_trans_types,
            "Quantity Left": sorted_quantities_left,
        }
    )

    return xirr_result_df, detailed_cash_flows_df


# Read data from CSV
df = pd.read_csv("Share_Trading_Full.csv", skiprows=1)

results_df = pd.DataFrame(columns=["Portfolio_Name", "Strategy_ID", "NSE Code", "XIRR"])
detailed_cash_flows_df = pd.DataFrame(
    columns=["Stock", "Date", "Cash Flow", "Trans. Type", "Quantity Left"]
)

start_date = "01-01-2024"  # Example start date
last_date = "10-07-2024"

unique_portfolio_names = df["Portfolio_Name"].unique()
unique_strategy_ids = df["Strategy_ID"].unique()
unique_nse_codes = df["NSE Code"].unique()

for portfolio_name in unique_portfolio_names:
    for strategy_id in unique_strategy_ids:
        for nse_code in unique_nse_codes:
            code_df = df[
                (df["Portfolio_Name"] == portfolio_name)
                & (df["Strategy_ID"] == strategy_id)
                & (df["NSE Code"] == nse_code)
            ]
            if not code_df.empty:
                try:
                    xirr_result, detailed_cash_flows = xirr_cal(
                        code_df, start_date, last_date
                    )
                    results_df = pd.concat([results_df, xirr_result], ignore_index=True)
                    detailed_cash_flows_df = pd.concat(
                        [detailed_cash_flows_df, detailed_cash_flows], ignore_index=True
                    )
                except Exception as e:
                    print(
                        f"Error processing {portfolio_name}, {strategy_id}, {nse_code}: {e}"
                    )

results_df