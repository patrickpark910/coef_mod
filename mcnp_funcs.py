'''
AUXILLIARY MCNP FUNCTIONS

Written by Patrick Park (RO, Physics '22)
ppark@reed.edu
First published: Dec. 30, 2020
Last updated: Feb. 17, 2021

__________________
Default MCNP units

Length: cm
Mass: g
Energy & Temp.: MeV
Positive density (+x): atoms/barn-cm
Negative density (-x): g/cm3
Time: shakes
(1 barn = 10e-24 cm2, 1 sh = 10e-8 sec)

'''

import os, sys, multiprocessing, glob
import numpy as np
import pandas as pd

BETA_EFF = 0.0075
CORE_POS = {'B1', 'B2', 'B3', 'B4', 'B5', 'B6',
            'C1', 'C2', 'C3', 'C4', 'C6', 'C7', 'C8', 'C10', 'C11', 'C12',
            'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12',
            'D13', 'D14', 'D15', 'D16', 'D17', 'D18',
            'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
            'E13', 'E14', 'E15', 'E16', 'E17', 'E18', 'E19', 'E20', 'E21', 'E22', 'E23', 'E24',
            'F1', 'F2', 'F3', 'F4', 'F5', 'F7', 'F8', 'F14', 'F15', 'F16', 'F17', 'F18',
            'F19', 'F20', 'F21', 'F22', 'F24', 'F26', 'F27', 'F28', 'F29', 'F30'}
CM_PER_PERCENT_HEIGHT = 0.38
FE_ID = {'B1': '7202', 'B2': '9678', 'B3': '9679', 'B4': '7946', 'B5': '7945', 'B6': '8104',
         'C1': '4086', 'C2': '4070', 'C3': '8102', 'C4': '3856', 'C6': '8103',
         'C7': '4117', 'C8': '8105', 'C10': '8736', 'C11': '8735', 'C12': '1070',
         # C12 is 10705 but only 4 digit IDs are supported here
         'D1': '3679', 'D2': '8732', 'D3': '4103', 'D4': '8734', 'D5': '3685', 'D6': '4095',
         'D7': '4104', 'D8': '4054', 'D9': '4118', 'D10': '3677', 'D11': '4131', 'D12': '4065',
         'D13': '3851', 'D14': '3866', 'D15': '8733', 'D16': '4094', 'D17': '4129', 'D18': '3874',
         'E2': '3872', 'E3': '4106', 'E4': '3671', 'E5': '4062', 'E6': '4121', 'E7': '4114',
         'E8': '4077', 'E9': '3674', 'E10': '4071', 'E11': '4122', 'E12': '4083', 'E13': '3853',
         'E14': '4134', 'E15': '4133', 'E16': '4085', 'E17': '4110', 'E18': '4055', 'E19': '3862',
         'E20': '4064', 'E21': '3858', 'E22': '4053', 'E23': '3748', 'E24': '3852',
         'F1': '4057', 'F2': '4125', 'F3': '4074', 'F4': '4069', 'F5': '4088', 'F7': '3868',
         'F8': '4120', 'F14': '3810', 'F15': '4130', 'F16': '4091', 'F17': '3673', 'F18': '3682',
         'F19': '4132', 'F20': '4046', 'F21': '3865', 'F22': '3743', 'F24': '3835', 'F26': '3676',
         'F27': '3840', 'F28': '3854', 'F29': '4049', 'F30': '4127'}
MEV_PER_KELVIN = 8.617e-11
REACT_ADD_RATE_LIMIT_DOLLARS = 0.16
RODS = ["safe", "shim", "reg"]  # must be in lower case

# From LA-UR-13-21822
U235_TEMP_DICT = {294: '92235.80c', 600: '92235.81c', 900: '92235.82c', 1200: '92235.83c',
                  2500: '92235.84c', 0.1: '92235.85c', 250: '92235.86c', 77: '92235.67c', 3000: '92235.68c'}
U238_TEMP_DICT = {294: '92238.80c', 600: '92238.81c', 900: '92238.82c', 1200: '92238.83c',
                  2500: '92238.84c', 0.1: '92238.85c', 250: '92238.86c', 77: '92238.67c', 3000: '92238.68c'}
PU239_TEMP_DICT = {294: '94239.80c', 600: '94239.81c', 900: '94239.82c', 1200: '94239.83c',
                   2500: '94239.84c', 0.1: '94239.85c', 250: '94239.86c', 77: '94239.67c', 3000: '94239.68c'}
ZR_TEMP_DICT = {294: '40000.66c', 300: '40000.56c', 587: '40000.58c'}
H1_TEMP_DICT = {294: '1001.80c', 600: '1001.81c', 900: '1001.82c', 1200: '1001.83c', 2500: '1001.84c',
                0.1: '1001.85c', 250: '1001.86c'}
HZR_TEMP_DICT = {294: 'h/zr.20t', 400: 'h/zr.21t', 500: 'h/zr.22t', 600: 'h/zr.23t', 700: 'h/zr.24t',
                 800: 'h/zr.25t', 1000: 'h/zr.26t', 1200: 'h/zr.27t'}
