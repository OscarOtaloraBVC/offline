from services.rbac.rbac_core import genKubeconfigFile
from services.user_service import get_user,list_namespace_names,create_user_certs,get_last_user_cert,enable_user
from services.profile_service import get_user_aggregated_permissions,get_permissions_list
from models.user_certs_model import UserCertCreate
import ast

def genKubeconfig(user_id):
    model=getModel(user_id)

    if model['model']==None:
        return {'msg':model['msg'],'kubeconfig':None,"successful":False}

    user=get_user(user_id)
    objs_created=[]
    cert=get_last_user_cert(user_id)
    if(cert!=None):
        objs_created= ast.literal_eval(cert['objs_created'].replace("'","\""))

    kc=genKubeconfigFile(model['model'],objs_created)
    
    uc={}
    uc['user_id']=int(user_id)
    uc['kubeconfig_content']=str(kc['kubeconfig'])
    uc['objs_created']=str(kc['objs_created'])
    create_user_certs(UserCertCreate(**uc))

    #Enable on BD
    enable_user(user_id)

    return  {'msg':model['msg'],'kubeconfig':kc['kubeconfig'],"successful":True}

def getLastKibeconfig(user_id):
    uc=get_last_user_cert(user_id)
    if uc==None:
        return genKubeconfig(user_id)
    else:
        return {'msg':'Old kubeconfig, id:'+str(uc['id']),'kubeconfig':uc['kubeconfig_content']}

def getModel(user_id):

    user = get_user(user_id)

    # The user object now contains 'assignments' which is a list of profile-namespace pairs.
    if not user or not user.assignments:
        username = user.username if user else f"ID {user_id}"
        return {"msg": f"User '{username}' requires at least one profile and namespace assignment.", "model": None}

    # Check if any assigned 'Customized' profile is empty
    customized_profiles = {
        assignment.profile.id: assignment.profile.name
        for assignment in user.assignments
        if assignment.profile.type == "Customized"
    }

    for profile_id, profile_name in customized_profiles.items():
        if not get_permissions_list(profile_id):
            return {"msg": f"Profile '{profile_name}' is of type 'Customized' but has no permissions defined.", "model": None}

    permissions = get_user_aggregated_permissions(user_id)

    # The new model structure combines profile types and namespaces.
    profiles_ns = [
        {"type": assignment.profile.type, "namespace": assignment.namespace,"profile_id":assignment.profile.id}
        for assignment in user.assignments
    ]

    model = {"user_id": user.id, "username": user.username, "cert_days": user.cert_days, "permissions": permissions, "profiles_ns": profiles_ns}
    return {'msg': '', 'model': model}
