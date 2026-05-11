import argparse
import sys
import os
import subprocess
import base64
import string
import importlib.resources
import re
import json

GROUP_NAME="nuam-team"
PATH_TMP_FILES="/tmp/rbac-auth"
WORKDIR=""
OBJS_CREATED=[]
CLUSTERROLE_LIST_NS="nuam-users-list-ns"

def genKubeconfigFile(model,objs_created_old):
    global WORKDIR
    global OBJS_CREATED
    global CLUSTERROLE_LIST_NS
    OBJS_CREATED=[]
    deleteOldResources(objs_created_old,model['user_id'])
    WORKDIR=creteWorkDir(str(model['user_id']))
    
    if any(p.get("type") == "Customized" for p in model["profiles_ns"]):
        roles=createRoles(model)
        createBindings(model,roles)
        rol=createCluterRoles(model)
        if rol != None:
            createBindingCluster(rol,model,"custom")

    if any(p.get("type") == "TotalAccessOverNamespace" for p in model["profiles_ns"]):
        roles=createClusterrolesallNs(model)
        createBindings(model,roles)

    if any(p.get("type") == "OnlyReadOverAllCluster" for p in model["profiles_ns"]):
        rol=createClusterroleOnlyReadOverAllCluster()
        createBindingCluster(rol,model,"only-read-all-bind")
        

    if any(p.get("type") == "SuperUsers" for p in model["profiles_ns"]):
        rol=createClusterroleSuperUsers()
        createBindingCluster(rol,model,"superuser-bind")

     # List NS - allUsers
    rol=createClusterroleListNs()
    createBindingCluster(rol,model,"list-ns")

    createCerts(model)

    csrName=createCertificateSigningRequest(model)
    kubeconfigPath=createKubeConfig(model,csrName)

    res={"kubeconfig":get_file_content(kubeconfigPath),"objs_created":OBJS_CREATED}
    #execCmd("rm -rf "+WORKDIR)
    return res

def get_api_group(apiWithVersion):
    if "/" in apiWithVersion:
        return apiWithVersion.rsplit('/', 1)[0]
    return ""

def genRolYaml(templateContent, namespacegroup, role_name):
    rules_list = []
    
    # Construimos cada bloque de recursos dentro de la secciÃ³n 'rules'
    for item in namespacegroup.get('resources', []):
        # Usamos yaml.dump para asegurar que la lista de verbs se formatee correctamente
        # o simplemente formateamos el string manualmente para mayor control
        rule_block = (
            f"- apiGroups: [\""+get_api_group(str(item['resource_api']))+"\"]\n"
            f"  resources: [\"{item['resource']}\"]\n"
            f"  verbs: {item['verbs']}"
        )
        rules_list.append(rule_block)
    
    # Unimos todas las reglas con saltos de lÃ­nea e indentaciÃ³n
    # Se aÃ±aden 2 espacios de sangrÃ­a para que queden alineados bajo 'rules:'
    rules_string = "\n".join(rules_list)
    
    # Reemplazamos los placeholders en la plantilla
    # .replace se usa para inyectar los valores dinÃ¡micos
    yaml_output = templateContent.replace("$role_name", f"\"{role_name}\"")
    yaml_output = yaml_output.replace("$namespace", namespacegroup['namespace'])
    yaml_output = yaml_output.replace("$resources", rules_string)
    
    return yaml_output


def group_permissions_by_namespace(model):
    # Dictionary to temporarily group data by namespace name
    grouped_data = {}

    for permission in model.get('permissions', []):
        
        if(permission['resource_namespaced']==False):
            continue

        namespace = permission['namespace']
        
        # Structure for the specific resource
        resource_item = {
            "resource": permission['resource'],
            "resource_namespaced":permission['resource_namespaced'],
            "resource_api":permission['resource_api'],
            "verbs": permission['verbs']
        }
        
        # Create namespace entry if it doesn't exist
        if namespace not in grouped_data:
            grouped_data[namespace] = {
                "namespace": namespace,
                "resources": []
            }
        
        # Add the resource to the corresponding namespace
        grouped_data[namespace]["resources"].append(resource_item)

    # Convert the dictionary values back into a list
    return list(grouped_data.values())

