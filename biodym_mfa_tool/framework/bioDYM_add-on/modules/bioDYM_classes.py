"""
Created on 20.02.2025

@author: lhoppe
"""

"""
File bioDYM_classes

Contains parameter definition for first order model processes

standard abbreviation: bicl


"""



# Define fompParameter class to create fompParameter analogously to the ParameterDict of ODYM 
# Code and comments copied from ODYM_Classes.py

class Obj(object):
    """
    Class with the object definition for a data object (system, process, flow, ...) in ODYM
    """
    def __init__(self, Name=None, ID=None, UUID=None):
        """ Basic initialisation of Obj."""
        self.Name            = Name # object name
        self.ID              = ID   # object ID
        self.UUID            = UUID # object UUID
        self.Aspects         = {'Time': 'Model time','Cohort': 'Age-cohort','OriginProcess':'Process where flow originates','DestinationProcess':'Destination process of flow','OriginRegion': 'Region where flow originates from','DestinationRegion': 'Region where flow is bound to', 'Good': 'Process, good, or commodity', 'Material': 'Material: ore, alloy, scrap type, ...','Element': 'Chemical element' } # Define the aspects of the system variables
        self.Dimensions      = {'Time': 'Time', 'Process':'Process', 'Region': 'Region', 'Good': 'Process, good, or commodity', 'Material': 'Material: ore, alloy, scrap type, ...','Element': 'Chemical element' } # Define the dimensions of the system variables


class fompParameter(Obj):
  
    """
    Class with the definition and methods for first order model process parameters
    """
    
    def __init__(self, Name = None, ID = None, UUID = None, P_Res = None,  Indices = None, Values=None, Uncert=None, Unit = None):
        """ Basic initialisation of a parameter."""
        Obj.__init__(self, Name = Name, ID = ID, UUID = UUID) # Hand over parameters to parent class init
        self.P_Res       = P_Res   # id of process to which parameter is assigned (id: int)
        self.Indices     = Indices # String with indices as defined in IndexTable, separated by ,: 't,c,p,s,e'
        self.Values      = Values   # parameter values, np.array, multidimensional, unit is Unit
        self.Uncert      = Uncert  # uncertainty of value in %
        self.Unit        = Unit   # Unit of parameter values