ZRH_TEMP_DICT = {294: 'zr/h.30t', 400: 'zr/h.31t', 500: 'zr/h.32t', 600: 'zr/h.33t', 700: 'zr/h.34t',
                 800: 'zr/h.35t', 1000: 'zr/h.36t', 1200: 'zr/h.37t'}
WATER_TEMP_DICT = {294: 'lwtr.20t', 350: 'lwtr.21t', 400: 'lwtr.22t', 450: 'lwtr.23t', 500: 'lwtr.24t',
                   550: 'lwtr.25t', 600: 'lwtr.26t', 650: 'lwtr.27t', 800: 'lwtr.28t'}

WATER_MAT_CARD = 102
FUEL_MAT_CARDS_LIST = list(FE_ID.values())
MOD_MAT_CARDS_LIST = [WATER_MAT_CARD]

def find_water_density(temp, units='Kelvin'):
    temp = float(temp)
    while units.lower() != 'c':
        if units.lower() in ['c', 'cel', 'celsius']: units = 'c'
        elif units.lower() in ['f', 'fahren', 'fahrenheit']: temp, units = ((temp-32)*0.556), 'c'
        elif units.lower() in ['k','kelvin','kelvins']: temp, units = (temp-273.15), 'c'
        elif units.lower() in ['q', 'quit', 'kill']: sys.exit()
        else:
            user_input = input("Units not recognized. Input units ['f','c','k'] or 'q' to quit: ")
            temp, units = user_input[0], user_input[1]
    # Equation for water density given temperature in C, works for 0 to 150 C at 1 atm
    # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4909168/
    density = round((999.83952+16.945176*temp-7.9870401e-3*temp**2-46.170461e-6*temp**3+105.56302e-9-280.54253e-12*temp**5)/(1+16.897850e-3*temp)/1000, 6)
    print(f"At {round(temp,6)} {units.upper()}, water density was calculated to be {density} g/cc.")
    if temp < 0 or temp > 150: print(f"--Warning. The given {temp} {units.upper()} is outside of the limits [0, 150] C of the used density equation.")
    return density

def initialize_rane():
    print(
        "\n\n      _/_/_/         _/_/_/       _/      _/     _/_/_/_/_/\n    _/     _/     _/      _/     _/_/    _/     _/\n   _/_/_/_/      _/_/_/_/_/     _/  _/  _/     _/_/_/_/_/\n  _/   _/       _/      _/     _/    _/_/     _/\n _/     _/     _/      _/     _/      _/     _/_/_/_/_/\n\n")


def find_base_file(filepath):
    # filepath: string with current folder directory name, e.g. "C:/MCNP6/facilities/reed/rodcal_mcnp"
    base_input_name = None
    while base_input_name == None:
        potential_base_input_name = input('Input base MCNP file name, including extension: ')
        if potential_base_input_name in ['q', 'quit', 'kill']:
            sys.exit()
        elif potential_base_input_name in os.listdir(f'{filepath}'):
            base_input_name = potential_base_input_name
        else:
            print(f"'{potential_base_input_name}' cannot be found. Try again, or type 'quit' to quit.")
    return base_input_name  # Name of the base input deck as string


def check_kcode(filepath, file):
    kcode_checked = False
    for line in reversed(list(open(f'{filepath}/{file}', 'r'))):
        entries = line.split(' ')
        if entries[0] == 'kcode':
            kcode_checked = True
    if kcode_checked == True:
        print(f"Checked that '{file}' contains kcode card.")
    else:
        print(
            'The kcode card could not be found in the base deck. The following input decks will be produced without a kcode card, which is necessary for keff calculations in MCNP.')

        '''
        kcode_card = input(f"The kcode card could not be found in '{base_file}'. It needs to be added if you want to calculate keff with MCNP. Would you like to add it now? ")
        if kcode_card in ['y','yes']: add_kcode()
        else: sys.exit()
        '''

    return kcode_checked  # True or False


def add_kcode():  # for now, kcode must be added manually
    pass


def check_run_mcnp():
    ask_to_run_mcnp = input("Would you like to run MCNP now? Type 'yes' to run or 'no' to quit: ")
    if ask_to_run_mcnp.lower() in ['y', 'yes']:
        return True
    elif ask_to_run_mcnp.lower() in ['n', 'no', 'q', 'quit', 'kill']:
        return False
    else:
        return check_run_mcnp()
    # Loops until it returns True or False on whether to go ahead and run MCNP.


def get_tasks():
    cores = multiprocessing.cpu_count()
    tasks = input(f"How many CPU cores should be used? Free: {cores}. Use: ")
    if not tasks:
        print(f'The number of tasks is set to the available number of cores: {cores}.')
        tasks = cores
    else:
        try:
            tasks = int(tasks)
            if tasks < 1 or tasks > multiprocessing.cpu_count():
                raise
        except:
            print(f'Number of tasks is inappropriate. Using maximum number of CPU cores: {cores}')
            tasks = cores
    return tasks  # Integer between 1 and total number of cores available.