# Usage:
# result = group_permissions_by_namespace(input_object)


def execCmd(cmd):
    print("CMD: "+cmd)
    os.system(cmd)

def printStep(msg):
    print("\n---------------------------------------------------------------")
    print(msg)
    print("---------------------------------------------------------------")

def getTemplateContent(template):
    resource_path = importlib.resources.files('services.rbac.templates').joinpath(template)
    yaml_string_content = resource_path.read_text(encoding='utf-8')
    return yaml_string_content

def replace_template_regex(contTemplate, var, value):
    replacement_value_str = str(value)
    escaped_variable_name = re.escape(var)
    pattern = re.compile(
        r"\$\{" + escaped_variable_name + r"\}|" +  # For ${variable_name}
        r"\$" + escaped_variable_name + r"\b"      # For $variable_name
    )
    return pattern.sub(replacement_value_str, contTemplate)

def format_list_to_quoted_string(data_list):
    if not data_list:
        return ""
    quoted_items = [f"\"{item}\"" for item in data_list]
    result_string = ",".join(quoted_items)
    return result_string

def creteWorkDir(username):
    wd=PATH_TMP_FILES+"/"+username
    execCmd("mkdir -p "+str(wd))
    return wd

def get_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def create_file(content, path_file):
    try:
        with open(path_file, 'w', encoding='utf-8') as f:
            f.write(str(content))
        return True
    except IOError as e:
        print(f"Error writing to file {path_file}: {e}")
        return False
    except TypeError as e:
        print(f"Error: Content must be a string or convertible to a string. {e}")
        return False

def createRoles(model):
    printStep("Creating Roles...")
    roles=[]
    global OBJS_CREATED

    gn=group_permissions_by_namespace(model)
    for g in gn:
        templContent=getTemplateContent('roleTemplate.yaml')
        ns=g['namespace']
        rolename="nuam-user-"+str(model['user_id'])+"-"+str(ns)
        yamlContent=genRolYaml(templContent,g,rolename)
        
        global WORKDIR
        path=WORKDIR+"/"+rolename+".yaml"
        create_file(yamlContent,path)
        execCmd("kubectl apply -f "+path)
        OBJS_CREATED.append({'kind':'role','ns':ns,'name':rolename})
        roles.append({"role":rolename,"namespace":ns})
    return roles

def createCluterRoles(model):
    printStep("Creating ClusterRoles-Custom...")
   
    res_group = {}

    for item in model['permissions']:
        if item['resource_namespaced']==True:
            continue
        res = item['resource']
        if res not in res_group:
            res_group[res] = []
        res_group[res]=item

    if not res_group:
        return None

    ## -----
    global OBJS_CREATED
    global WORKDIR
    rolename="nuam-user-"+str(model['user_id'])+"-custom-clusterrole"

    templContent=getTemplateContent('clusterRoleCustom.yaml')
    yamlContent=genClusterRolYaml(templContent,rolename,res_group)
  
    path=WORKDIR+"/"+rolename+".yaml"
    create_file(yamlContent,path)
    execCmd("kubectl apply -f "+path)
    OBJS_CREATED.append({'kind':'clusterrole','ns':None,'name':rolename})
    rol={"role":rolename,"namespace":None}
    return rol

def genClusterRolYaml(yaml_template, role_name, data):
    # 1. Generar el bloque de rules dinámicamente
    rules_list = []
    
    for item in data.values():
       
        rule = (
            f"- apiGroups: [\"{get_api_group(str(item['resource_api']))}\"]\n"
            f"  resources: [\"{item['resource']}\"]\n"
            f"  verbs: {json.dumps(item['verbs'])}" # json.dumps formatea la lista a ["a", "b"]
        )
        rules_list.append(rule)
    
    rules_string = "\n".join(rules_list)
    
    final_yaml = yaml_template.replace("$role_name", role_name)
    final_yaml = final_yaml.replace("$resources", rules_string)
    
    return final_yaml


