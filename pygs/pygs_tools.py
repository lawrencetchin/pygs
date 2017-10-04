#!/usr/bin/env python
import string
import initialize_service as initService
import pandas as pd
from numpy import nan

def _cleanSheetName(sheet_name, spreadsheetId):
    service = initService._getService()
    current_state = service.spreadsheets().get(spreadsheetId = spreadsheetId).execute()
    tot_names = []
    for sheet in current_state['sheets']:
        if sheet_name.lower() == sheet['properties']['title'].lower():
            try:
                name_split = sheet['properties']['title'].split(sheet_name + "_")
                if len(name_split) > 1:
                    tot_names.append(int(name_split[-1])) 
                else:
                    tot_names.append(0) 
            except ValueError:
                pass
    if len(tot_names) == 0:
        return sheet_name
    new_sheet_name = sheet_name + "_" + str(max(tot_names)+1)
    return new_sheet_name

def _getEndCol(two_dim_array):
    array_length = len(two_dim_array[0])
    
    if array_length > 702:
        raise ValueError("You have more than 702 columns which would be past column 'ZZ'. Please make smarter choices.")
    
    lookup_dict = {}
    for pos, char in enumerate(string.ascii_uppercase):
        lookup_dict[pos+1] = char
        
    if array_length <= 26:
        return lookup_dict[array_length]
    
    if array_length % 26 == 0:
        first_letter = lookup_dict[(array_length%26)+(array_length/26)-1]
        second_letter = 'Z'
    else:
        first_letter = lookup_dict[array_length/26]
        second_letter = lookup_dict[array_length%26]
    
    return first_letter + second_letter

def _cleanDF(df):
    #handles converting strings to unicode or int/floats to strings
    def convertCell(cellVal):
        try:
            return str(cellVal)
        except UnicodeEncodeError:
            return cellVal.encode('utf-8').strip()
    #fill any NA's
    df = df.fillna('')
    #try to encode it as a string, if all else fails, do utf-8
    #TODO - check how utf-8 handles datetimes
    try:
        df = df.astype(str)
    except UnicodeEncodeError:
        for col in df.columns:
            df[col] = df[col].apply(lambda x: convertCell(x))
    return df

def _fixResponse(response):
    #return response
    if len(response['values']) > 1:
        #setup the dataframe with no headers
        df = pd.DataFrame(response['values'][1:]).fillna(value = nan).fillna('')
        #get the width of the DF to see if we need to add/remove columns
        width = df.shape[1]
        header = response['values'][0]
        #if there are more headers then there are columns, just make the columns empty
        if len(header) > width:
            df.columns = header[:width]
            for col in header[width:]:
                df[col] = ''
            #df = pd.concat([df,pd.DataFrame(columns=header[width:])]).fillna('')
            return df
        else:
            #if the body is bigger than the header, adjust accordingly:
            df.columns = [x for x in header] + ["Unnamed Sheet Col " + str(x) for x in range(1, df.shape[1] - len(header) + 1) if x >= 0]
            df = df.fillna('')
            return df
    #if we only have a header row, just make the empty DF
    if len(response['values']) == 1:
        return pd.DataFrame(columns=response['values'][0])