def run_mcnp(filepath, input_deck_filepath, outputs_folder_name, tasks_to_use):
    if not os.path.isdir(f"{filepath}/{outputs_folder_name}"): os.mkdir(f"{filepath}/{outputs_folder_name}")
    if 'o_' + input_deck_filepath.split('/')[-1].split(".")[0] + '.o' not in os.listdir(
            f"{filepath}/{outputs_folder_name}"):
        print('Running MCNP...')
        output_deck_filepath = f"{filepath}/{outputs_folder_name}/o_{input_deck_filepath.split('/')[-1].split('.')[0]}"
        os.system(f"mcnp6 i={input_deck_filepath} n={output_deck_filepath}. tasks {tasks_to_use}")
    else:
        print(
            f"--This MCNP run will be skipped because the output for {input_deck_filepath.split('/')[-1]} already exists.")


def delete_files(target_folder_filepath, o=False, r=False, s=False):
    # Default args are False unless specified in command
    # NB: os.remove(f'*.r') does not work bc os.remove does not take wildcards (*)
    # if o: 
    #    for file in glob.glob(f'{target_folder_filepath}/*.o'): os.remove(file) 
    if r:
        for file in glob.glob(f'{target_folder_filepath}/*.r'): os.remove(file)
    if s:
        for file in glob.glob(f'{target_folder_filepath}/*.s'): os.remove(file)


def extract_keff(target_filepath):
    # target_outputs: list of output file names from which to read keff values
    # keff_file_name: string with desired file name of collected keffs + .csv
    get_keff, found_keff = False, False
    keff, keff_unc = None, None

    for line in open(target_filepath):
        if not found_keff:
            if line.startswith(" the estimated average keffs"):
                get_keff = True
            elif get_keff and line.startswith("       col/abs/trk len"):
                keff, keff_unc = float(line.split()[2]), float(line.split()[3])
                # print(f"{target_filepath.split('/')[-1]}: keff = {keff} +/- {keff_unc}")
                found_keff = True
    if not found_keff: print("--Error: keff cannot be found")
    return keff, keff_unc


'''
Calculates a few other rod parameters.

rho_csv_name: str, name of CSV of rho values to read from, e.g. "rho.csv"
params_csv_name: str, desired name of CSV of rod parameters, e.g. "rod_parameters.csv"

Does not return anything. Only performs file creation.
'''


def calc_params_coef(rho_csv_name, params_csv_name, module_name):
    rho_df = pd.read_csv(rho_csv_name, index_col=0)
    original_x_value = rho_df.index[abs(rho_df['rho']) == 0].tolist()[0]
    parameters = ['x', 'D x', 'D rho', 'rho unc', 'D dollars', 'dollars unc',
                  'coef rho', 'coef rho avg', 'coef rho unc', 'coef dollars', 'coef dollars avg', 'coef dollars unc']

    # Setup a dataframe to collect rho values
    # Here, 'D' stands for $\Delta$, i.e., macroscopic change
    params_df = pd.DataFrame(columns=parameters)  # use lower cases to match 'rods' def above
    params_df['x'] = rho_df.index.values.tolist()
    params_df.set_index('x', inplace=True)
    params_df['D rho'] = rho_df['rho']
    params_df['rho unc'] = rho_df['rho unc']
    params_df['D dollars'] = rho_df['dollars']
    params_df['dollars unc'] = rho_df['dollars unc']

    for x_value in params_df.index.values.tolist():
        if x_value == original_x_value:
            params_df.loc[x_value, 'D x'] = 0
            params_df.loc[x_value, 'coef rho'], params_df.loc[x_value, 'coef rho unc'], \
            params_df.loc[x_value, 'coef dollars'], params_df.loc[x_value, 'coef dollars unc'], \
            params_df.loc[x_value, 'coef rho avg'], params_df.loc[x_value, 'coef dollars avg'] = 0, 0, 0, 0, 0, 0
        else:
            if module_name == 'coef_void':
                params_df.loc[x_value, 'D x'] = -100 * round(x_value - original_x_value, 1)
            elif module_name == 'coef_pntc':
                params_df.loc[x_value, 'D x'] = round(x_value - original_x_value, 1)
            elif module_name == 'coef_mod':
                params_df.loc[x_value, 'D x'] = round(x_value - original_x_value, 1)

            params_df.loc[x_value, 'coef rho'] = params_df.loc[x_value, 'D rho'] / params_df.loc[x_value, 'D x']
            params_df.loc[x_value, 'coef dollars'] = params_df.loc[x_value, 'D dollars'] / params_df.loc[x_value, 'D x']

            if module_name == 'coef_void' or 'coef_pntc' or 'coef_mod':
                params_df.loc[x_value, 'coef rho unc'] = params_df.loc[x_value, 'rho unc'] / 100
                params_df.loc[x_value, 'coef dollars unc'] = params_df.loc[x_value, 'dollars unc'] / 100
                
        if module_name == 'coef_mod':
            params_df.loc[x_value, 'density'] = find_water_density(x_value)

    for x_value in params_df.index.values.tolist():
        x = []
        if str(module_name).lower() == 'coef_void':
            x = [i for i in params_df.index.values.tolist() if x_value <= i <= original_x_value]
        elif str(module_name).lower() == 'coef_pntc' or 'coef_mod':
            x = [i for i in params_df.index.values.tolist() if original_x_value <= i <= x_value]
        if len(x) > 1:
            y_rho = params_df.loc[x, 'coef rho'].tolist()
            params_df.loc[x_value, 'coef rho avg'] = np.mean(np.polyval(np.polyfit(x, y_rho, 1), x))
            y_dollars = params_df.loc[x, 'coef dollars'].tolist()
            params_df.loc[x_value, 'coef dollars avg'] = np.mean(np.polyval(np.polyfit(x, y_dollars, 1), x))

    print(f"\nVarious {module_name} parameters:\n{params_df}")
    params_df.to_csv(params_csv_name)


