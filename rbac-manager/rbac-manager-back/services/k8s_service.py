import subprocess
from services.rbac.rbac_service import genKubeconfig,getLastKibeconfig

def get_kubernetes_namespaces():
    try:
        # Run the kubectl command
        result = subprocess.run(
            ['kubectl', 'get', 'ns', '-o', 'jsonpath={.items[*].metadata.name}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # Split the result and convert each to a dict
        namespaces = result.stdout.strip().split()
        return namespaces
        #return [{"namespace": ns} for ns in namespaces]

    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl: {e.stderr}")
        return []


def get_kubernetes_apiresources():
    try:
        result = subprocess.run(
            ['kubectl', 'api-resources'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        lines = result.stdout.strip().splitlines()
        if not lines:
            return []

        # Extract header to get column positions
        header = lines[0]
        name_idx = header.find("NAME")
        shortnames_idx = header.find("SHORTNAMES")
        apiversion_idx = header.find("APIVERSION")
        namespaced_idx = header.find("NAMESPACED")
        kind_idx = header.find("KIND")

        resources = []

        i=1
        for line in lines[1:]:
            # Use slicing to extract columns by position
            name = line[name_idx:shortnames_idx].strip()
            # shortnames = line[shortnames_idx:apiversion_idx].strip()  # optional
            apiversion = line[apiversion_idx:namespaced_idx].strip()
            namespaced_str = line[namespaced_idx:kind_idx].strip().lower()
            namespaced = namespaced_str == "true"

            resources.append({
                "id":i,
                "resource": name,
                "namespaced": namespaced,
                "apiversion": apiversion
            })
            i+=1

        return resources

    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl: {e.stderr}")
        return []

def generate_kubeconfig(user_id):
    return genKubeconfig(user_id)

def get_last_kubeconfig(user_id):
    return getLastKibeconfig(user_id)