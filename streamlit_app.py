import streamlit as st
import pandas as pd
import numpy as np
import os

# # Set Page Config
# st.set_page_config(page_title="TU Data Processing Tool", page_icon=None, layout="wide", initial_sidebar_state="expanded", menu_items=None)

st.title("TU Data Processing Tool")

# Text input for directory path
directory_path = st.text_input("Enter or paste the directory path:")
deliverect_directory_path = directory_path

# Display selected directory path
if directory_path:
    st.write("Selected directory:", directory_path)

    # Process Deliverect Order Data
    if st.button("Process Deliverect Data"):

        os.chdir(directory_path + r'\01 - Source Data\01 - Deliverect\CSV Files\Orders')

        # Create Deliverect Consolidated File
        deliverect_data = []

        for file_path in [
            '23.01 - Jan 23 Orders.csv',
            '23.02 - Feb 23 Orders.csv',
            '23.03 - Mar 23 Orders.csv',
            '23.04 - Apr 23 Orders.csv',
            '23.05 - May 23 Orders.csv',
            '23.06 - Jun 23 Orders.csv',
            '23.07 - Jul 23 Orders.csv',
            '23.08 - Aug 23 Orders.csv',
            '23.09 - Sep 23 Orders.csv',
            '23.10 - Oct 23 Orders.csv',
            '23.11 - Nov 23 Orders.csv',
            '23.12 - Dec 23 Orders.csv'
        ]:
            if os.path.exists(file_path):
                # If the file path exists, load the corresponding CSV file and append it to the list
                df = pd.read_csv(file_path, dtype={'OrderID': str}, encoding='utf-8')
                df['OrderID'] = '#' + df['OrderID'].astype(str)  # Add '#' in front of OrderID
                deliverect_data.append(df)
            else:
                # If the file path does not exist, append None to the list
                deliverect_data.append(None)

        # Concatenate the loaded data frames
        deliverect_data = pd.concat([df for df in deliverect_data if df is not None])

        # Drop Cancelled Duplicates
        deliverect_data['Status'] = deliverect_data['Status'].replace('CANCELED', 'CANCEL')
        deliverect_data = deliverect_data.drop_duplicates()

        # Clean Created Time
        deliverect_data['AdjustedCreatedTime'] = pd.to_datetime(deliverect_data['CreatedTimeUTC']).dt.tz_localize('UTC')
        deliverect_data['AdjustedCreatedTime'] = deliverect_data['AdjustedCreatedTime'].dt.tz_convert('Europe/Berlin')
        deliverect_data['OrderDate'] = deliverect_data['AdjustedCreatedTime'].dt.date
        deliverect_data['OrderTime'] = deliverect_data['AdjustedCreatedTime'].dt.time

        # Clean Pickup Time
        deliverect_data['AdjustedPickupTime'] = pd.to_datetime(deliverect_data['PickupTimeUTC']).dt.tz_localize('UTC')
        deliverect_data['AdjustedPickupTime'] = deliverect_data['AdjustedPickupTime'].dt.tz_convert('Europe/Berlin')
        deliverect_data['PickupTime'] = deliverect_data['AdjustedPickupTime'].dt.time

        # Clean Scheduled Time
        try:
            deliverect_data['AdjustedScheduledTime'] = pd.to_datetime(
                deliverect_data['ScheduledTimeUTC']).dt.tz_localize('UTC')
            deliverect_data['AdjustedScheduledTime'] = deliverect_data['AdjustedScheduledTime'].dt.tz_convert(
                'Europe/Berlin')
            deliverect_data['ScheduledTime'] = deliverect_data['AdjustedScheduledTime'].dt.time
        except Exception:
            deliverect_data['ScheduledTime'] = np.nan

        # Clean Location
        deliverect_data['Location'] = deliverect_data['Location'].str.replace('Birdie Birdie ', '')
        deliverect_data['Location'] = deliverect_data['Location'].str.replace('Tasty Urban - Prenzlauer Berg',
                                                                              'Prenzlauer Berg')
        deliverect_data['Location'] = deliverect_data['Location'].str.replace('Tasty Urban Prenzlauer Berg',
                                                                              'Prenzlauer Berg')
        deliverect_data['Location'] = deliverect_data['Location'].apply(
            lambda x: x.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore'))
        deliverect_data['Location'] = deliverect_data['Location'].str.replace('Kln Sdstadt', 'Koln Sudstadt')
        deliverect_data['Location'] = deliverect_data['Location'].str.replace('Kln Sdbahnhof', 'Koln Sudbahnhof')
        deliverect_data['Location'] = deliverect_data['Location'].str.strip()

        # Clean Other Columns
        deliverect_data['Channel'] = deliverect_data['Channel'].str.replace('TakeAway Com', 'Lieferando')
        deliverect_data['OrderStatus'] = deliverect_data['Status'].str.replace('_', ' ').str.title()
        deliverect_data['DeliveryType'] = deliverect_data['Type'].str.title()
        deliverect_data['PaymentType'] = deliverect_data['Payment'].str.title()
        deliverect_data['DeliveryFee'] = deliverect_data['DeliveryCost']
        deliverect_data['Discounts'] = deliverect_data['DiscountTotal']
        deliverect_data['GrossAOV'] = deliverect_data['SubTotal']
        deliverect_data['NetAOV'] = deliverect_data['PaymentAmount']
        deliverect_data['Tips'] = deliverect_data['Tip']

        # Clean Food Panda OrderID
        deliverect_data['OrderID'] = np.where(deliverect_data['Channel'] == 'Food Panda',
                                              deliverect_data['OrderID'].str.split(' ', n=1).str[0],
                                              deliverect_data['OrderID'])

        # Create New Columns
        deliverect_data['PrimaryKey'] = deliverect_data['OrderID'] + ' - ' + deliverect_data['Location'] + ' - ' + \
                                        deliverect_data['OrderDate'].astype(str)

        # Drop Columns that aren't needed
        columns_to_drop = ['CreatedTimeUTC', 'PickupTimeUTC', 'ScheduledTimeUTC', 'ReceiptID', 'Note', 'ChannelLink',
                           'Tax', 'FailureMessage', 'LocationID', 'PosLocationID', 'ChannelLinkID',
                           'OrderTotalAmount', 'CustomerAuthenticatedUserId', 'DeliveryTimeInMinutes',
                           'PreparationTimeInMinutes', 'AdjustedCreatedTime', 'AdjustedPickupTime',
                           'AdjustedScheduledTime', 'Type',
                           'Voucher', 'Payment', 'PaymentAmount', 'DiscountTotal', 'SubTotal', 'PaymentAmount', 'Tip',
                           'Status', 'DeliveryCost', 'CreatedTime']
        deliverect_data.drop(columns=columns_to_drop, inplace=True)

        # Sort Columns
        cols = deliverect_data.columns.tolist()
        first_cols = ['OrderDate', 'OrderTime', 'PickupTime', 'ScheduledTime', 'Location', 'Brands', 'OrderID',
                      'Channel', 'OrderStatus', 'DeliveryType', 'PaymentType', 'NetAOV', 'Rebate', 'ServiceCharge',
                      'DeliveryFee', 'Discounts', 'Tips', 'GrossAOV', 'VAT', 'IsTestOrder', 'ProductPLUs',
                      'ProductNames', 'PrimaryKey']
        remaining_cols = [col for col in cols if col not in first_cols]
        deliverect_data = deliverect_data[first_cols + remaining_cols]

        # Sort Rows
        deliverect_data = deliverect_data.sort_values(by=['OrderDate', 'OrderTime'])

        # Align Columns Names
        deliverect_data = deliverect_data.rename(columns={'Discounts': 'PromotionsOnItems'})

        # Standardise Brands
        deliverect_data['Brands'] = np.where(deliverect_data['Brands'].isnull(), 'Birdie Birdie',
                                             deliverect_data['Brands'])
        deliverect_data['Loc with Brand'] = deliverect_data['Location'] + ' - ' + \
                                            deliverect_data['Brands'].str.split(n=1).str[0]

        # Standardise Columns
        column_order = ['PrimaryKey', 'Location', 'Loc with Brand', 'Brands', 'OrderID', 'OrderDate', 'OrderTime',
                        'Channel', 'OrderStatus', 'DeliveryType', 'GrossAOV', 'PromotionsOnItems', 'DeliveryFee',
                        'Tips', 'ProductPLUs', 'ProductNames', 'IsTestOrder', 'PaymentType', 'PickupTime']
        deliverect_data = deliverect_data[column_order]

        # Reset Index
        deliverect_data = deliverect_data.reset_index(drop=True)

        # Remove Duplicate Primary Keys
        cleaned_deliverect_data = deliverect_data['PrimaryKey']
        cleaned_deliverect_data = cleaned_deliverect_data.drop_duplicates()

        # Create new DataFrame
        deliverect_data = deliverect_data[deliverect_data.index.isin(cleaned_deliverect_data.index)]

        # Filter Lieferando Test Order
        deliverect_data = deliverect_data.loc[deliverect_data['OrderID'] != '#63H1WT']

        # Change to Data Directory
        os.chdir(directory_path + r'\99 - Test')

        # Export File
        deliverect_data.to_csv('Deliverect Data.csv', index=False)

        # Process Deliverect Order Data
        if st.button("Process Deliverect Item Level Data"):


        st.success("Data processing completed successfully.")

else:
    st.write("Invalid directory path.")