"""
prints dictionary of 'polynomial' and 'r-squared'
e.g., {'polynomial': [-0.0894, 0.234, 0.8843], 'r-squared': 0.960}
"""


def find_poly_reg(x, y, degree):
    results = {}
    coeffs = np.polyfit(x, y, degree)
    # Polynomial Coefficients
    results['polynomial'] = coeffs.tolist()
    # r-squared
    p = np.poly1d(coeffs)
    # fit values, and mean
    yhat = p(x)  # or [p(z) for z in x]
    ybar = np.sum(y) / len(y)  # or sum(y)/len(y)
    ssreg = np.sum((yhat - ybar) ** 2)  # or sum([ (yihat - ybar)**2 for yihat in yhat])
    sstot = np.sum((y - ybar) ** 2)  # or sum([ (yi - ybar)**2 for yi in y])
    results['r-squared'] = ssreg / sstot
    return results


'''
Finds the desired set of parameters to change for a given rod.

rod: str, name of rod, e.g. "shim"
height: float, percent rod height, e.g. 10
base_input_name: str, name of base deck with extension, e.g. "rc.i"
inputs_folder_name: str, name of input folder, e.g. "inputs"

Returns 'True' when new input deck is completed, or 'False' if the input deck already exists.

NB: This is the function you will change the most for use with a different facility's MCNP deck.
'''


def change_rod_height(filepath, module_name, rod_heights_dict, base_input_name, inputs_folder_name):
    if rod_heights_dict is None or len(rod_heights_dict) == 0:
        heights_list = list(input(
            'Input desired integer heights of the safe, shim, and reg rods, in order, separated by commas, e.g., 100, 20, 30: ').split(
            ","))
        rod_heights_dict = {RODS[0]: heights_list[0], RODS[1]: heights_list[1], RODS[2]: heights_list[2]}

    base_input_deck = open(base_input_name, 'r')
    # Encode new input name with rod heights: "input-a100-h20-r55.i" means safe 100, shim 20, reg 55, etc.

    new_input_name = f'{filepath}/{inputs_folder_name}/{module_name}-a{str(rod_heights_dict["safe"]).zfill(3)}-h{str(rod_heights_dict["shim"]).zfill(3)}-r{str(rod_heights_dict["reg"]).zfill(3)}.i'  # careful not to mix up ' ' and " " here

    # If the inputs folder doesn't exist, create it
    if not os.path.isdir(inputs_folder_name):
        os.mkdir(inputs_folder_name)

    # If the input deck exists, skip
    if os.path.isfile(new_input_name):
        # print(f"--The input deck '{new_input_name}' will be skipped because it already exists.")
        return False

    new_input_deck = open(new_input_name, 'w+')

    rods = [
        *rod_heights_dict]  # The * operator unpacks the dictionary, e.g., {"safe":1,shim":2,"reg":3} --> ["safe","shim","reg"], just in case it gets redefined elsewhere.

    start_marker_safe = "Safe Rod ("
    end_marker_safe = f"End of Safe Rod"
    start_marker_shim = "Shim Rod ("
    end_marker_shim = f"End of Shim Rod"
    start_marker_reg = "Reg Rod ("
    end_marker_reg = f"End of Reg Rod"

    # Indicates if we are between 'start_marker' and 'end_marker'
    inside_block_safe = False
    inside_block_shim = False
    inside_block_reg = False

    '''
    'start_marker' and 'end_marker' are what you're searching for in each 
    line of the whole input deck to indicate start and end of rod parameters. 
    Thus it needs to be unique, like "Safe Rod (0% Withdrawn)" and "End of Safe Rod".
    Make sure the input deck contains these markers EXACTLY as they are defined here,
    e.g. watch for capitalizations or extra spaces between words.
    '''

    # Now, we're reading the base input deck ('rc.i') line-by-line.
    for line in base_input_deck:

        # print("here1")
        # If we're not inside the block, just copy the line to a new file
        if inside_block_safe == False and inside_block_shim == False and inside_block_reg == False:
            # If this is the line with the 'start_marker', rewrite it to the new file with required changes
            if start_marker_safe in line:
                # print("checkA")
                inside_block_safe = True
                new_input_deck.write(f'c {"Safe"} Rod ({rod_heights_dict["safe"]}% withdrawn)\n')
                continue

            if start_marker_shim in line:
                # print("checkH")
                inside_block_shim = True
                new_input_deck.write(f'c {"Shim"} Rod ({rod_heights_dict["shim"]}% withdrawn)\n')
                continue

            if start_marker_reg in line:
                # print("checkR")
                inside_block_reg = True
                new_input_deck.write(f'c {"Reg"} Rod ({rod_heights_dict["reg"]}% withdrawn)\n')
                continue
            # print("checkSkip")
            new_input_deck.write(line)
            continue
        # print("here2")
        # Logic for what to do when we're inside the block
        if inside_block_safe == True:
            # print("check1")
            # If the line starts with a 'c'
            if line[0] == 'c':
                # If this is the line with the 'end_marker', it means we're outside the block now
                if end_marker_safe in line:
                    inside_block_safe = False
                    new_input_deck.write(line)
                    continue
                # If not, just write the line to new file
                else:
                    new_input_deck.write(line)
                    continue

            # We're now making the actual changes to the rod geometry
            if 'pz' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('pz', line, rod_heights_dict["safe"]) + '\n')
                # print(f'{new_input_name} pz change')
                continue
            if 'k/z' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('k/z', line, rod_heights_dict["safe"]) + '\n')
                # print(f'{new_input_name} k/z change')
                continue
            # If not, just write the line to the new file
            else:
                new_input_deck.write(line)
                continue

        if inside_block_shim == True:
            # If the line starts with a 'c'
            if line[0] == 'c':
                # If this is the line with the 'end_marker', it means we're outside the block now
                if end_marker_shim in line:
                    inside_block_shim = False
                    new_input_deck.write(line)
                    continue
                # If not, just write the line to new file
                else:
                    new_input_deck.write(line)
                    continue

            # We're now making the actual changes to the rod geometry
            if 'pz' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('pz', line, rod_heights_dict["shim"]) + '\n')
                # print(f'{new_input_name} pz change')
                continue
            if 'k/z' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('k/z', line, rod_heights_dict["shim"]) + '\n')
                # print(f'{new_input_name} k/z change')
                continue
            # If not, just write the line to the new file
            else:
                new_input_deck.write(line)
                continue

        if inside_block_reg == True:
            # If the line starts with a 'c'
            if line[0] == 'c':
                # If this is the line with the 'end_marker', it means we're outside the block now
                if end_marker_reg in line:
                    inside_block_reg = False
                    new_input_deck.write(line)
                    continue
                # If not, just write the line to new file
                else:
                    new_input_deck.write(line)
                    continue

            # We're now making the actual changes to the rod geometry
            if 'pz' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('pz', line, rod_heights_dict["reg"]) + '\n')
                # print(f'{new_input_name} pz change')
                continue
            if 'k/z' in line and line[0].startswith('8'):
                new_input_deck.write(edit_rod_height_code('k/z', line, rod_heights_dict["reg"]) + '\n')
                # print(f'{new_input_name} k/z change')
                continue
            # If not, just write the line to the new file
            else:
                new_input_deck.write(line)
                continue

    base_input_deck.close()
    new_input_deck.close()
    return True


