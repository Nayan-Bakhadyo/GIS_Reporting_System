
def BTS_Tower_style_function(feature):
    tower_owner = feature['properties']['Tower_owne']
    if tower_owner == 'NCELL':
        return {'color': 'purple'}
    elif tower_owner == 'NTC_GSM':
        return {'color': 'blue'}
    else:
        return {'color': 'black'}