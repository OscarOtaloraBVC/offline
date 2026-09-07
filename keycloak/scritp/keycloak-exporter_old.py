#!/usr/bin/env python3
"""
Keycloak Realm Exporter - Exporta todos los reinos de Keycloak sin detener servicios
Uso: python3 keycloak-exporter.py
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

class KeycloakExporter:
    def __init__(self, namespace: str = "keycloak", pod: str = "keycloak-nuam-0", 
                user: str = "ootalora", password: str = "Abcd123456"):
        self.namespace = namespace
        self.pod = pod
        self.user = user
        self.password = password
        self.temp_dir = "/tmp/keycloak-export"
        self.local_dir = f"keycloak-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.realms_to_exclude = ["master", "nuam"]
        
    def execute_in_pod(self, command: str) -> tuple:
        """Ejecuta un comando dentro del pod"""
        full_cmd = ["kubectl", "exec", "-n", self.namespace, self.pod, "--", "/bin/bash", "-c", command]
        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, check=False)
            # El mensaje "Defaulted container" y "Logging into" pueden estar en stderr
            # pero no son errores reales
            stdout = result.stdout
            stderr = result.stderr
            
            # Verificar si hay errores reales (no mensajes informativos)
            error_lines = []
            for line in stderr.split('\n'):
                if 'Defaulted container' not in line and 'Logging into' not in line:
                    if line.strip():
                        error_lines.append(line)
            
            stderr_clean = '\n'.join(error_lines)
            
            # Si stdout está vacío pero stderr tiene "Logging into", es éxito
            if not stdout and "Logging into" in result.stderr:
                stdout = result.stderr
            
            return stdout, stderr_clean
        except Exception as e:
            return "", str(e)
    
    def setup_credentials(self) -> bool:
        """Configura las credenciales de kcadm.sh"""
        print("🔑 Configurando credenciales...")
        cmd = f"cd /opt/keycloak/bin && ./kcadm.sh config credentials --server http://localhost:8080 --realm master --user {self.user} --password {self.password} 2>&1"
        stdout, stderr = self.execute_in_pod(cmd)
        
        # Verificar si hay "Logging into" en cualquier parte de la salida
        combined = stdout + stderr
        if "Logging into" in combined:
            print("✅ Credenciales configuradas")
            return True
        print(f"❌ Error: {stderr}")
        return False
    
    def list_realms(self) -> List[str]:
        """Lista todos los reinos"""
        print("📋 Obteniendo lista de reinos...")
        cmd = "cd /opt/keycloak/bin && ./kcadm.sh get realms --fields realm 2>&1 | grep -o '\"realm\" : \"[^\"]*\"' | cut -d'\"' -f4"
        stdout, _ = self.execute_in_pod(cmd)
        
        # Limpiar la salida (puede incluir mensajes de logging)
        lines = stdout.split('\n')
        realms = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('{'):
                realms.append(line)
        
        filtered = [r for r in realms if r not in self.realms_to_exclude]
        
        print(f"✅ Encontrados {len(realms)} reinos totales")
        if filtered:
            print(f"📌 Reinos a exportar ({len(filtered)}): {', '.join(filtered)}")
        else:
            print(f"📌 No hay reinos para exportar (excluyendo master y nuam)")
        
        return filtered
    
    def export_component(self, realm: str, component: str) -> bool:
        """Exporta un componente específico"""
        commands = {
            "realms": f"cd /opt/keycloak/bin && ./kcadm.sh get realms/{realm} 2>&1",
            "users": f"cd /opt/keycloak/bin && ./kcadm.sh get users -r {realm} 2>&1",
            "clients": f"cd /opt/keycloak/bin && ./kcadm.sh get clients -r {realm} 2>&1",
            "roles": f"cd /opt/keycloak/bin && ./kcadm.sh get roles -r {realm} 2>&1",
            "groups": f"cd /opt/keycloak/bin && ./kcadm.sh get groups -r {realm} 2>&1",
            "client-scopes": f"cd /opt/keycloak/bin && ./kcadm.sh get client-scopes -r {realm} 2>&1",
            "identity-providers": f"cd /opt/keycloak/bin && ./kcadm.sh get identity-provider/instances -r {realm} 2>&1"
        }
        
        if component not in commands:
            return False
        
        target_dir = f"{self.temp_dir}/{realm}"
        self.execute_in_pod(f"mkdir -p {target_dir}")
        
        stdout, _ = self.execute_in_pod(commands[component])
        
        # Verificar que no sea un error
        if stdout and not stdout.startswith("Error") and not stdout.startswith("Error:"):
            filename = f"{target_dir}/{component}.json"
            # Escapar el contenido para heredoc
            escaped = stdout.replace("'", "'\\''")
            self.execute_in_pod(f"cat > {filename} << 'EOF'\n{escaped}\nEOF")
            print(f"  ✅ {component} exportado")
            return True
        else:
            if stdout:
                print(f"  ⚠️ {component}: {stdout[:100]}...")
        return False
    
    def export_realm(self, realm: str) -> Dict[str, bool]:
        """Exporta todos los componentes de un reino"""
        print(f"\n📦 Exportando reino: {realm}")
        print("-" * 50)
        
        components = ["realms", "users", "clients", "roles", "groups", "client-scopes", "identity-providers"]
        results = {}
        
        for comp in components:
            results[comp] = self.export_component(realm, comp)
        
        success = sum(1 for v in results.values() if v)
        print(f"✅ Exportados {success}/{len(components)} componentes")
        return results
    
    def copy_files(self, realm: str) -> bool:
        """Copia archivos del pod a local"""
        source = f"{self.temp_dir}/{realm}"
        target = f"{self.local_dir}/{realm}"
        os.makedirs(target, exist_ok=True)
        
        cmd = f"ls -1 {source}/*.json 2>/dev/null || echo ''"
        stdout, _ = self.execute_in_pod(cmd)
        files = [f.strip() for f in stdout.split('\n') if f.strip()]
        
        if not files:
            print(f"⚠️ No hay archivos para copiar de {realm}")
            return False
        
        print(f"📥 Copiando {len(files)} archivos de {realm}...")
        for file in files:
            filename = os.path.basename(file)
            local_file = os.path.join(target, filename)
            cmd = ["kubectl", "cp", "-n", self.namespace, f"{self.pod}:{file}", local_file]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✅ {filename}")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Error en {filename}: {e}")
                return False
        return True
    
    def create_readme(self, realms: List[str]):
        """Crea un README"""
        readme_file = os.path.join(self.local_dir, "README.md")
        
        lines = []
        lines.append("# Exportación de Keycloak")
        lines.append("")
        lines.append("## Información")
        lines.append("- Fecha: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        lines.append("- Namespace: " + self.namespace)
        lines.append("- Pod: " + self.pod)
        lines.append("- Usuario: " + self.user)
        lines.append("- Reinos excluidos: master, nuam")
        lines.append("- Reinos exportados: " + (', '.join(realms) if realms else 'Ninguno'))
        lines.append("")
        lines.append("## Estructura de archivos")
        lines.append("```")
        lines.append(self.local_dir + "/")
        lines.append("├── export-summary.json")
        lines.append("├── import-realms.sh")
        lines.append("├── README.md")
        lines.append("└── [reino]/")
        lines.append("    ├── realms.json")
        lines.append("    ├── users.json")
        lines.append("    ├── clients.json")
        lines.append("    ├── roles.json")
        lines.append("    ├── groups.json")
        lines.append("    ├── client-scopes.json")
        lines.append("    └── identity-providers.json")
        lines.append("```")
        lines.append("")
        lines.append("## Como importar")
        lines.append("")
        lines.append("### 1. Copiar al pod destino:")
        lines.append("```bash")
        lines.append("kubectl cp " + self.local_dir + " -n <namespace> <pod>:/tmp/keycloak-import")
        lines.append("```")
        lines.append("")
        lines.append("### 2. Ejecutar importación:")
        lines.append("```bash")
        lines.append("kubectl exec -it -n <namespace> <pod> -- /bin/bash -c \"")
        lines.append("cd /opt/keycloak/bin && \\")
        lines.append("./kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin && \\")
        lines.append("bash /tmp/keycloak-import/import-realms.sh")
        lines.append("\"")
        lines.append("```")
        lines.append("")
        lines.append("## Notas importantes")
        lines.append("- Los usuarios se importan sin contraseñas")
        lines.append("- Los secretos de clientes pueden cambiar")
        lines.append("- Verificar IDs para evitar conflictos")
        
        content = '\n'.join(lines)
        
        with open(readme_file, 'w') as f:
            f.write(content)
        print(f"📖 README creado")
    
    def create_import_script(self, realms: List[str]):
        """Crea script de importación"""
        import_script = os.path.join(self.local_dir, "import-realms.sh")
        
        lines = []
        lines.append("#!/bin/bash")
        lines.append("echo \"=========================================\"")
        lines.append("echo \"IMPORTANDO REINOS EN KEYCLOAK\"")
        lines.append("echo \"=========================================\"")
        lines.append("")
        lines.append("cd /opt/keycloak/bin")
        lines.append("./kcadm.sh config credentials --server http://localhost:8080 --realm master --user ADMIN_USER --password ADMIN_PASSWORD")
        lines.append("")
        
        if not realms:
            lines.append("echo \"⚠️ No hay reinos para importar\"")
        else:
            for realm in realms:
                lines.append("")
                lines.append("echo \"\"")
                lines.append("echo \"📦 Importando reino: " + realm + "\"")
                lines.append("echo \"-----------------------------------------\"")
                lines.append("")
                lines.append("if [ -f \"/tmp/keycloak-import/" + realm + "/realms.json\" ]; then")
                lines.append("    echo \"  Importando realm...\"")
                lines.append("    ./kcadm.sh create realms -f /tmp/keycloak-import/" + realm + "/realms.json")
                lines.append("fi")
                lines.append("")
                lines.append("if [ -f \"/tmp/keycloak-import/" + realm + "/clients.json\" ]; then")
                lines.append("    echo \"  Importando clientes...\"")
                lines.append("    ./kcadm.sh create clients -r " + realm + " -f /tmp/keycloak-import/" + realm + "/clients.json")
                lines.append("fi")
                lines.append("")
                lines.append("if [ -f \"/tmp/keycloak-import/" + realm + "/roles.json\" ]; then")
                lines.append("    echo \"  Importando roles...\"")
                lines.append("    ./kcadm.sh create roles -r " + realm + " -f /tmp/keycloak-import/" + realm + "/roles.json")
                lines.append("fi")
                lines.append("")
                lines.append("if [ -f \"/tmp/keycloak-import/" + realm + "/users.json\" ]; then")
                lines.append("    echo \"  Importando usuarios...\"")
                lines.append("    ./kcadm.sh create users -r " + realm + " -f /tmp/keycloak-import/" + realm + "/users.json")
                lines.append("fi")
                lines.append("")
                lines.append("if [ -f \"/tmp/keycloak-import/" + realm + "/groups.json\" ]; then")
                lines.append("    echo \"  Importando grupos...\"")
                lines.append("    ./kcadm.sh create groups -r " + realm + " -f /tmp/keycloak-import/" + realm + "/groups.json")
                lines.append("fi")
                lines.append("")
                lines.append("echo \"✅ " + realm + " importado\"")
        
        lines.append("")
        lines.append("echo \"\"")
        lines.append("echo \"=========================================\"")
        lines.append("echo \"IMPORTACIÓN COMPLETADA\"")
        lines.append("echo \"=========================================\"")
        
        content = '\n'.join(lines)
        
        with open(import_script, 'w') as f:
            f.write(content)
        os.chmod(import_script, 0o755)
        print(f"📝 Script de importación creado")
    
    def create_summary(self, results: Dict[str, Any]):
        """Crea resumen JSON"""
        summary_file = os.path.join(self.local_dir, "export-summary.json")
        summary = {
            "export_date": datetime.now().isoformat(),
            "namespace": self.namespace,
            "pod": self.pod,
            "user": self.user,
            "total_realms": len(results),
            "realms": results
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📄 Resumen guardado")
    
    def export_all(self):
        """Ejecuta la exportación completa"""
        print("🚀 Iniciando exportación de Keycloak")
        print("=" * 60)
        print(f"📌 Namespace: {self.namespace}")
        print(f"📌 Pod: {self.pod}")
        print(f"📌 Usuario: {self.user}")
        print("=" * 60)
        
        if not self.setup_credentials():
            print("❌ No se pudieron configurar las credenciales")
            sys.exit(1)
        
        realms = self.list_realms()
        if not realms:
            print("⚠️ No hay reinos para exportar (excluyendo master y nuam)")
            # Crear directorio vacío con README explicativo
            os.makedirs(self.local_dir, exist_ok=True)
            self.create_readme([])
            self.create_import_script([])
            print(f"\n📁 Directorio local: {self.local_dir}")
            return
        
        self.execute_in_pod(f"mkdir -p {self.temp_dir}")
        os.makedirs(self.local_dir, exist_ok=True)
        print(f"\n📁 Directorio local: {self.local_dir}")
        
        results = {}
        for realm in realms:
            results[realm] = self.export_realm(realm)
            self.copy_files(realm)
        
        self.create_summary(results)
        self.create_import_script(realms)
        self.create_readme(realms)
        
        self.execute_in_pod(f"rm -rf {self.temp_dir}")
        
        print("\n" + "=" * 60)
        print("✅ EXPORTACIÓN COMPLETADA")
        print("=" * 60)
        print(f"📁 Archivos en: {self.local_dir}")
        print(f"📊 Reinos exportados: {len(realms)}")
        
        for realm, comps in results.items():
            success = sum(1 for v in comps.values() if v)
            print(f"  ✅ {realm}: {success}/7 componentes")

def main():
    exporter = KeycloakExporter(
        namespace="keycloak",
        pod="keycloak-nuam-0",
        user="ootalora",
        password="Abcd123456"
    )
    exporter.export_all()

if __name__ == "__main__":
    main()