def change_cell_densities(filepath, module_name, cell_densities_dict, base_input_name, inputs_folder_name):
    base_input_deck = open(base_input_name, 'r')
    # Encode new input name with rod heights: "input-a100-h20-r55.i" means safe 100, shim 20, reg 55, etc.

    new_input_name = f'{filepath}/{inputs_folder_name}/{module_name}.i'  # careful not to mix up ' ' and " " here

    # print(cell_densities_dict)

    for key, value in cell_densities_dict.items():
        new_input_name = new_input_name.split('.')[0] + f"-m{key}-{''.join(c for c in str(value) if c not in '.')}.i"

    # If the inputs folder doesn't exist, create it
    if not os.path.isdir(inputs_folder_name):
        os.mkdir(inputs_folder_name)

    # If the input deck exists, skip
    if os.path.isfile(new_input_name): return False

    new_input_deck = open(new_input_name, 'w+')

    mats_to_change = [
        *cell_densities_dict]  # The * operator unpacks the dictionary, e.g., {"safe":1,shim":2,"reg":3} --> ["safe","shim","reg"], just in case it gets redefined elsewhere.

    start_marker_cells = "Begin Cells"
    start_marker_surfs = "Begin Surfaces"

    # Indicates if we are between 'start_marker' and 'end_marker'
    inside_block_cells = False

    '''
    'start_marker' and 'end_marker' are what you're searching for in each 
    line of the whole input deck to indicate start and end of rod parameters. 
    Thus it needs to be unique, like "Safe Rod (0% Withdrawn)" and "End of Safe Rod".
    Make sure the input deck contains these markers EXACTLY as they are defined here,
    e.g. watch for capitalizations or extra spaces between words.
    '''

    # Now, we're reading the base input deck ('rc.i') line-by-line.
    for line in base_input_deck:
        # If we're not inside the block, just copy the line to a new file
        if inside_block_cells == False:
            # If this is the line with the 'start_marker', rewrite it to the new file with required changes
            if start_marker_cells in line:
                inside_block_cells = True
                new_input_deck.write(line)
                continue
            if start_marker_surfs in line:
                inside_block_cells = False
                new_input_deck.write(line)
                continue
            new_input_deck.write(line)
            continue
        # Logic for what to do when we're inside the block
        if inside_block_cells == True:
            # We're now making the actual changes to the cell density
            # 'line' already has \n at the end, but anything else doesn't
            if len(line.split()) > 0 and line.split()[0] != 'c' and line.split()[1] in mats_to_change:
                new_input_deck.write(f"c {line}")
                new_input_deck.write(
                    f"{edit_cell_density_code(line, line.split()[1], cell_densities_dict[line.split()[1]])}\n")
                continue
            elif len(line.split()) > 0 and line.split()[0] == 'c':
                new_input_deck.write(line)
                continue
            else:
                new_input_deck.write(line)
                # new_input_deck.write(f"{' '.join(line.split())}\n") # removes multi-spaces for proper MCNP syntax highlighting
                # ^that causes way too many issues for multi-line arguments
                continue

    base_input_deck.close()
    new_input_deck.close()
    return True