def createClusterrolesallNs(model):
    printStep("Creating Roles...")
    roles=[]
    global OBJS_CREATED
    for pns in model['profiles_ns']:
        if pns['type']!='TotalAccessOverNamespace':
            continue
        ns=pns['namespace']
        yamlContent=""
        rolename="nuam-user-"+str(model['user_id'])+"-"+ns+"-"+"all-ns"
        roles.append({"role":rolename,"namespace":ns})
        yamlContent=getTemplateContent('roleTemplateAllNs.yaml')
        yamlContent=replace_template_regex(yamlContent,"role_name",rolename)
        yamlContent=replace_template_regex(yamlContent,"namespace",ns)
        
        global WORKDIR
        path=WORKDIR+"/"+rolename+".yaml"
        create_file(yamlContent,path)
        execCmd("kubectl apply -f "+path)
        OBJS_CREATED.append({'kind':'role','ns':ns,'name':rolename})
    return roles

def createClusterroleOnlyReadOverAllCluster():
    printStep("Creating ClusteRole ReadOnly...")
    
    yamlContent=""
    rolename="nuam-users-only-read-all"
    yamlContent=getTemplateContent('clusterRoleReadAll.yaml')
    yamlContent=replace_template_regex(yamlContent,"role_name",rolename)
    
    global WORKDIR
    path=WORKDIR+"/"+rolename+".yaml"
    create_file(yamlContent,path)

    check_process = subprocess.run(
            ["kubectl", "get", "clusterrole", rolename],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
    if check_process.returncode != 0:
        execCmd("kubectl apply -f "+path)
    else:
        print("ClusterRole "+rolename+" exist")

    
    return {"role":rolename}

def createClusterroleSuperUsers():
    printStep("Creating ClusteRole SuperUsers...")
    
    yamlContent=""
    rolename="nuam-users-superuser"
    yamlContent=getTemplateContent('clusterRoleSuperUser.yaml')
    yamlContent=replace_template_regex(yamlContent,"role_name",rolename)
    
    global WORKDIR
    path=WORKDIR+"/"+rolename+".yaml"
    create_file(yamlContent,path)

    check_process = subprocess.run(
            ["kubectl", "get", "clusterrole", rolename],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
    if check_process.returncode != 0:
        execCmd("kubectl apply -f "+path)
    else:
        print("ClusterRole "+rolename+" exist")

    
    return {"role":rolename}

def createClusterroleListNs():
    printStep("Creating ClusteRole List Namespaces...")
    
    global CLUSTERROLE_LIST_NS
    yamlContent=""
    rolename=CLUSTERROLE_LIST_NS
    yamlContent=getTemplateContent('clusterRoleListNs.yaml')
    yamlContent=replace_template_regex(yamlContent,"role_name",rolename)
    
    global WORKDIR
    path=WORKDIR+"/"+rolename+".yaml"
    create_file(yamlContent,path)

    check_process = subprocess.run(
            ["kubectl", "get", "clusterrole", rolename],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
    if check_process.returncode != 0:
        execCmd("kubectl apply -f "+path)
    else:
        print("ClusterRole "+rolename+" exist")

    
    return {"role":rolename}

def createBindingCluster(rol,model,subfix): 
    printStep("Creating ClusterRoleBinding "+subfix+"...")
    namerb="nuam-user-"+str(model['user_id'])+"-"+subfix
    global OBJS_CREATED
    OBJS_CREATED.append({'kind':'clusterrolebinding','ns':'default','name':namerb})
    check_process = subprocess.run(
            ["kubectl", "get", "clusterrolebinding", namerb],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
    if check_process.returncode != 0:
        execCmd("kubectl create clusterrolebinding \""+namerb+"\" --clusterrole=\""+rol['role']+"\" --user=\""+model['username']+"\"")
    else:
        print("ClusterRoleBinding "+namerb+" exist")
    
def createBindings(model,roles):
    printStep("Creating Bindings...")
    global OBJS_CREATED
    for rol in roles:
        namerb=rol['role']+"-bind"
        check_process = subprocess.run(
            ["kubectl", "get", "rolebinding", namerb,"-n",rol['namespace']],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
        OBJS_CREATED.append({'kind':'rolebinding','ns':rol['namespace'],'name':namerb})
        if check_process.returncode != 0:
            execCmd("kubectl create rolebinding \""+namerb+"\" --role=\""+rol['role']+"\" --user=\""+model['username']+"\" -n "+rol['namespace']+"")
        else:
            print("RoleBinding "+namerb+" exist")

def createCerts(model):  
    global WORKDIR
    printStep("Creating certificates...") 
    execCmd("cd "+WORKDIR+" && openssl genrsa -out "+model['username']+".key 2048")      
    execCmd("cd "+WORKDIR+" && openssl req -new -key "+model['username']+".key -out "+model['username']+".csr -subj \"/CN="+model['username']+"/O="+GROUP_NAME+"\"")      
    

def createCertificateSigningRequest(model):
    global WORKDIR
    printStep("Creating CertificateSigningRequest...")
    template_content=getTemplateContent("csrTemplate.yaml")
    
    csr_name_value='nuam-user-'+str(model['user_id'])+'-csr'
    
    fileCsr=WORKDIR+"/"+model['username']+".csr"
    with open(fileCsr, 'rb') as f:
            file_bytes = f.read()
    base64_encoded_bytes = base64.b64encode(file_bytes)
    base64_string_with_wraps = base64_encoded_bytes.decode('ascii').replace('\n', '').replace('\r', '')

    final_yaml_content=replace_template_regex(template_content,"CSR_NAME",csr_name_value)
    final_yaml_content=replace_template_regex(final_yaml_content,"CSR_BASE64",base64_string_with_wraps)
    final_yaml_content=replace_template_regex(final_yaml_content,"CSR_EXP",str(60*60*24*model['cert_days']))
    
    check_process = subprocess.run(
            ["kubectl", "get", "certificatesigningrequest", csr_name_value],
            capture_output=True,
            text=True,
            check=False # No lanzar excepción si no existe
        )
    if check_process.returncode == 0:
        execCmd("kubectl delete certificatesigningrequest "+csr_name_value)
    
    fileCSR=WORKDIR+"/certificateSigningRequest.yaml"
    with open(fileCSR, 'w', encoding='utf-8') as f:
        f.write(final_yaml_content)
    execCmd("kubectl apply -f "+fileCSR)
    execCmd("kubectl certificate approve "+csr_name_value)
    global OBJS_CREATED
    OBJS_CREATED.append({'kind':'certificatesigningrequest','ns':None,'name':csr_name_value})
    return csr_name_value

def createKubeConfig(model,csr_name):
    global WORKDIR
    printStep("Creating Kubeconfig...")
    pathCrt=WORKDIR+"/"+model['username']+".crt"
    execCmd("kubectl get csr "+csr_name+" -o jsonpath='{.status.certificate}' | base64 -d > "+pathCrt)
    
    # res = subprocess.run(
    #     ["kubectl","config","view","--raw","-o","jsonpath={.clusters[0].cluster.server}"],
    #     capture_output=True,
    #     text=True,
    #     check=True
    # )
    # server=res.stdout
    server=os.getenv('RBAC_CLUSTER_URL')

    #cmd="kubectl config view -o jsonpath='{.contexts[?(@.name==\"'$(kubectl config current-context)'\")].context.cluster}'"
    #print("CMD: "+cmd)
    #with os.popen(cmd) as pipe:
    #    outc = pipe.read()
    #cluster=outc.strip()
    cluster = os.getenv('RBAC_CLUSTER_NAME')
    
    kubeconfigPath=WORKDIR+"/"+model['username']+".kubeconfig"
    
    # WHEN IS with local kbeconfig
    #caPath=WORKDIR+"/ca.crt"
    #execCmd("kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > "+caPath)

    # WHEN IS AccounService: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    ##caPath="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

    ## FROM VAR
    caPath=os.getenv('RBAC_CLUSTER_CA_CRT_PATH')

    cmd="kubectl config set-cluster "+cluster+" " \
        "--server="+server+" " \
        "--certificate-authority="+caPath+" " \
        "--embed-certs=true " \
        "--kubeconfig="+kubeconfigPath+" && "

    cmd+="kubectl config set-credentials "+model['username']+" " \
         "--client-certificate="+WORKDIR+"/"+model['username']+".crt " \
         "--client-key="+WORKDIR+"/"+model['username']+".key " \
         "--embed-certs=true " \
         "--kubeconfig="+kubeconfigPath+" && "

    cmd+="kubectl config set-context "+model['username']+"-context " \
         "--cluster="+cluster+" " \
         "--user="+model['username']+" " \
         "--kubeconfig="+kubeconfigPath+" && "

    cmd+="kubectl config use-context "+model['username']+"-context --kubeconfig="+kubeconfigPath #+" && "
    #cmd+="kubectl --kubeconfig="+kubeconfigPath+" get ns"
    
    execCmd(cmd)

    return kubeconfigPath

def deleteOldResources(objs_created_old,user_id):
    printStep("Deleting old RBAC objects...")
    cmd = "kubectl get certificatesigningrequests -o name | grep \"nuam-user-"+str(user_id)+"-\" | xargs -r kubectl delete"
    execCmd(cmd)

    cmd = "kubectl get rolebindings --all-namespaces -o custom-columns=\":metadata.namespace,:metadata.name\" | grep \"nuam-user-"+str(user_id)+"-\" | xargs -r -L 1 bash -c 'kubectl delete rolebinding $1 -n $0'"
    execCmd(cmd)

    cmd = "kubectl get roles --all-namespaces -o custom-columns=\":metadata.namespace,:metadata.name\" | grep \"nuam-user-"+str(user_id)+"-\" | xargs -r -L 1 bash -c 'kubectl delete role $1 -n $0'"
    execCmd(cmd)

    cmd = "kubectl get clusterrolebindings -o name | grep \"nuam-user-"+str(user_id)+"-\" | xargs -r kubectl delete"
    execCmd(cmd)

    cmd = "kubectl get clusterroles -o name | grep \"nuam-user-"+str(user_id)+"-\" | xargs -r kubectl delete"
    execCmd(cmd)

    # ----- OLD LOGIC ----
    # order_of_kinds = ["certificatesigningrequest","rolebinding", "role","clusterrolebinding"]
    # organized_list = []
   
    # for kind_to_collect in order_of_kinds:
    #     for item in objs_created_old:
    #         if item.get('kind') == kind_to_collect:
    #             organized_list.append(item)
    
    # for obj in organized_list:
    #     if(obj['kind']=='certificatesigningrequest'):
    #         #execCmd("kubectl delete certificatesigningrequest "+obj['name'])
    #         deleteResource('certificatesigningrequest',obj['name'],obj['ns'])
    #     if(obj['kind']=='rolebinding'):
    #         #execCmd("kubectl delete rolebinding "+obj['name']+" -n "+obj['ns'])
    #         deleteResource('rolebinding',obj['name'],obj['ns'])
    #     if(obj['kind']=='clusterrolebinding'):
    #         #execCmd("kubectl delete clusterrolebinding "+obj['name'])
    #         deleteResource('clusterrolebinding',obj['name'],obj['ns'])
    #     if(obj['kind']=='role'):
    #         #execCmd("kubectl delete role "+obj['name']+" -n "+obj['ns'])
    #         deleteResource('role',obj['name'],obj['ns'])

def deleteResource(resource_kind,resource_name,ns):
    if ns!=None:
        check_process = subprocess.run(
                ["kubectl", "get", resource_kind, resource_name,"-n",ns],
                capture_output=True,
                text=True,
                check=False # No lanzar excepción si no existe
            )
    else:
        check_process = subprocess.run(
                ["kubectl", "get", resource_kind, resource_name],
                capture_output=True,
                text=True,
                check=False # No lanzar excepción si no existe
            )

    if check_process.returncode == 0:
        if ns!=None:
            execCmd("kubectl delete "+resource_kind+" "+resource_name+" -n "+ns)
        else:
            execCmd("kubectl delete "+resource_kind+" "+resource_name)