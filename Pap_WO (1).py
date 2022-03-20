# Papyrus-WhatsOp module

def uml_xml_json_parse():
    import shutil
    import os

#Make no attention to the "r" character before the directory path's examples. It is only a python syntax so the "\" character can be taken literally.

    dir_or = input("Please enter the papyrus model directory path:\n")
# During the developement period the path used was the one from the Papyrus workspace. 
# See example below:
# r'C:\Users\rroja\workspace-papyrus\Sellar\Sellar.uml'

    dir_target = input("Please crate a directory path to parse the original model file and thus avoid any damage to the original source code.\n"+
                   "Once created please input it below:\n (Please notice that results from OpenMDAO will be stored in a folder created automatically in this directory)\n")
#As dir_target the path used was as below. It can be any preferred location.
#dir_target = r'C:\Users\rroja\Documents\ISAE\Research Project\Jupyter_Tests\Copied_uml-to-xml'

#The name of the generated copy is with a direct parse to XML file. model_XML.xml
    name='model_XML.xml'
    path = os.path.join(dir_target, name)

    shutil.copyfile(dir_or, path)
    print('xml file parsed')
    
    import json
    import xmltodict

    with open(r''+path+'') as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        xml_file.close()

    json_data = json.dumps(data_dict)
    with open("data.json", "w") as json_file:
        json_file.write(json_data)
        json_file.close()
        
    # JSON file
    
    f = open ('data.json', "r")
  
    # Reading from file
    data = json.loads(f.read())
    
    return data

def MDAO_ids_QoI(json_data):
    Parameters_dict={}
    for Requirements in json_data["xmi:XMI"]["Requirementprofile:RequirementPlus"]:
        if Requirements.get("QoI")==None or Requirements.get("@MDAO_id")==None :
            Parameters_dict[Requirements.get("@MDAO_id")]=Requirements.get("QoI")
    
    return Parameters_dict

def MDAO_ids_QoI_TS(json_data):
#Constructing the dictionary that gatter the Ids liked to MDAO with the internal papyrus @xmi:id.
    id_dict={}

    for Requirements in json_data["xmi:XMI"]["Requirementprofile:RequirementPlus"]:
        id_dict[Requirements.get("@base_NamedElement")]=Requirements.get("@MDAO_id")    

    id_dict

    #Constructing the names vs xmi:id dictionary
    name_dict={}
    for req_block in json_data["xmi:XMI"]["uml:Model"]['packagedElement']:
        if req_block.get('@xmi:type')=='uml:Package':
            if type(req_block['packagedElement']) == dict:
                name_dict[req_block['packagedElement']['@xmi:id']]=req_block['packagedElement']['@name']
            else:
                for variable in req_block['packagedElement']:
                    name_dict[variable.get('@xmi:id')]=variable.get("@name")


    #Code to automatically create the requirements dictionary (id:name)
    #The aim is to verify that the correlation between the information is correct.
    Requirements_dict = {}
    for xmi_id in id_dict:
        if xmi_id in name_dict.keys():
             Requirements_dict[id_dict[xmi_id]]=name_dict[xmi_id]

    #WE SHOULD ADDRESS ONLY THE NEEDED PARAMETERS FROM THE MDAO PROBLEM.
    #below we get all of them that have a "QoI" just to code the case when a req. has not this attribute.

    Parameters_dict = {}
    for Requirements in json_data["xmi:XMI"]["Requirementprofile:RequirementPlus"]:    
        if Requirements.get("QoI")==None:
            print("no limit value")
        else:
            if Requirements.get("@MDAO_id") in Requirements_dict.keys():
                Parameters_dict[Requirements.get("@MDAO_id")] = Requirements["QoI"]

    return Parameters_dict

def Project_Pull(pid):
    import subprocess
    
    cmd_Ppull ="wop pull --json --project-id " + str(pid)
    
    Project_Pull = subprocess.run(cmd_Ppull,capture_output=True, text=True).stdout

    #print(Project_Pull)
    #Project_Pull_str=Project_Pull[0]

    with open("Project_Pull_def.json", "w") as json_file:
        json_file.write(Project_Pull)
        json_file.close()

    import json
    # Disciplines JSON file
    p = open ('Project_Pull_def.json', "r")
    pulled_project = json.loads(p.read())

    return pulled_project

def Project_Disc_List(pulled_project):
    #Creation of the list for all the sub-analysis (Disciplines) in the whatsopt project
    Project_Disc_list = []

    #Disciplines parse
    for disciplines in pulled_project['analyses_attributes']:
        Project_Disc_list.append(disciplines)

    return Project_Disc_list

def Disciplines_in_MBSE(Project_Disc_list,Parameters_dict):
    #Discipline List append algorithm for the outputs variables that are found in the req. diagram.
    MDA_Disc_list = []

    for Disc in Project_Disc_list:
        for disc_attr in Disc["disciplines_attributes"]:
            if disc_attr['name']+'_Analysis' == Disc['name']:
                for var_attr in disc_attr['variables_attributes']:
                    if var_attr['name'] in Parameters_dict.keys() and var_attr['io_mode'] == 'out':
                        if disc_attr['name'] not in MDA_Disc_list:
                            MDA_Disc_list.append(Disc)


    return MDA_Disc_list