def change_cell_and_mat_temps(filepath, module_name, cell_temps_dict, base_input_name, inputs_folder_name):
    base_input_deck = open(base_input_name, 'r')

    # Encode new input name with rod heights: "coef_mod-temp-294.i" means moderator (water) at 294 K.
    new_input_name = f'{filepath}/{inputs_folder_name}/{module_name}-temp-{str(int(list(cell_temps_dict.values())[0])).zfill(4)}.i'
    # careful not to mix up ' ' and " " here

    # If the inputs folder doesn't exist, create it
    if not os.path.isdir(inputs_folder_name):
        os.mkdir(inputs_folder_name)

    # If the input deck exists, skip
    if os.path.isfile(new_input_name): return False # quits this function right here

    new_input_deck = open(new_input_name, 'w+')

    start_marker_cells = "Begin Cells"
    start_marker_water_cells = "Begin Core Water Cells"
    start_marker_surfs = "Begin Surfaces"
    start_marker_mats = "Begin Materials"
    end_marker_water_cells = "End Core Water Cells"
    end_marker_mats = "End Materials"

    # Indicates if we are between 'start_marker' and 'end_marker'
    inside_block_cells, inside_block_surfs, inside_block_mats, inside_block_water_cells = False, False, False, False
    mat_id = 0

    '''
    'start_marker' and 'end_marker' are what you're searching for in each 
    line of the whole input deck to indicate start and end of rod parameters. 
    Thus it needs to be unique, like "Safe Rod (0% Withdrawn)" and "End of Safe Rod".
    Make sure the input deck contains these markers EXACTLY as they are defined here,
    e.g. watch for capitalizations or extra spaces between words.
    '''

    # Now, we're reading the base input deck ('rc.i') line-by-line.
    for line in base_input_deck:
        # If this is the line with the 'start_marker', rewrite it to the new file with required changes
        if start_marker_cells in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = True, False, False, False
            new_input_deck.write(line)
            continue
        if start_marker_water_cells in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = False, True, False, False
            new_input_deck.write(line)
            continue
        if start_marker_surfs in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = False, False, True, False
            new_input_deck.write(line)
            continue
        if start_marker_mats in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = False, False, False, True
            new_input_deck.write(line)
            continue
        if end_marker_mats in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = False, False, False, False
            new_input_deck.write(line)
            continue
        if end_marker_water_cells in line:
            inside_block_cells, inside_block_water_cells, inside_block_surfs, inside_block_mats = True, False, False, False
            new_input_deck.write(line)
            continue
        if not inside_block_cells and not inside_block_surfs and not inside_block_mats and not inside_block_water_cells:
            new_input_deck.write(line)
            continue
        # Logic for what to do when we're inside the block
        if inside_block_cells:
            # We're now making the actual changes to the cell density
            # 'line' already has \n at the end, but anything else doesn't
            if len(line.split()) > 0 and line.split()[0] != 'c' and line.split()[1] in [str(m) for m in list(cell_temps_dict.keys())]:
                new_input_deck.write(f"c {line}")
                new_input_deck.write(
                    f"{edit_cell_temp_code(line, line.split()[1], cell_temps_dict[int(line.split()[1])])}\n")
                continue
            elif len(line.split()) > 0 and line.split()[0] == 'c':
                new_input_deck.write(line)
                continue
            else:
                new_input_deck.write(line)
                continue
        if inside_block_water_cells:
            if len(line.split()) > 0 and line.split()[0] != 'c' and 'imp:' in line:
                new_input_deck.write(f"c {line}")
                new_input_deck.write(line.replace('imp:n=1', f'imp:n=1 tmp={cell_temps_dict[102] * MEV_PER_KELVIN}'))
                continue
            else:
                new_input_deck.write(line)
                continue
        if inside_block_surfs:
            new_input_deck.write(line)
            continue
        if inside_block_mats:
            if len(line.split()) > 0 and line.split()[0] != 'c':
                if line.startswith('m'):
                    mat_id = int(''.join(filter(lambda i: i.isdigit(), line.split()[0])))
                if mat_id in list(cell_temps_dict.keys()):
                    # print(mat_id, mat_id in list(cell_temps_dict.keys()))
                    new_input_deck.write(f"c {line}")
                    new_input_deck.write(f"{edit_mat_temp_code(line, cell_temps_dict[mat_id])}\n")
                    # print(f"{edit_mat_temp_code(line, cell_temps_dict[mat_id])}\n")
                    continue
                else:
                    new_input_deck.write(line)
                    continue
            elif len(line.split()) > 0 and line.split()[0] == 'c':
                new_input_deck.write(line)
                continue
            else:
                new_input_deck.write(line)
                continue

    base_input_deck.close()
    new_input_deck.close()
    return True


