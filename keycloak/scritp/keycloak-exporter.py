#!/usr/bin/env python3
"""
Keycloak Realm Exporter - Exporta todos los reinos de Keycloak sin detener servicios
Uso: python3 keycloak-exporter.py
"""

import subprocess
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

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
        self.server_url = "http://localhost:8080"
        self.kcadm_path = "/opt/keycloak/bin/kcadm.sh"
        
    def execute_kubectl(self, command: str, interactive: bool = False) -> tuple:
        """Ejecuta un comando dentro del pod usando kubectl"""
        if interactive:
            # Para comandos interactivos
            full_cmd = ["kubectl", "exec", "-it", "-n", self.namespace, self.pod, "--", "/bin/bash", "-c", command]
        else:
            full_cmd = ["kubectl", "exec", "-n", self.namespace, self.pod, "--", "/bin/bash", "-c", command]
        
        try:
            if interactive:
                result = subprocess.run(full_cmd, capture_output=False, text=True, check=False)
                return "", ""
            else:
                result = subprocess.run(full_cmd, capture_output=True, text=True, check=False)
                # Filtrar mensajes de kubectl
                stderr_clean = self._clean_stderr(result.stderr)
                return result.stdout, stderr_clean
        except Exception as e:
            return "", str(e)
    
    def _clean_stderr(self, stderr: str) -> str:
        """Limpia los mensajes de stderr de kubectl"""
        if not stderr:
            return ""
        
        # Filtrar mensajes informativos de kubectl
        lines_to_keep = []
        for line in stderr.split('\n'):
            if ('Defaulted container' not in line and 
                'Logging into' not in line and
                'Using' not in line and
                line.strip()):
                lines_to_keep.append(line)
        
        return '\n'.join(lines_to_keep)
    
    def configure_credentials(self) -> bool:
        """Configura las credenciales usando kcadm.sh"""
        print("🔑 Configurando credenciales...")
        
        cmd = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh config credentials --server {self.server_url} --realm master --user {self.user} --password {self.password}"
        stdout, stderr = self.execute_kubectl(cmd)
        
        if not stderr or "error" in stderr.lower():
            print("✅ Credenciales configuradas correctamente")
            return True
        else:
            print(f"❌ Error configurando credenciales: {stderr}")
            return False
    
    def get_realms(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de todos los reinos usando kcadm.sh"""
        print("📋 Obteniendo lista de reinos...")
        
        cmd = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh get realms --fields realm,displayName,enabled"
        stdout, stderr = self.execute_kubectl(cmd)
        
        if stderr and "error" in stderr.lower():
            print(f"❌ Error obteniendo reinos: {stderr}")
            return []
        
        try:
            # Parsear la salida JSON
            realms_data = json.loads(stdout) if stdout else []
            
            # Filtrar reinos excluidos y los que no son válidos
            filtered_realms = []
            for realm in realms_data:
                realm_name = realm.get('realm', '')
                if realm_name and realm_name not in self.realms_to_exclude:
                    # Verificar que el reino esté habilitado
                    if realm.get('enabled', False):
                        filtered_realms.append(realm)
                    else:
                        print(f"⚠️ Reino '{realm_name}' está deshabilitado, omitiendo...")
            
            print(f"✅ Encontrados {len(realms_data)} reinos totales")
            if filtered_realms:
                realm_names = [r['realm'] for r in filtered_realms]
                print(f"📌 Reinos a exportar ({len(filtered_realms)}): {', '.join(realm_names)}")
            else:
                print(f"📌 No hay reinos para exportar (excluyendo: {', '.join(self.realms_to_exclude)})")
            
            return filtered_realms
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"Salida recibida: {stdout[:200]}...")
            return []
    
    def export_realm_with_kcadm(self, realm: str, realm_info: Dict[str, Any]) -> bool:
        """Exporta un reino completo usando kcadm.sh"""
        print(f"\n📦 Exportando reino: {realm}")
        print("-" * 60)
        
        # Crear directorio para el reino
        realm_dir = f"{self.temp_dir}/{realm}"
        self.execute_kubectl(f"mkdir -p {realm_dir}")
        
        # Exportar metadatos del reino
        print(f"📝 Exportando metadatos del reino...")
        cmd = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh get realms/{realm}"
        stdout, _ = self.execute_kubectl(cmd)
        if stdout:
            self._save_content_in_pod(realm_dir, "realm.json", stdout)
            print("  ✅ Metadatos exportados")
        else:
            print("  ⚠️ No se pudieron exportar metadatos")
        
        # Componentes a exportar
        components = [
            ("users", "users"),
            ("clients", "clients"),
            ("roles", "roles"),
            ("groups", "groups"),
            ("client-scopes", "client-scopes"),
            ("identity-provider/instances", "identity-providers"),
        ]
        
        success_count = 0
        total_components = len(components) + 1  # +1 por el realm
        
        for endpoint, filename in components:
            print(f"📝 Exportando {filename}...")
            cmd = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh get {endpoint} -r {realm}"
            stdout, stderr = self.execute_kubectl(cmd)
            
            if stdout:
                # Validar que sea JSON válido
                try:
                    data = json.loads(stdout)
                    if isinstance(data, list) and len(data) == 0:
                        print(f"  ⚠️ {filename} está vacío")
                        self._save_content_in_pod(realm_dir, f"{filename}.json", "[]")
                    elif isinstance(data, dict) and len(data) == 0:
                        print(f"  ⚠️ {filename} está vacío")
                        self._save_content_in_pod(realm_dir, f"{filename}.json", "{}")
                    else:
                        self._save_content_in_pod(realm_dir, f"{filename}.json", stdout)
                        print(f"  ✅ {filename} exportado ({len(data)} elementos)")
                    success_count += 1
                except json.JSONDecodeError:
                    print(f"  ⚠️ {filename} - formato inválido, guardando como texto")
                    self._save_content_in_pod(realm_dir, f"{filename}.txt", stdout)
                    success_count += 1
            else:
                # Crear archivo vacío
                self._save_content_in_pod(realm_dir, f"{filename}.json", "[]")
                print(f"  ⚠️ {filename} vacío o sin datos")
                success_count += 1
        
        # Exportar client-scopes adicionales si existen
        print(f"📝 Exportando client-scopes detallados...")
        cmd = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh get client-scopes -r {realm}"
        stdout, _ = self.execute_kubectl(cmd)
        if stdout:
            try:
                data = json.loads(stdout)
                if data and len(data) > 0:
                    # Guardar lista completa de client-scopes
                    self._save_content_in_pod(realm_dir, "client-scopes-full.json", stdout)
                    print(f"  ✅ client-scopes detallados exportados ({len(data)} elementos)")
                    
                    # Exportar cada client-scope individualmente
                    scope_dir = f"{realm_dir}/client-scopes"
                    self.execute_kubectl(f"mkdir -p {scope_dir}")
                    
                    for scope in data:
                        scope_name = scope.get('name', 'unknown')
                        scope_id = scope.get('id', '')
                        if scope_id:
                            cmd_detail = f"cd {os.path.dirname(self.kcadm_path)} && ./kcadm.sh get client-scopes/{scope_id} -r {realm}"
                            detail_stdout, _ = self.execute_kubectl(cmd_detail)
                            if detail_stdout:
                                safe_name = scope_name.replace('/', '_').replace(' ', '_')
                                self._save_content_in_pod(scope_dir, f"{safe_name}.json", detail_stdout)
                                print(f"    ✅ {scope_name} exportado")
            except json.JSONDecodeError:
                pass
        
        return success_count > 0
    
    def _save_content_in_pod(self, directory: str, filename: str, content: str):
        """Guarda contenido en un archivo dentro del pod"""
        # Escapar contenido para evitar problemas con caracteres especiales
        escaped_content = content.replace("'", "'\\''").replace('"', '\\"')
        cmd = f"echo '{escaped_content}' > {directory}/{filename}"
        self.execute_kubectl(cmd)
    
    def copy_files_from_pod(self, realm: str) -> bool:
        """Copia los archivos exportados del pod al sistema local"""
        source = f"{self.temp_dir}/{realm}"
        target = f"{self.local_dir}/{realm}"
        os.makedirs(target, exist_ok=True)
        
        print(f"📥 Copiando archivos de {realm}...")
        
        # Obtener lista de archivos
        cmd = f"find {source} -type f -name '*.json' -o -name '*.txt'"
        stdout, _ = self.execute_kubectl(cmd)
        files = [f.strip() for f in stdout.split('\n') if f.strip()]
        
        if not files:
            print(f"⚠️ No hay archivos para copiar de {realm}")
            return False
        
        success = True
        for file_path in files:
            # Determinar la ruta relativa para mantener la estructura
            rel_path = file_path.replace(f"{self.temp_dir}/{realm}/", "")
            local_file = os.path.join(target, rel_path)
            
            # Crear directorio si es necesario
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            
            # Copiar archivo
            cmd = f"cat {file_path}"
            content, _ = self.execute_kubectl(cmd)
            
            if content:
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ {rel_path}")
            else:
                print(f"  ⚠️ {rel_path} - archivo vacío")
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write('[]')
        
        return success
    
    def create_import_script(self, realms: List[str]):
        """Crea un script de importación para cada reino"""
        import_script = os.path.join(self.local_dir, "import-realms.sh")
        
        lines = [
            "#!/bin/bash",
            "# Script de importación para Keycloak",
            "# Generado automáticamente el: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "",
            "echo \"=========================================\"",
            "echo \"IMPORTANDO REINOS EN KEYCLOAK\"",
            "echo \"=========================================\"",
            "",
            "cd /opt/keycloak/bin",
            "",
            "# Configurar credenciales",
            "echo \"Configurando credenciales...\"",
            "./kcadm.sh config credentials --server http://localhost:8080 --realm master --user ADMIN_USER --password ADMIN_PASSWORD",
            "echo \"Credenciales configuradas\"",
            "",
            "# Función para importar reino",
            "import_realm() {",
            "    local realm=$1",
            "    echo \"\"",
            "    echo \"📦 Importando reino: $realm\"",
            "    echo \"-----------------------------------------\"",
            "    ",
            "    # Verificar si el reino ya existe",
            "    if ./kcadm.sh get realms/$realm > /dev/null 2>&1; then",
            "        echo \"⚠️ El reino $realm ya existe, omitiendo...\"",
            "        return 0",
            "    fi",
            "    ",
            "    # Importar metadatos del reino",
            "    if [ -f \"/tmp/keycloak-import/$realm/realm.json\" ]; then",
            "        echo \"  Importando metadatos del reino...\"",
            "        ./kcadm.sh create realms -f /tmp/keycloak-import/$realm/realm.json",
            "    fi",
            "    ",
            "    # Importar componentes",
            "    for component in clients roles groups client-scopes; do",
            "        if [ -f \"/tmp/keycloak-import/$realm/$component.json\" ]; then",
            "            echo \"  Importando $component...\"",
            "            ./kcadm.sh create $component -r $realm -f /tmp/keycloak-import/$realm/$component.json",
            "        fi",
            "    done",
            "    ",
            "    # Importar usuarios (sin contraseñas)",
            "    if [ -f \"/tmp/keycloak-import/$realm/users.json\" ]; then",
            "        echo \"  Importando usuarios...\"",
            "        ./kcadm.sh create users -r $realm -f /tmp/keycloak-import/$realm/users.json",
            "    fi",
            "    ",
            "    echo \"✅ $realm importado\"",
            "}",
            ""
        ]
        
        if not realms:
            lines.append("echo \"⚠️ No hay reinos para importar\"")
        else:
            for realm in realms:
                lines.append(f"import_realm \"{realm}\"")
                lines.append("")
        
        lines.extend([
            "echo \"\"",
            "echo \"=========================================\"",
            "echo \"IMPORTACIÓN COMPLETADA\"",
            "echo \"=========================================\"",
            "",
            "echo \"Resumen de importación:\"",
            "ls -la /tmp/keycloak-import/"
        ])
        
        # Guardar script
        with open(import_script, 'w') as f:
            f.write('\n'.join(lines))
        
        os.chmod(import_script, 0o755)
        print(f"📝 Script de importación creado: {import_script}")
    
    def create_readme(self, realms: List[Dict[str, Any]]):
        """Crea un README con información de la exportación"""
        readme_file = os.path.join(self.local_dir, "README.md")
        
        lines = [
            "# Exportación de Keycloak",
            "",
            "## Información de la exportación",
            "",
            f"- **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Namespace:** `{self.namespace}`",
            f"- **Pod:** `{self.pod}`",
            f"- **Usuario:** `{self.user}`",
            f"- **Servidor:** `{self.server_url}`",
            f"- **Reinos excluidos:** `{', '.join(self.realms_to_exclude)}`",
            f"- **Reinos exportados:** {len(realms)}",
            "",
            "## Estructura de archivos",
            "```",
            f"{self.local_dir}/",
            "├── import-realms.sh     # Script para importar todos los reinos",
            "├── README.md            # Este archivo",
            "└── [reino]/             # Cada reino tiene su propia carpeta",
            "    ├── realm.json        # Metadatos del reino",
            "    ├── users.json        # Usuarios del reino",
            "    ├── clients.json      # Clientes del reino",
            "    ├── roles.json        # Roles del reino",
            "    ├── groups.json       # Grupos del reino",
            "    ├── client-scopes/    # Scopes de cliente detallados",
            "    └── identity-providers.json # Proveedores de identidad",
            "```",
            "",
            "## Cómo importar los reinos",
            "",
            "### 1. Copiar los archivos al pod destino:",
            "```bash",
            f"kubectl cp {self.local_dir} -n <namespace-destino> <pod-destino>:/tmp/keycloak-import",
            "```",
            "",
            "### 2. Ejecutar el script de importación:",
            "```bash",
            "kubectl exec -it -n <namespace-destino> <pod-destino> -- /bin/bash -c \"",
            "  chmod +x /tmp/keycloak-import/import-realms.sh &&",
            "  /tmp/keycloak-import/import-realms.sh",
            "\"",
            "```",
            "",
            "### 3. Para importar reinos individuales:",
            "```bash",
            "kubectl exec -it -n <namespace-destino> <pod-destino> -- /bin/bash -c \"",
            "  cd /opt/keycloak/bin &&",
            "  ./kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin &&",
            "  ./kcadm.sh create realms -f /tmp/keycloak-import/<reino>/realm.json",
            "\"",
            "```",
            "",
            "## Notas importantes",
            "",
            "1. **Usuarios:** Los usuarios se importan sin contraseñas (requieren reset de contraseña)",
            "2. **IDs:** Verificar que los IDs no estén duplicados en el sistema destino",
            "3. **Secretos:** Los secretos de clientes pueden cambiar, verificar después de la importación",
            "4. **Dependencias:** Asegurar que los reinos dependientes estén importados primero",
            "5. **Archivos vacíos:** Los archivos sin datos contienen `[]` o `{}` según corresponda",
            "",
            "## Verificación de la importación",
            "",
            "```bash",
            "# Verificar reinos importados",
            "kubectl exec -it -n <namespace> <pod> -- /bin/bash -c \"",
            "  cd /opt/keycloak/bin &&",
            "  ./kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin &&",
            "  ./kcadm.sh get realms --fields realm,displayName,enabled",
            "\"",
            "```"
        ]
        
        with open(readme_file, 'w') as f:
            f.write('\n'.join(lines))
        print(f"📖 README creado: {readme_file}")
    
    def create_summary(self, realms: List[Dict[str, Any]]):
        """Crea un resumen en formato JSON"""
        summary_file = os.path.join(self.local_dir, "export-summary.json")
        
        summary = {
            "export_info": {
                "date": datetime.now().isoformat(),
                "namespace": self.namespace,
                "pod": self.pod,
                "user": self.user,
                "server_url": self.server_url,
                "excluded_realms": self.realms_to_exclude,
                "timestamp": int(time.time())
            },
            "realms": realms,
            "total_realms": len(realms)
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resumen guardado: {summary_file}")
    
    def export_all(self):
        """Ejecuta la exportación completa de todos los reinos"""
        print("=" * 70)
        print("🚀 KEYCLOAK REALM EXPORTER".center(70))
        print("=" * 70)
        print(f"📌 Namespace: {self.namespace}")
        print(f"📌 Pod: {self.pod}")
        print(f"📌 Usuario: {self.user}")
        print(f"📌 Servidor: {self.server_url}")
        print("=" * 70)
        
        # 1. Configurar credenciales
        if not self.configure_credentials():
            print("❌ No se pudieron configurar las credenciales")
            sys.exit(1)
        
        # 2. Obtener lista de reinos
        realms = self.get_realms()
        if not realms:
            print("⚠️ No hay reinos para exportar")
            # Crear directorio local
            os.makedirs(self.local_dir, exist_ok=True)
            self.create_readme([])
            self.create_import_script([])
            print(f"\n📁 Directorio local: {self.local_dir}")
            return
        
        # 3. Crear directorio temporal en el pod
        print(f"\n📁 Creando directorio temporal en el pod: {self.temp_dir}")
        self.execute_kubectl(f"rm -rf {self.temp_dir}")
        self.execute_kubectl(f"mkdir -p {self.temp_dir}")
        
        # 4. Crear directorio local
        os.makedirs(self.local_dir, exist_ok=True)
        print(f"📁 Directorio local: {self.local_dir}")
        
        # 5. Exportar cada reino
        exported_realms = []
        for realm_info in realms:
            realm_name = realm_info.get('realm', '')
            success = self.export_realm_with_kcadm(realm_name, realm_info)
            
            if success:
                # Copiar archivos del pod al local
                self.copy_files_from_pod(realm_name)
                exported_realms.append(realm_info)
                print(f"✅ {realm_name} exportado exitosamente")
            else:
                print(f"❌ Error exportando {realm_name}")
        
        # 6. Limpiar archivos temporales del pod
        print(f"\n🧹 Limpiando archivos temporales...")
        self.execute_kubectl(f"rm -rf {self.temp_dir}")
        
        # 7. Crear archivos de documentación
        self.create_summary(exported_realms)
        self.create_import_script([r['realm'] for r in exported_realms])
        self.create_readme(exported_realms)
        
        # 8. Resumen final
        print("\n" + "=" * 70)
        print("✅ EXPORTACIÓN COMPLETADA".center(70))
        print("=" * 70)
        print(f"📁 Archivos en: {self.local_dir}")
        print(f"📊 Reinos exportados: {len(exported_realms)} de {len(realms)}")
        print("=" * 70)
        
        # Mostrar lista de reinos exportados
        if exported_realms:
            print("\n📋 Reinos exportados:")
            for r in exported_realms:
                print(f"  • {r.get('realm', '')} ({r.get('displayName', 'Sin nombre')}) - {'Habilitado' if r.get('enabled', False) else 'Deshabilitado'}")
        else:
            print("\n⚠️ No se exportó ningún reino")

def main():
    """Función principal"""
    # Puedes modificar estos parámetros según tu entorno
    exporter = KeycloakExporter(
        namespace="keycloak",
        pod="keycloak-nuam-0",
        user="ootalora",
        password="Abcd123456"
    )
    exporter.export_all()

if __name__ == "__main__":
    main()