def MDA_json_to_push(MDA_Disc_list,Parameters_dict,Project_Disc_list):

    #Algorithm to find the disciplines whose outputs are inputs for the disciplines previoulsy found.
    #This algorithm is a loop that finishes when there are no more disciplines to be added to the list.
    
    import json
    Inputs_list = []

    while(True):

        MDA_list_size_init= len(MDA_Disc_list)

        for Disc in MDA_Disc_list:
            for disc_attr in Disc["disciplines_attributes"]:
                if disc_attr['name']+'_Analysis' == Disc['name']:
                    for var_attr in disc_attr['variables_attributes']:
                        if var_attr['io_mode'] == 'in':
                            if var_attr['name'] not in Inputs_list:
                                Inputs_list.append(var_attr['name'])

    #Inputs_list

        for Disc in Project_Disc_list:
            for disc_attr in Disc["disciplines_attributes"]:
                if disc_attr['name']+'_Analysis' == Disc['name']:
                    for var_attr in disc_attr['variables_attributes']:
                        if var_attr['io_mode'] == 'out':
                            if (var_attr['name'] in Inputs_list) and (Disc not in MDA_Disc_list):
                                MDA_Disc_list.insert(0,Disc)

        MDA_list_size_up= len(MDA_Disc_list)

        if MDA_list_size_up != MDA_list_size_init:
            MDA_list_size_init = MDA_list_size_up
            continue
        else:
            break    
            
    list_of_variables=[]

    #DRONE_MDA concatenation.

    #FOR LOOP TO RETRIEVE ALL THE DISCIPLINES THAT MIGHT HAVE AN output AS input for our original disc.

    #we start to append all "out" variables in the list without any change.
    for Disc in MDA_Disc_list:
        for disc_attr in Disc["disciplines_attributes"]:
            if disc_attr['name']+'_Analysis' == Disc['name']:
                for var_attr in disc_attr['variables_attributes']:
                    if var_attr['name'] in [v_dict['name'] for v_dict in list_of_variables]:
                        pass
                    elif var_attr['io_mode'] == 'out':
                        list_of_variables.append(var_attr)
   
    # Now we have to search all the "in" variables for each discipline leaving outside all previous "out" variables.


    for Disc in MDA_Disc_list:
        for disc_attr in Disc["disciplines_attributes"]:
            if disc_attr['name']+'_Analysis' == Disc['name']:
                for var_attr in disc_attr['variables_attributes']:
                    if var_attr['name'] in [v_dict['name'] for v_dict in list_of_variables]:
                        pass
                    else:
                        Inputs_list.append(var_attr)
                        list_of_variables.append(var_attr)

#The QoI is inserted to those variables that are found in the Parameters_dict.

    #Algorithm to modify the top level DRIVER variables initial value.
     
    init_value_template = {'init': None, 'lower': None, 'upper': None}


    for var in list_of_variables:
        if var['name'] in Parameters_dict.keys():
            init_value_template['init']=Parameters_dict.get(var['name'])
            var['parameter_attributes']=init_value_template
            init_value_template = {'init': None, 'lower': None, 'upper': None}

    #Algorithm to modify the local discipline Driver.

    init_value_template = {'init': None, 'lower': None, 'upper': None}

    for Disc in Project_Disc_list:
        for disc_attr in Disc["disciplines_attributes"]:
            if disc_attr['name'] == '__DRIVER__':
                for var_attr in disc_attr['variables_attributes']:
                    if var_attr['name'] in Parameters_dict.keys():
                        init_value_template['init']=Parameters_dict.get(var_attr['name'])
                        var_attr['parameter_attributes']=init_value_template
                        init_value_template = {'init': None, 'lower': None, 'upper': None}

    #if the variables are out in a discipline then they shall be "in" at the driver.
    # inversely, if the variables are an independent "in", then they are "out" from the driver.
                        
    #For the Driver, the io_mode needs to be switched:
    #Notice that a "new_list" is needed in order to make a "deep copy" and do not modify the original format."   
    import copy
    new_list = copy.deepcopy(list_of_variables)
    for instance in new_list:
        if instance['io_mode'] == 'out':
            instance['io_mode'] = 'in'
        elif instance['io_mode'] == 'in':
            instance['io_mode'] = 'out'
    #Insert into the json file the list of variables:
    #First we start to generate the format for the DRIVER
    
    DRONE_MDA_push = {'name': 'DRONE_Reference_push', 
             'disciplines_attributes': [{
                 'name': '__DRIVER__', 
                 'type': 'null_driver',
                 'variables_attributes':[]}]}

    DRONE_MDA_push['disciplines_attributes'][0]['variables_attributes'] = new_list
    
    #Insert the disciplines:
    for disc in MDA_Disc_list:
        DRONE_MDA_push['disciplines_attributes'].append({'name': disc['name'],'type': 'mda', 'sub_analysis_attributes': disc})

    #Convert json file into a string so as to be pushed to WhatsOpt:
    string_problem_mod = json.dumps(DRONE_MDA_push)
        
    return string_problem_mod