'''
Performs the necessary changes on the values

value: str, MCNP geometry mnemonic, e.g. "pz"
line: str, line read from input deck
height: float, desired rod height, e.g. 10

NB: Bottom of rod is 5.120640 at 0% and 53.2694 at 100%. 
Use +/- 4.81488 to 'z_coordinate' for a 1% height change. 
'''


def edit_rod_height_code(geometry, line, height):
    entries = line.split()  # use empty line.split() argument to split on any whitespace

    # For loop not recommended here, as entries are formatted differently between geometries
    if geometry == 'pz':
        entries[2] = str(round(float(entries[2]) + height * CM_PER_PERCENT_HEIGHT, 5))
        new_line = '   '.join(entries[0:4]) + ' '
        new_line += ' '.join(entries[4:])

    if geometry == 'k/z':
        entries[4] = str(round(float(entries[4]) + height * CM_PER_PERCENT_HEIGHT, 5))
        new_line = '   '.join(entries[0:7]) + ' '
        new_line += ' '.join(entries[7:])

    return new_line


def get_core_pos_to_vacate(): pass


def edit_cell_density_code(line, mat_card, new_density):
    entries = line.split()  # use empty line.split() argument to split on any whitespace
    if entries[1] == str(mat_card):
        entries[2] = str(-new_density)
        new_line = ' '.join(entries)
        return new_line
    else:
        return line


def edit_cell_temp_code(line, mat_card, new_temp):
    new_temp, entries = float(new_temp), line.split()
    if entries[1] == str(mat_card):  # use empty line.split() argument to split on any whitespace
        if '$' in entries:
            entries.insert(entries.index('$'), f"tmp={new_temp * MEV_PER_KELVIN}")
            new_line = ' '.join(entries)
            return new_line
        else:
            entries.append(f"tmp={new_temp * MEV_PER_KELVIN}")
            new_line = ' '.join(entries)
            return new_line
    else:
        return line


def edit_mat_temp_code(line, new_temp):
    # print('edit mat temp code engaged')
    entries = line.split('$')[0].split()  # only counts entries before the Fortran in-line comment marker $
    for entry in entries:
        if entry in list(U235_TEMP_DICT.values()):
            # print([int(i) for i in list(U235_TEMP_DICT.keys())])
            new_temp = find_closest_value(list(U235_TEMP_DICT.keys()), new_temp)
            return line.replace(entry, U235_TEMP_DICT[new_temp]).rstrip()
        # by default, the original line has a trailing \n, so we need to get rid of it in the new_line
        # because the change_cell_and_mat_temps() function already adds a \n to each new line
        elif entry in list(U238_TEMP_DICT.values()):
            new_temp = find_closest_value(list(U238_TEMP_DICT.keys()), new_temp)
            return line.replace(entry, U238_TEMP_DICT[new_temp]).rstrip()
        elif entry in list(PU239_TEMP_DICT.values()):
            new_temp = find_closest_value(list(PU239_TEMP_DICT.keys()), new_temp)
            return line.replace(entry, PU239_TEMP_DICT[new_temp]).rstrip()
        elif entry in list(ZR_TEMP_DICT.values()):
            new_temp = find_closest_value(list(ZR_TEMP_DICT.keys()), new_temp)
            return line.replace(entry, ZR_TEMP_DICT[new_temp]).rstrip()
        elif entry in list(H1_TEMP_DICT.values()):
            new_temp = find_closest_value(list(H1_TEMP_DICT.keys()), new_temp)
            return line.replace(entry, H1_TEMP_DICT[new_temp]).rstrip()
    if entries[0].startswith('mt'):
        for i in range(0, len(entries)):
            if entries[i].startswith('h/zr'):
                new_temp = find_closest_value(list(HZR_TEMP_DICT.keys()), new_temp)
                entries[i] = HZR_TEMP_DICT[new_temp]
            elif entries[i].startswith('zr/h'):
                new_temp = find_closest_value(list(ZRH_TEMP_DICT.keys()), new_temp)
                entries[i] = ZRH_TEMP_DICT[new_temp]
        return f"{' '.join(entries)} $ {' '.join(line.split('$')[-1:1])}".rstrip()


def find_closest_value(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]


