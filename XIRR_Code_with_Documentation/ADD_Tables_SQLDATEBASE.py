# XIRR ADD

import pandas as pd
from sqlalchemy import create_engine
import psycopg2 as ps


def insert_data_to_postgresql(dataframe, conn, table_name):
    # Create an engine
    engine = create_engine(
        f"postgresql+psycopg2://postgres:khushal@localhost:5432/real_project"
    )

    # Write DataFrame to PostgreSQL
    dataframe.to_sql(
        table_name, engine, schema="Active", if_exists="append", index=False
    )

    print(
        f"Table {table_name} created/updated successfully in the PostgreSQL database."
    )


# Example usage
if __name__ == "__main__":
    # PostgreSQL connection
    try:

        # Enter you Postgrad details

        
        conn = ps.connect(
            dbname="",
            user="",
            password="",
            host="",
            port="",
            connect_timeout=10,
            sslmode="prefer",
        )

        # Insert data into PostgreSQL
        insert_data_to_postgresql(results_df, conn, "Portfolio_Xirr_report")

        # Close PostgreSQL connection
        conn.close()
        print("Data successfully inserted into PostgreSQL database.")
    except Exception as e:
        print(f"An error occurred: {e}")



    