def convert_keff_to_rho(keff_csv_name, rho_csv_name):
    # Assumes the keff.csv has columns labeled "rod" and "rod unc" for keff and keff uncertainty values for a given rod
    keff_df = pd.read_csv(keff_csv_name, index_col=0)
    rods = [c for c in keff_df.columns.values.tolist() if "unc" not in c]
    heights = keff_df.index.values.tolist()

    # Setup a dataframe to collect rho values
    rho_df = pd.DataFrame(columns=keff_df.columns.values.tolist())  # use lower cases to match 'rods' def above
    rho_df["height"] = heights
    rho_df.set_index("height", inplace=True)

    '''
    ERROR PROPAGATION FORMULAE
    % Delta rho = 100* frac{k2-k1}{k2*k1}
    numerator = k2-k1
    delta num = sqrt{(delta k2)^2 + (delta k1)^2}
    denominator = k2*k1
    delta denom = k2*k1*sqrt{(frac{delta k2}{k2})^2 + (frac{delta k1}{k1})^2}
    delta % Delta rho = 100*sqrt{(frac{delta num}{num})^2 + (frac{delta denom}{denom})^2}
    '''
    for rod in rods:
        for height in heights:
            k1 = keff_df.loc[height, rod]
            k2 = keff_df.loc[heights[-1], rod]
            dk1 = keff_df.loc[height, f"{rod} unc"]
            dk2 = keff_df.loc[heights[-1], f"{rod} unc"]
            k2_minus_k1 = k2 - k1
            k2_times_k1 = k2 * k1
            d_k2_minus_k1 = np.sqrt(dk2 ** 2 + dk1 ** 2)
            d_k2_times_k1 = k2 * k1 * np.sqrt((dk2 / k2) ** 2 + (dk1 / k1) ** 2)
            rho = (k2 - k1) / (k2 * k1) * 100

            rho_df.loc[height, rod] = rho
            if k2_minus_k1 != 0:
                d_rho = rho * np.sqrt((d_k2_minus_k1 / k2_minus_k1) ** 2 + (d_k2_times_k1 / k2_times_k1) ** 2)
                rho_df.loc[height, f"{rod} unc"] = d_rho
            else:
                rho_df.loc[height, f"{rod} unc"] = 0

    print(f"\nDataframe of rho values and their uncertainties:\n{rho_df}\n")
    rho_df.to_csv(f"{rho_csv_name}")


'''
Converts a CSV of keff and uncertainty values to a CSV of rho and uncertainty values.

keff_csv_name: str, name of CSV of keff values, including extension, "keff.csv"
rho_csv_name: str, desired name of CSV of rho values, including extension, "rho.csv"

Does not return anything. Only makes the actual file changes.
'''


def convert_keff_to_rho_coef(original_x_value, keff_csv_name, rho_csv_name):
    # Assumes the keff.csv has columns labeled "rod" and "rod unc" for keff and keff uncertainty values for a given rod
    keff_df = pd.read_csv(keff_csv_name, index_col=0)
    x_values = keff_df.index.values.tolist()

    # Setup a dataframe to collect rho values
    rho_df = pd.DataFrame(columns=keff_df.columns.values.tolist())  # use lower cases to match 'rods' def above
    rho_df.columns = ['rho', 'rho unc']
    rho_df["x"] = x_values
    rho_df.set_index("x", inplace=True)

    '''
    ERROR PROPAGATION FORMULAE
    % Delta rho = 100* frac{k2-k1}{k2*k1}
    numerator = k2-k1
    delta num = sqrt{(delta k2)^2 + (delta k1)^2}
    denominator = k2*k1
    delta denom = k2*k1*sqrt{(frac{delta k2}{k2})^2 + (frac{delta k1}{k1})^2}
    delta % Delta rho = 100*sqrt{(frac{delta num}{num})^2 + (frac{delta denom}{denom})^2}
    '''

    for x_value in x_values:
        k1 = keff_df.loc[x_value, 'keff']
        k2 = keff_df.loc[original_x_value, 'keff']
        dk1 = keff_df.loc[x_value, 'keff unc']
        dk2 = keff_df.loc[original_x_value, 'keff unc']
        k2_minus_k1 = k2 - k1
        k2_times_k1 = k2 * k1
        d_k2_minus_k1 = np.sqrt(dk2 ** 2 + dk1 ** 2)
        d_k2_times_k1 = k2 * k1 * np.sqrt((dk2 / k2) ** 2 + (dk1 / k1) ** 2)
        rho = -(k2 - k1) / (k2 * k1) * 100
        dollars = 0.01 * rho / BETA_EFF

        rho_df.loc[x_value, 'rho'] = rho
        rho_df.loc[x_value, 'dollars'] = dollars
        # while the 'dollars' (and 'dollars unc') columns are not in the original rho_df definition,
        # simply defining a value inside it automatically adds the column
        if k2_minus_k1 != 0:
            rho_unc = rho * np.sqrt((d_k2_minus_k1 / k2_minus_k1) ** 2 + (d_k2_times_k1 / k2_times_k1) ** 2)
            dollars_unc = rho_unc / 100 / BETA_EFF
            rho_df.loc[x_value, 'rho unc'], rho_df.loc[x_value, 'dollars unc'] = rho_unc, dollars_unc
        else:
            rho_df.loc[x_value, 'rho unc'], rho_df.loc[x_value, 'dollars unc'] = 0, 0

    print(f"\nDataframe of rho values and their uncertainties:\n{rho_df}\n")
    rho_df.to_csv(f"{rho_csv_name}")
